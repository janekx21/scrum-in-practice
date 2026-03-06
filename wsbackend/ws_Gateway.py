import asyncio
import websockets

import json
import struct
import zlib
from websockets.asyncio.server import serve
from ws_mesh_frame_to_glb import mesh_frame_bytes_to_glb

from pathlib import Path
from datetime import datetime

import numpy as np

DTYPE_MAP = {
    "float16": np.float16,
    "float32": np.float32,
    "float64": np.float64,
    "uint8": np.uint8,
    "uint16": np.uint16,
    "uint32": np.uint32,
    "uint64": np.uint64,
    "int16": np.int16,
    "int32": np.int32,
    "int64": np.int64,
}

WS_HOST = "0.0.0.0"
WS_PORT = 9001

UPSTREAM_URI = "ws://141.44.17.48:8768"

FRAME_COUNTER = 0


# ---- PLACEHOLDER HOOKS (später ersetzt du das durch eure echten Funktionen) ----

def try_parse_and_transform_upstream_binary(raw: bytes):
    """
    Später:
      outer, inner, payload = parse_frame(raw)
      if outer.type == "pose": return ("text", pose_string)
      if outer.type == "mesh": return ("bytes", glb_bytes)
    Heute:
      passthrough
    """
    return ("bytes", raw)

def try_transform_upstream_text(raw: str):
    """
    Später könntest du Upstream-Text mappen oder filtern.
    Heute passthrough.
    """
    return ("text", raw)

# -----------------------------------------------------------------------------

def decode_pose(pose_bytes: bytes) -> dict:
    def dtype_from_header(value: str) -> np.dtype:
        if value in DTYPE_MAP:
            return np.dtype(DTYPE_MAP[value])
        return np.dtype(value)

    def extract_first_json_object(buf: bytes, start_at: int = 0) -> tuple[dict, int]:
        start = buf.find(b"{", start_at)
        if start == -1:
            raise ValueError("No JSON object found in pose payload")

        depth = 0
        in_str = False
        esc = False

        for i in range(start, len(buf)):
            c = buf[i]
            if in_str:
                if esc:
                    esc = False
                elif c == ord("\\"):
                    esc = True
                elif c == ord('"'):
                    in_str = False
            else:
                if c == ord('"'):
                    in_str = True
                elif c == ord("{"):
                    depth += 1
                elif c == ord("}"):
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        obj = json.loads(buf[start:end].decode("utf-8"))
                        return obj, end

        raise ValueError("JSON object not closed in pose payload")

    def consume_array(payload: bytes, off: int, dtype: np.dtype, count: int, stride: int) -> tuple[np.ndarray, int]:
        n = int(count) * int(stride)
        nbytes = n * dtype.itemsize
        if off + nbytes > len(payload):
            raise ValueError(f"Array exceeds payload: need {nbytes} bytes at offset {off}, payload={len(payload)}")
        arr = np.frombuffer(payload, dtype=dtype, count=n, offset=off).copy()
        off += nbytes
        if stride == 1:
            return arr.reshape((count,)), off
        return arr.reshape((count, stride)), off

    def to_jsonable_array(arr: np.ndarray):
        if np.issubdtype(arr.dtype, np.floating):
            return arr.astype(np.float32).tolist()
        return arr.tolist()

    # pose_bytes entspricht dem "payload" (bereits dekomprimiert), beginnt mit inner JSON header
    inner, inner_end = extract_first_json_object(pose_bytes, 0)
    off = inner_end

    # Header keys: time_dt / pose_dt / orientation_dt
    t_dt = dtype_from_header(inner["time_dt"])
    p_dt = dtype_from_header(inner["pose_dt"])
    q_dt = dtype_from_header(inner["orientation_dt"])

    remaining = len(pose_bytes) - off
    per_item = t_dt.itemsize + (3 * p_dt.itemsize) + (4 * q_dt.itemsize)
    if per_item <= 0 or (remaining % per_item) != 0:
        raise ValueError(f"Pose payload size mismatch: remaining={remaining}, per_item={per_item}")

    n = remaining // per_item

    times, off = consume_array(pose_bytes, off, t_dt, n, 1)
    poses, off = consume_array(pose_bytes, off, p_dt, n, 3)
    oris,  off = consume_array(pose_bytes, off, q_dt, n, 4)

    # Wichtig: Key-Namen wie von dir vorgegeben ("oriantations" mit Tippfehler)
    return {
        "count": int(n),
        "times": to_jsonable_array(times),
        "poses": to_jsonable_array(poses),
        "oriantations": to_jsonable_array(oris),
    }

