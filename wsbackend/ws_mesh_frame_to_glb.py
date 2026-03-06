#!/usr/bin/env python3
import json
import struct
import zlib
from pathlib import Path
from typing import Optional, Tuple, List

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
    if off + 4 > len(b):
        raise ValueError("Truncated while reading u32")
    return struct.unpack_from("<I", b, off)[0], off + 4


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


def decompress_zlib_chunks(buf: bytes, off: int) -> Tuple[bytes, int]:
    """
    Reads repeated [u32 chunk_len][zlib bytes] until EOF.
    Returns (decompressed_payload, chunk_count).
    """
    out = bytearray()
    chunks = 0
    while off < len(buf):
        clen, off = read_u32_le(buf, off)
        if clen <= 0:
            raise ValueError(f"Invalid chunk length: {clen}")
        if off + clen > len(buf):
            raise ValueError("Truncated: chunk exceeds message size")
        out += zlib.decompress(buf[off:off + clen])
        off += clen
        chunks += 1
    return bytes(out), chunks


def consume_array(payload: bytes, off: int, dtype: str, count: int, stride: int) -> Tuple[np.ndarray, int]:
    np_dtype = DTYPE_MAP[dtype]
    n = int(count) * int(stride)
    nbytes = np.dtype(np_dtype).itemsize * n
    if off + nbytes > len(payload):
        raise ValueError(f"Array exceeds payload: need {nbytes} bytes at offset {off}, payload={len(payload)}")
    arr = np.frombuffer(payload, dtype=np_dtype, count=n, offset=off).copy()
    off += nbytes
    arr = arr.reshape((int(count), int(stride)))
    return arr, off


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
    if len(faces) == 0 or len(vertices) == 0:
        return np.zeros((len(vertices), 3), dtype=np.float32)

    v0 = vertices[faces[:, 0]]
    v1 = vertices[faces[:, 1]]
    v2 = vertices[faces[:, 2]]

    fn = np.cross(v1 - v0, v2 - v0)  # area-weighted face normals

    vn = np.zeros_like(vertices, dtype=np.float32)
    np.add.at(vn, faces[:, 0], fn)
    np.add.at(vn, faces[:, 1], fn)
    np.add.at(vn, faces[:, 2], fn)

    n = np.linalg.norm(vn, axis=1, keepdims=True)
    n[n == 0] = 1.0
    vn /= n
    return vn


def rebase_triangles_for_block(T: np.ndarray, v_off: int, v_cnt: int, global_v_cnt: int) -> np.ndarray:
    if T.size == 0:
        return T.astype(np.int64, copy=False)

    Ti = T.astype(np.int64, copy=False)
    tmin = int(Ti.min())
    tmax = int(Ti.max())

    if 0 <= tmin and tmax < v_cnt:
        return Ti

    if v_off <= tmin and tmax < (v_off + v_cnt):
        return Ti - v_off

    cand = Ti - v_off
    if cand.min() >= 0 and cand.max() < v_cnt:
        return cand

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
        Tb_local = Tb_local + vertex_base

        v_merged.append(Vb)
        f_merged.append(Tb_local.astype(np.int64, copy=False))

        if colors is not None:
            c_off = int(b.get("c_off", -1))
            c_len = int(b.get("c_len", 0))
            if c_off >= 0 and c_len > 0:
                cb = colors.reshape(-1, colors.shape[1])
                Cb = cb[c_off // colors.shape[1] : (c_off + c_len) // colors.shape[1]]
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
        if C.dtype != np.uint8:
            C = C.astype(np.uint8)

    return V, F, C


def export_glb(vertices_f32: np.ndarray, faces_i64: np.ndarray, colors_rgb_u8: Optional[np.ndarray]) -> bytes:
    mesh = trimesh.Trimesh(vertices=vertices_f32, faces=faces_i64, process=False)

    vn = compute_vertex_normals_numpy(vertices_f32, faces_i64)
    mesh._cache["vertex_normals"] = vn

    if colors_rgb_u8 is not None:
        c = colors_rgb_u8
        if c.ndim == 2 and c.shape[1] == 3:
            alpha = np.full((c.shape[0], 1), 255, dtype=np.uint8)
            c = np.concatenate([c, alpha], axis=1)
        if c.shape[0] == vertices_f32.shape[0] and c.shape[1] == 4:
            mesh.visual.vertex_colors = c

    glb = mesh.export(file_type="glb")
    if isinstance(glb, str):
        glb = glb.encode("utf-8")
    return glb


def mesh_frame_bytes_to_glb(frame_bytes: bytes) -> Tuple[bytes, dict, dict]:
    """
    Input: WebSocket binary message for a mesh frame:
      [u32 outer_json_len][outer_json][u32 chunk_len][zlib]...

    Returns:
      (glb_bytes, outer_header, meshheader)
    """
    off = 0
    outer_len, off = read_u32_le(frame_bytes, off)
    if off + outer_len > len(frame_bytes):
        raise ValueError("Outer header truncated")

    outer = json.loads(frame_bytes[off:off + outer_len].decode("utf-8"))
    off += outer_len

    ftype = (outer.get("type") or "").lower()
    if ftype != "mesh":
        raise ValueError(f"Not a mesh frame (type={outer.get('type')!r})")

    compression = (outer.get("compression") or "").lower()
    if compression != "zlib":
        raise ValueError(f"Unsupported compression: {compression!r}")

    payload, _chunks = decompress_zlib_chunks(frame_bytes, off)

    meshheader, end_off = extract_first_json_object(payload)

    v_cnt = int(meshheader.get("vertex_count", 0) or 0)
    t_cnt = int(meshheader.get("triangle_count", 0) or 0)
    if v_cnt == 0 or t_cnt == 0:
        raise ValueError("Empty mesh (vertex_count or triangle_count is 0)")

    vertices, triangles, _normals, colors = decode_global_arrays(payload, meshheader, end_off)
    V, F, C = merge_blocks_to_single_mesh(vertices, triangles, colors, meshheader)
    glb = export_glb(V, F, C)
    return glb, outer, meshheader


def save_glb(glb_bytes: bytes, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(glb_bytes)