#!/usr/bin/env python3
import argparse
import json
import struct
import zlib
from pathlib import Path

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


def read_u32_le(buf: bytes, off: int) -> tuple[int, int]:
    if off + 4 > len(buf):
        raise ValueError("Truncated while reading u32")
    return struct.unpack_from("<I", buf, off)[0], off + 4


def extract_first_json_object(buf: bytes, start_at: int = 0) -> tuple[dict, int]:
    """
    Finds the first complete JSON object {...} in buf starting at start_at.
    Returns (obj, end_offset).
    """
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


def decompress_zlib_chunks(buf: bytes, off: int) -> bytes:
    out = bytearray()
    while off < len(buf):
        clen, off = read_u32_le(buf, off)
        if clen <= 0:
            raise ValueError(f"Invalid chunk length: {clen}")
        if off + clen > len(buf):
            raise ValueError("Truncated: chunk exceeds file size")
        comp = buf[off:off + clen]
        off += clen
        out += zlib.decompress(comp)
    return bytes(out)


def dtype_from_header(value: str) -> np.dtype:
    if value in DTYPE_MAP:
        return np.dtype(DTYPE_MAP[value])
    # allow numpy-style strings too
    return np.dtype(value)


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
    # float16 -> float for readable JSON
    if np.issubdtype(arr.dtype, np.floating):
        return arr.astype(np.float32).tolist()
    # uint64 etc. -> Python int
    return arr.tolist()


def decode_one_file(in_path: Path) -> dict:
    raw = in_path.read_bytes()
    off = 0

    # outer header
    outer_len, off = read_u32_le(raw, off)
    if off + outer_len > len(raw):
        raise ValueError("Truncated outer JSON")
    outer = json.loads(raw[off:off + outer_len].decode("utf-8"))
    off += outer_len

    if (outer.get("compression") or "").lower() != "zlib":
        raise ValueError(f"Unsupported compression: {outer.get('compression')}")

    # decompress chunk stream
    payload = decompress_zlib_chunks(raw, off)

    # inner header (second header)
    inner, inner_end = extract_first_json_object(payload, 0)
    data_off = inner_end

    ftype = (outer.get("type") or "").lower()
    out = {
        "file": str(in_path),
        "outer": outer,
        "inner": inner,
        "type": ftype,
    }

    if ftype == "mesh":
        v_dt = dtype_from_header(inner["vertex_dtype"])
        v_cnt = int(inner["vertex_count"])
        v_stride = int(inner["vertex_stride"])

        t_dt = dtype_from_header(inner["triangle_dtype"])
        t_cnt = int(inner["triangle_count"])
        t_stride = int(inner["triangle_stride"])

        vertices, data_off = consume_array(payload, data_off, v_dt, v_cnt, v_stride)
        triangles, data_off = consume_array(payload, data_off, t_dt, t_cnt, t_stride)

        decoded = {
            "vertices": to_jsonable_array(vertices),
            "triangles": to_jsonable_array(triangles),
        }

        # normals optional (count may be 0)
        if "normal_dtype" in inner and "normal_count" in inner and "normal_stride" in inner:
            n_cnt = int(inner["normal_count"])
            if n_cnt > 0:
                n_dt = dtype_from_header(inner["normal_dtype"])
                n_stride = int(inner["normal_stride"])
                normals, data_off = consume_array(payload, data_off, n_dt, n_cnt, n_stride)
                decoded["normals"] = to_jsonable_array(normals)

        # colors optional; in your frames it’s "color_bytes"
        if "color_bytes" in inner:
            cb = int(inner["color_bytes"])
            if cb > 0:
                c_dt = dtype_from_header(inner.get("color_dtype", "uint8"))
                c_stride = int(inner.get("color_stride", 3))

                # interpret as packed bytes, then reshape if possible
                if data_off + cb > len(payload):
                    raise ValueError("Colors exceed payload")
                c_raw = payload[data_off:data_off + cb]
                data_off += cb

                c_arr = np.frombuffer(c_raw, dtype=c_dt).copy()
                if c_stride > 1 and (c_arr.size % c_stride == 0):
                    c_arr = c_arr.reshape((c_arr.size // c_stride, c_stride))
                decoded["colors"] = to_jsonable_array(c_arr)

        out["decoded"] = decoded
        out["remaining_bytes_after_decode"] = len(payload) - data_off
        return out

    if ftype == "pose":
        # Header keys in your sample: time_dt / pose_dt / orientation_dt
        t_dt = dtype_from_header(inner["time_dt"])
        p_dt = dtype_from_header(inner["pose_dt"])
        q_dt = dtype_from_header(inner["orientation_dt"])

        remaining = len(payload) - data_off
        one_item = t_dt.itemsize + (3 * p_dt.itemsize) + (4 * q_dt.itemsize)
        if one_item <= 0 or remaining % one_item != 0:
            raise ValueError(f"Pose payload size mismatch: remaining={remaining}, per_item={one_item}")

        n = remaining // one_item

        times, data_off = consume_array(payload, data_off, t_dt, n, 1)
        poses, data_off = consume_array(payload, data_off, p_dt, n, 3)
        oris, data_off = consume_array(payload, data_off, q_dt, n, 4)

        out["decoded"] = {
            "count": int(n),
            "times": to_jsonable_array(times),
            "poses": to_jsonable_array(poses),
            "orientations": to_jsonable_array(oris),
        }
        out["remaining_bytes_after_decode"] = len(payload) - data_off
        return out

    raise ValueError(f"Unknown frame type: {ftype!r}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path, help="Input .bin file OR directory")
    ap.add_argument("-o", "--output", type=Path, required=True, help="Output .json file OR directory")
    args = ap.parse_args()

    inp = args.input
    outp = args.output

    if inp.is_file():
        data = decode_one_file(inp)
        outp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {outp}")
        return

    if inp.is_dir():
        outp.mkdir(parents=True, exist_ok=True)
        for f in sorted(inp.glob("*.bin")):
            try:
                data = decode_one_file(f)
                (outp / (f.stem + ".json")).write_text(
                    json.dumps(data, indent=2, ensure_ascii=False),
                    encoding="utf-8"
                )
                print(f"Wrote {outp / (f.stem + '.json')}")
            except Exception as e:
                print(f"Skip {f.name}: {e}")
        return

    raise SystemExit("Input must be a file or directory")


if __name__ == "__main__":
    main()