async def proxy_loop(client_ws, upstream_ws):
    """
    Upstream -> Client, mit Transform-Hooks.
    """
    async for msg in upstream_ws:
        if isinstance(msg, bytes):
            kind, out = try_parse_and_transform_upstream_binary(msg)
        else:
            kind, out = try_transform_upstream_text(msg)

        if kind == "bytes":
            await client_ws.send(out)
        else:
            # kind == "text"
            await client_ws.send(out)

def read_u32_le(b: bytes, off: int) -> tuple[int, int]:
    if off + 4 > len(b):
        raise ValueError("Truncated while reading u32")
    return struct.unpack_from("<I", b, off)[0], off + 4

def decompress_zlib_chunks(b: bytes, off: int) -> bytes:
    out = bytearray()
    chunk_count = 0
    while off < len(b):
        clen, off = read_u32_le(b, off)
        if clen <= 0:
            raise ValueError(f"Invalid chunk length: {clen}")
        if off + clen > len(b):
            raise ValueError("Truncated chunk")
        out += zlib.decompress(b[off:off + clen])
        off += clen
        chunk_count += 1
    return bytes(out)

def parse_frame(message: bytes) -> tuple[dict, dict | None, bytes | None]:
    """
    Erwartet: [u32 outer_json_len][outer_json][u32 chunk_len][zlib]...
    Returns: (outer_header, inner_header_or_None, decompressed_payload_or_None)
    """
    off = 0
    outer_len, off = read_u32_le(message, off)
    if off + outer_len > len(message):
        raise ValueError("Outer JSON truncated")

    outer = json.loads(message[off:off + outer_len].decode("utf-8"))
    off += outer_len

    # Wenn kein payload folgt, sind wir fertig
    if off >= len(message):
        return outer, None, None

    compression = (outer.get("compression") or "").lower()
    if compression != "zlib":
        raise ValueError(f"Unsupported compression: {compression!r}")

    payload = decompress_zlib_chunks(message, off)

    # inner header liegt am Anfang vom dekomprimierten payload
    inner, _ = extract_first_json_object(payload, 0)
    return outer, inner, payload

def extract_first_json_object(buf: bytes, start_at: int = 0) -> tuple[dict, int]:
    start = buf.find(b"{", start_at)
    if start == -1:
        raise ValueError("No JSON object found")

    depth = 0
    in_str = False
    esc = False

    for i in range(start, len(buf)):
        c = buf[i]
        if in_str:
            if esc:
                esc = False
            elif c == ord("\\"):
                esc = True
            elif c == ord('"'):
                in_str = False
        else:
            if c == ord('"'):
                in_str = True
            elif c == ord("{"):
                depth += 1
            elif c == ord("}"):
                depth -= 1
                if depth == 0:
                    end = i + 1
                    obj = json.loads(buf[start:end].decode("utf-8"))
                    return obj, end

    raise ValueError("JSON object not closed")


