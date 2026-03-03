#!/usr/bin/env python3
import argparse
import json
import struct
import zlib
from pathlib import Path
from typing import Tuple, Optional


def read_u32_le(b: bytes, off: int) -> Tuple[int, int]:
    return struct.unpack_from("<I", b, off)[0], off + 4


def decompress_chunked_payload(file_bytes: bytes) -> Tuple[dict, bytes, int]:
    """
    Layout:
    [u32 header_json_len] [header_json_bytes]
    then repeated until EOF:
      [u32 chunk_len] [zlib_compressed_chunk_bytes]
    Returns: (outer_header_json, decompressed_payload, chunk_count)
    """
    off = 0
    if len(file_bytes) < 4:
        raise ValueError("Too small for header length")

    hdr_len, off = read_u32_le(file_bytes, off)
    if off + hdr_len > len(file_bytes):
        raise ValueError("Header JSON exceeds file size")

    outer = json.loads(file_bytes[off:off + hdr_len].decode("utf-8"))
    off += hdr_len

    out = bytearray()
    chunks = 0
    while off < len(file_bytes):
        if off + 4 > len(file_bytes):
            raise ValueError("Truncated: missing chunk length at end")
        clen, off = read_u32_le(file_bytes, off)
        if clen < 1:
            raise ValueError("Invalid chunk length (0)")
        if off + clen > len(file_bytes):
            raise ValueError("Truncated: chunk exceeds file size")

        comp = file_bytes[off:off + clen]
        off += clen

        out += zlib.decompress(comp)
        chunks += 1

    return outer, bytes(out), chunks


def extract_first_json_object(payload: bytes) -> Tuple[dict, int]:
    """
    Extract the first complete JSON object {...} from payload.
    Returns (obj, end_offset).
    """
    start = payload.find(b"{")
    if start == -1:
        raise ValueError("No '{' found in payload (no JSON?)")

    depth = 0
    in_str = False
    esc = False

    for i in range(start, len(payload)):
        c = payload[i]
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
                    obj = json.loads(payload[start:end].decode("utf-8"))
                    return obj, end

    raise ValueError("JSON object not closed")


def fmt_stamp(outer: dict) -> str:
    st = outer.get("stamp") or {}
    sec = st.get("sec")
    nsec = st.get("nanosec")
    if sec is None and nsec is None:
        return "n/a"
    return f"{sec}.{str(nsec).zfill(9)}"


def summarize_meshheader(mh: dict) -> str:
    parts = []
    for k in ["frame_id", "message_id", "block_size"]:
        if k in mh:
            parts.append(f"{k}={mh.get(k)}")

    # vertex / triangle summary if present
    if "vertex_count" in mh:
        parts.append(
            f"V={mh.get('vertex_count')} "
            f"({mh.get('vertex_dtype')} x{mh.get('vertex_stride')})"
        )
    if "triangle_count" in mh:
        parts.append(
            f"T={mh.get('triangle_count')} "
            f"({mh.get('triangle_dtype')} x{mh.get('triangle_stride')})"
        )
    if "normal_count" in mh:
        parts.append(f"N={mh.get('normal_count')}")
    if "color_bytes" in mh:
        parts.append(
            f"Cbytes={mh.get('color_bytes')} "
            f"({mh.get('color_dtype')} x{mh.get('color_stride')})"
        )

    blocks = mh.get("blocks")
    if isinstance(blocks, list):
        parts.append(f"blocks={len(blocks)}")

    return ", ".join(parts) if parts else "(no known meshheader keys found)"


def inspect_one(path: Path) -> dict:
    b = path.read_bytes()

    outer, payload, chunks = decompress_chunked_payload(b)

    info = {
        "file": str(path),
        "size_bytes": len(b),
        "chunks": chunks,
        "payload_bytes": len(payload),
        "outer_type": outer.get("type"),
        "outer_version": outer.get("version"),
        "outer_compression": outer.get("compression"),
        "stamp": fmt_stamp(outer),
        "meshheader_ok": False,
        "meshheader_summary": None,
        "meshheader": None,
    }

    try:
        mh, mh_end = extract_first_json_object(payload)
        info["meshheader_ok"] = True
        info["meshheader"] = mh
        info["meshheader_summary"] = summarize_meshheader(mh)
        info["meshheader_end_offset"] = mh_end
    except Exception as e:
        info["meshheader_error"] = str(e)

    return info


def main():
    ap = argparse.ArgumentParser(description="Inspect chunked zlib mesh .bin files")
    ap.add_argument("input", help="File or directory")
    ap.add_argument("--glob", default="*.bin", help="Glob pattern when input is a directory (default: *.bin)")
    ap.add_argument("--dump-meshheader", action="store_true", help="Print full meshheader JSON if found")
    ap.add_argument("--as-json", action="store_true", help="Output as JSON lines (one object per file)")
    args = ap.parse_args()

    inp = Path(args.input)
    files = [inp] if inp.is_file() else sorted(inp.glob(args.glob))

    if not files:
        raise SystemExit("No files matched.")

    for f in files:
        try:
            info = inspect_one(f)
        except Exception as e:
            info = {"file": str(f), "error": str(e)}

        if args.as_json:
            print(json.dumps(info, ensure_ascii=False))
            continue

        # human-friendly output
        if "error" in info:
            print(f"[FAIL] {info['file']}: {info['error']}")
            continue

        print(f"\n[OK] {info['file']}")
        print(f"  size: {info['size_bytes']} bytes")
        print(f"  outer: type={info['outer_type']}, version={info['outer_version']}, compression={info['outer_compression']}")
        print(f"  stamp: {info['stamp']}")
        print(f"  chunks: {info['chunks']}, payload: {info['payload_bytes']} bytes")

        if info.get("meshheader_ok"):
            print(f"  meshheader: {info['meshheader_summary']}")
            if args.dump_meshheader:
                print("  meshheader JSON:")
                print(json.dumps(info["meshheader"], indent=2, ensure_ascii=False))
        else:
            print(f"  meshheader: NOT FOUND ({info.get('meshheader_error', 'unknown error')})")


if __name__ == "__main__":
    main()