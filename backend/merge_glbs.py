#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys

import trimesh

"""
    Lädt eine GLB und gibt ein einzelnes trimesh zurück (alle zusammengeführt)
    Berücksichtigt Scene-Transforms über scene.dump(concatenate=True)
"""
def glb_to_single_mesh(glb_path: Path) -> trimesh.Trimesh | None:
    loaded = trimesh.load(glb_path, force="scene")

    if isinstance(loaded, trimesh.Trimesh):
        return loaded

    if isinstance(loaded, trimesh.Scene):
        mesh = loaded.dump(concatenate=True)
        if isinstance(mesh, trimesh.Trimesh) and mesh.vertices.size > 0:
            return mesh
        return None

    return None


def merge_folder_to_one_mesh(input_dir: Path, output_file: Path) -> None:
    glbs = sorted(input_dir.glob("*.glb"))
    if not glbs:
        raise FileNotFoundError(f"No .glb files found in: {input_dir}")

    meshes: list[trimesh.Trimesh] = []

    for glb in glbs:
        m = glb_to_single_mesh(glb)
        if m is None or m.vertices.size == 0:
            print(f"Warning: skipping (no mesh): {glb}", file=sys.stderr)
            continue
        meshes.append(m)

    if not meshes:
        raise RuntimeError("No valid meshes loaded from input GLBs.")

    # Das ist der entscheidende Schritt: EIN Mesh erzeugen
    merged = trimesh.util.concatenate(meshes)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    merged.export(output_file)
    print(f"Merged {len(meshes)} GLBs -> single mesh: {output_file}")


def main():
    ap = argparse.ArgumentParser(
        description="Merge all .glb files in a folder into ONE single mesh object (.glb)."
    )
    ap.add_argument("input_dir", help="Folder containing .glb files (e.g. .../glbs)")
    ap.add_argument("-o", "--output", default="merged_single.glb", help="Output file (default: merged_single.glb)")
    args = ap.parse_args()

    input_dir = Path(args.input_dir)
    output_file = Path(args.output)

    if not input_dir.is_dir():
        raise NotADirectoryError(input_dir)

    merge_folder_to_one_mesh(input_dir, output_file)


if __name__ == "__main__":
    main()