async def handle_client(ws):
    peer = getattr(ws, "remote_address", None)
    print(f"[ws] connect {peer}")

    upstream_task = None
    upstream = None
    channel = None

    try:
        cmd = await ws.recv()
        print(f"Stream start für {cmd}")

        async with websockets.connect(UPSTREAM_URI, max_size=None) as ws_2:
            await ws_2.send(f"start:{cmd}")

            while True:
                try:
                # max. 5 Sekunden auf neue Nachricht warten
                    msg = await asyncio.wait_for(ws_2.recv(), timeout=5.0)
                except asyncio.TimeoutError:
                    print("No message for 5 seconds. Closing loop.")
                    break

                if isinstance(msg, bytes):
                    try:
                        outer, inner, payload = parse_frame(msg)
                    except Exception as e:
                        print("FRAME_PARSE_ERROR:", e, "| bytes=", len(msg))
                        continue

                    ftype = (outer.get("type") or "").lower()
                    if ftype == "mesh":
                        print(f"{datetime.now()} == MESH == ")
                        global FRAME_COUNTER
                        try:
                            glb, outer_hdr, meshheader = mesh_frame_bytes_to_glb(msg)

                            out = Path("glbs") / f"frame_{FRAME_COUNTER:06d}.glb"

                            st = outer_hdr.get("stamp") or {}
                            print("GLB OK:", out, "stamp:", f"{st.get('sec')}.{str(st.get('nanosec')).zfill(9)}",
                                "V:", meshheader.get("vertex_count"), "T:", meshheader.get("triangle_count"))
                            FRAME_COUNTER += 1

                        except Exception as e:
                            print("GLB FAIL:", e)
                            #return

                        if ws and glb:
                            await ws.send(glb)

                        print(f"{datetime.now()} - Done")

                        if ws and ws.state == websockets.State.OPEN:
                            await ws.send(glb)

                        print(f"{datetime.now()} - Done")

                    elif ftype == "pose":
                        print(f"{datetime.now()} == POSE ==")
                        if inner is None or payload is None:
                            print("header-only frame (no chunks/payload)")
                            return

                        # nur Analyse/Metadaten
                        print("stamp:", outer.get("stamp"))

                        # erwartete keys (wie du sie beschrieben hast / wie wir bisher gesehen haben)
                        # falls dein poseheader anders heißt, siehst du es direkt im print unten.
                        print("pose_header_keys:", list(inner.keys()))

                        time_dt = inner.get("time_dt") or inner.get("time_dtype")
                        pose_dt = inner.get("pose_dt") or inner.get("pose_dtype")
                        ori_dt = inner.get("orientation_dt") or inner.get("orientation_dtype")

                        print("dtypes:", {"time": time_dt, "pose": pose_dt, "orientation": ori_dt})

                        # count evtl. nicht im header -> nur payload size zeigen
                        print("payload_decompressed_bytes:", len(payload))
                        # hier kannst du später count berechnen / arrays dekodieren

                        if ws and ws.state == websockets.State.OPEN:
                            
                            await ws.send(json.dumps(decode_pose(payload)))
                            print("WS Server: send pose data via websocket")

                        print(f"{datetime.now()} - Done")
                    else:
                        print("== UNKNOWN TYPE ==")
                        print("type:", outer.get("type"))
                        print("outer:", outer)
                else:
                    print("TEXT:", msg)



    except websockets.ConnectionClosed:
        pass
    except Exception as e:
        print(f"[ws] error: {e}")
        try:
            await ws.send("ERROR internal")
        except Exception:
            pass
    finally:
        # cleanup
        if upstream_task and not upstream_task.done():
            upstream_task.cancel()
            try:
                await upstream_task
            except Exception:
                pass

        if upstream:
            try:
                await upstream.close()
            except Exception:
                pass

        if channel:
            try:
                await ws.send(f"ENDED {channel}")
            except Exception:
                pass

        print(f"[ws] disconnect {peer}")


async def main():
    print(f"[ws] starting on ws://{WS_HOST}:{WS_PORT}")
    async with websockets.serve(handle_client, WS_HOST, WS_PORT, max_size=None):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())