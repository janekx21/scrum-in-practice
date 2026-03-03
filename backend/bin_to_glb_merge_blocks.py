#!/usr/bin/env python3
import argparse
import json
import struct
import zlib
from pathlib import Path
from typing import Tuple, Optional, List

import numpy as np
import trimesh

DTYPE_MAP = {
    "float16": np.float16,
    "float32": np.float32,
    "uint8": np.uint8,
    "uint16": np.uint16,
    "uint32": np.uint32,
    "int16": np.int16,
    "int32": np.int32,
}


def read_u32_le(b: bytes, off: int) -> Tuple[int, int]:
    return struct.unpack_from("<I", b, off)[0], off + 4

"""
    Layout:
      [u32 outer_json_len][outer_json_bytes]
      then repeated until EOF:
        [u32 chunk_len][zlib-compressed bytes]
    Returns: (outer_header_json, decompressed_payload_bytes, chunk_count)
"""
def decompress_chunked_payload(file_bytes: bytes) -> Tuple[dict, bytes, int]:
    off = 0
    if len(file_bytes) < 4:
        raise ValueError("File too small")

    hdr_len, off = read_u32_le(file_bytes, off)
    if off + hdr_len > len(file_bytes):
        raise ValueError("Outer JSON header exceeds file size")

    outer = json.loads(file_bytes[off:off + hdr_len].decode("utf-8"))
    off += hdr_len

    out = bytearray()
    chunks = 0
    while off < len(file_bytes):
        if off + 4 > len(file_bytes):
            raise ValueError("Truncated: missing chunk length at end")
        clen, off = read_u32_le(file_bytes, off)
        if clen <= 0:
            raise ValueError("Invalid chunk length")
        if off + clen > len(file_bytes):
            raise ValueError("Truncated: chunk exceeds file size")

        comp = file_bytes[off:off + clen]
        off += clen

        out += zlib.decompress(comp)
        chunks += 1

    return outer, bytes(out), chunks

"""
    Extract the first complete JSON object {...} from payload.
    Returns (obj, end_offset).
"""
def extract_first_json_object(payload: bytes) -> Tuple[dict, int]:
    start = payload.find(b"{")
    if start == -1:
        raise ValueError("No JSON object start found in payload")

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

    raise ValueError("JSON object not closed (unbalanced braces)")


def consume_array(payload: bytes, off: int, dtype: str, count: int, stride: int) -> Tuple[np.ndarray, int]:
    np_dtype = DTYPE_MAP[dtype]
    n = count * stride
    nbytes = np.dtype(np_dtype).itemsize * n
    if off + nbytes > len(payload):
        raise ValueError(f"Array exceeds payload: need {nbytes} bytes at offset {off}, payload={len(payload)}")
    arr = np.frombuffer(payload, dtype=np_dtype, count=n, offset=off).copy()
    off += nbytes
    arr = arr.reshape((count, stride))
    return arr, off

"""
    Reads the global buffers as described by meshheader counts.
    We will then rebuild a correct merged mesh from blocks.
"""
def decode_global_arrays(payload: bytes, meshheader: dict, off_after_json: int):
    off = off_after_json

    v_dtype = meshheader["vertex_dtype"]
    v_cnt = int(meshheader["vertex_count"])
    v_stride = int(meshheader["vertex_stride"])
    vertices, off = consume_array(payload, off, v_dtype, v_cnt, v_stride)

    t_dtype = meshheader["triangle_dtype"]
    t_cnt = int(meshheader["triangle_count"])
    t_stride = int(meshheader["triangle_stride"])
    triangles, off = consume_array(payload, off, t_dtype, t_cnt, t_stride)

    normals = None
    n_cnt = int(meshheader.get("normal_count", 0) or 0)
    if n_cnt > 0:
        n_dtype = meshheader.get("normal_dtype", "float16")
        n_stride = int(meshheader.get("normal_stride", 3))
        normals, off = consume_array(payload, off, n_dtype, n_cnt, n_stride)

    colors = None
    if "color_bytes" in meshheader and int(meshheader.get("color_bytes", 0) or 0) > 0:
        c_dtype = meshheader.get("color_dtype", "uint8")
        c_stride = int(meshheader.get("color_stride", 3))
        c_bytes = int(meshheader["color_bytes"])
        item = np.dtype(DTYPE_MAP[c_dtype]).itemsize
        c_cnt = c_bytes // (item * c_stride)
        colors, off = consume_array(payload, off, c_dtype, c_cnt, c_stride)

    return vertices, triangles, normals, colors


