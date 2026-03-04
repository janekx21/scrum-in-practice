import asyncio
import json
import struct
import zlib
import websockets

from pathlib import Path
from ws_mesh_frame_to_glb import mesh_frame_bytes_to_glb, save_glb

FRAME_COUNTER = 0

URI = "ws://141.44.17.48:8768"


def parse_list_response_to_array(resp: str):
    return [s.strip() for s in resp.split(",") if s.strip()]


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

def handle_mesh(frame_bytes: bytes, outer: dict):
    print("== MESH ==")
    global FRAME_COUNTER
    try:
        glb, outer_hdr, meshheader = mesh_frame_bytes_to_glb(frame_bytes)

        out = Path("glbs") / f"frame_{FRAME_COUNTER:06d}.glb"
        save_glb(glb, out)

        # TODO here is the GLB as the "glb" thing

        st = outer_hdr.get("stamp") or {}
        print("GLB OK:", out, "stamp:", f"{st.get('sec')}.{str(st.get('nanosec')).zfill(9)}",
              "V:", meshheader.get("vertex_count"), "T:", meshheader.get("triangle_count"))
        FRAME_COUNTER += 1

    except Exception as e:
        print("GLB FAIL:", e)


def handle_pose(outer: dict, inner: dict | None, payload: bytes | None):
    print("== POSE ==")
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


async def main():
    async with websockets.connect(URI, max_size=None) as ws:
        print(f"Connected: {URI}")

        await ws.send("list")
        resp = await ws.recv()
        if not isinstance(resp, str):
            print("Unexpected non-text response to list")
            return

        datasets = parse_list_response_to_array(resp)
        print("Datasets:", datasets)

        # TODO decide on what stream we want to go with
        dataset = datasets[1]
        await ws.send(f"start:{dataset}")
        print(f"Started dataset: {dataset}")

        while True:
            # TODO asynchron machen
            msg = await ws.recv()

            if isinstance(msg, bytes):
                try:
                    outer, inner, payload = parse_frame(msg)
                except Exception as e:
                    print("FRAME_PARSE_ERROR:", e, "| bytes=", len(msg))
                    continue

                ftype = (outer.get("type") or "").lower()
                if ftype == "mesh":
                    handle_mesh(msg, outer)
                elif ftype == "pose":
                    handle_pose(outer, inner, payload)
                else:
                    print("== UNKNOWN TYPE ==")
                    print("type:", outer.get("type"))
                    print("outer:", outer)
            else:
                print("TEXT:", msg)


if __name__ == "__main__":
    asyncio.run(main())