def compute_vertex_normals_numpy(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    v = vertices
    f = faces

    if len(f) == 0 or len(v) == 0:
        return np.zeros((len(v), 3), dtype=np.float32)

    v0 = v[f[:, 0]]
    v1 = v[f[:, 1]]
    v2 = v[f[:, 2]]

    fn = np.cross(v1 - v0, v2 - v0)  # area-weighted face normals

    vn = np.zeros_like(v, dtype=np.float32)
    np.add.at(vn, f[:, 0], fn)
    np.add.at(vn, f[:, 1], fn)
    np.add.at(vn, f[:, 2], fn)

    n = np.linalg.norm(vn, axis=1, keepdims=True)
    n[n == 0] = 1.0
    vn /= n
    return vn

"""
    We try to detect whether triangles are:
      - global indices into the full vertex buffer, or
      - local indices into the block vertex slice.
    Then we return local indices 0..v_cnt-1.
"""
def rebase_triangles_for_block(T: np.ndarray, v_off: int, v_cnt: int, global_v_cnt: int) -> np.ndarray:
    if T.size == 0:
        return T.astype(np.int64, copy=False)

    Ti = T.astype(np.int64, copy=False)
    tmin = int(Ti.min())
    tmax = int(Ti.max())

    # Case 1: already local (0..v_cnt-1)
    if 0 <= tmin and tmax < v_cnt:
        return Ti

    # Case 2: global and within this block slice (v_off..v_off+v_cnt-1)
    if v_off <= tmin and tmax < (v_off + v_cnt):
        return Ti - v_off

    # Case 3: global overall, but triangles may still mostly target the block slice.
    # Try subtracting v_off and validate.
    cand = Ti - v_off
    if cand.min() >= 0 and cand.max() < v_cnt:
        return cand

    # If we land here, something doesn't match; fail loudly with diagnostics.
    raise ValueError(
        f"Cannot rebase triangles for block: v_off={v_off} v_cnt={v_cnt} "
        f"triangle_min={tmin} triangle_max={tmax} global_vertex_count={global_v_cnt}"
    )


def merge_blocks_to_single_mesh(vertices: np.ndarray,
                                triangles: np.ndarray,
                                colors: Optional[np.ndarray],
                                meshheader: dict) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
    blocks = meshheader.get("blocks") or []
    if not isinstance(blocks, list) or len(blocks) == 0:
        raise ValueError("No blocks in meshheader; cannot merge blockwise")

    v_merged: List[np.ndarray] = []
    f_merged: List[np.ndarray] = []
    c_merged: List[np.ndarray] = []

    vertex_base = 0
    used_blocks = 0

    for b in blocks:
        v_off = int(b.get("v_off", 0))
        v_cnt = int(b.get("v_cnt", 0))
        t_off = int(b.get("t_off", 0))
        t_cnt = int(b.get("t_cnt", 0))

        if v_cnt == 0 or t_cnt == 0:
            continue

        Vb = vertices[v_off:v_off + v_cnt]
        Tb = triangles[t_off:t_off + t_cnt]

        Tb_local = rebase_triangles_for_block(Tb, v_off, v_cnt, global_v_cnt=len(vertices))
        Tb_local = Tb_local + vertex_base  # shift into merged vertex array

        v_merged.append(Vb)
        f_merged.append(Tb_local.astype(np.int64, copy=False))

        if colors is not None:
            # colors are stored as bytes; meshheader blocks often include c_off/c_len
            c_off = int(b.get("c_off", -1))
            c_len = int(b.get("c_len", 0))
            if c_off >= 0 and c_len > 0:
                # c_len is bytes; with stride=3 uint8 => count = c_len/3
                cb = colors.reshape(-1, colors.shape[1])
                Cb = cb[c_off // colors.shape[1] : (c_off + c_len) // colors.shape[1]]
                # If sizes mismatch, fall back to vertex slice alignment
                if len(Cb) != v_cnt:
                    Cb = colors[v_off:v_off + v_cnt]
            else:
                Cb = colors[v_off:v_off + v_cnt]
            c_merged.append(Cb)

        vertex_base += v_cnt
        used_blocks += 1

    if used_blocks == 0:
        raise ValueError("All blocks were empty (no geometry).")

    V = np.vstack(v_merged).astype(np.float32, copy=False)
    F = np.vstack(f_merged).astype(np.int64, copy=False)

    C = None
    if colors is not None and len(c_merged) == used_blocks:
        C = np.vstack(c_merged)
        # ensure uint8 RGB
        if C.dtype != np.uint8:
            C = C.astype(np.uint8)

    return V, F, C


def export_glb(vertices_f32: np.ndarray, faces_i64: np.ndarray, colors_rgb_u8: Optional[np.ndarray]) -> bytes:
    mesh = trimesh.Trimesh(vertices=vertices_f32, faces=faces_i64, process=False)

    # normals without scipy
    vn = compute_vertex_normals_numpy(vertices_f32, faces_i64)
    mesh._cache["vertex_normals"] = vn

    if colors_rgb_u8 is not None:
        c = colors_rgb_u8
        if c.ndim == 2 and c.shape[1] == 3:
            alpha = np.full((c.shape[0], 1), 255, dtype=np.uint8)
            c = np.concatenate([c, alpha], axis=1)
        if c.shape[0] == vertices_f32.shape[0] and c.shape[1] == 4:
            mesh.visual.vertex_colors = c
        else:
            print("Warning: colors not applied (shape mismatch after merge).")

    glb = mesh.export(file_type="glb")
    if isinstance(glb, str):
        glb = glb.encode("utf-8")
    return glb


def pick_first_bin(path: Path) -> Path:
    if path.is_file():
        return path
    bins = sorted(path.glob("*.bin"))
    if not bins:
        raise FileNotFoundError(f"No .bin files found in {path}")
    return bins[0]


def main():
    ap = argparse.ArgumentParser(description="Convert chunked-zlib mesh .bin to a single merged GLB (blockwise merge)")
    ap.add_argument("input", help="Path to a .bin file or a directory containing .bin files")
    ap.add_argument("-o", "--out", default="out.glb", help="Output .glb path (default: out.glb)")
    args = ap.parse_args()


    folder = Path(args.input)
    files = sorted(folder.glob("*.bin"))
    print("Found", len(files), "bin files")

    for file in files:
        print("Processing:", file.name)
        convert(file, file.parent.joinpath("glbs").joinpath(file.name + ".glb"))
    print("Done")

def convert(input_path, output_path):
    inp = Path(input_path)
    bin_path = pick_first_bin(inp)

    raw = bin_path.read_bytes()
    outer, payload, chunks = decompress_chunked_payload(raw)
    meshheader, end_off = extract_first_json_object(payload)

    v_cnt = int(meshheader.get("vertex_count", 0) or 0)
    t_cnt = int(meshheader.get("triangle_count", 0) or 0)
    if v_cnt == 0 or t_cnt == 0:
        return

    vertices, triangles, normals, colors = decode_global_arrays(payload, meshheader, end_off)

    # Diagnose index ranges (hilft beim Debug)
    print("Global vertex_count:", len(vertices))
    print("Global triangle_count:", len(triangles))
    print("Triangle index min/max:", int(triangles.min()) if len(triangles) else None, "/", int(triangles.max()) if len(triangles) else None)

    V, F, C = merge_blocks_to_single_mesh(vertices, triangles, colors, meshheader)
    glb = export_glb(V, F, C)

    out_path = Path(output_path)
    out_path.write_bytes(glb)

    st = outer.get("stamp") or {}
    print("\nInput :", bin_path)
    print("Output:", out_path)
    print("Stamp :", f"{st.get('sec')}.{str(st.get('nanosec')).zfill(9)}")
    print("Chunks:", chunks, "Payload bytes:", len(payload))
    print("Merged:", f"V={len(V)} T={len(F)} Colors={'yes' if C is not None else 'no'}")
    print("MeshHeader:", f"frame_id={meshheader.get('frame_id')}, message_id={meshheader.get('message_id')}, block_size={meshheader.get('block_size')}")

if __name__ == "__main__":
    main()