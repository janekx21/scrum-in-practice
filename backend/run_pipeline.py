#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

from unpack_zips import unpack_many

"""
    Ruft automatisch bin_to_glb_merge_blocks.py im selben Ordner auf.
"""
def run_converter(extracted_dir: Path) -> None:
    script_dir = Path(__file__).parent
    converter_script = script_dir / "bin_to_glb_merge_blocks.py"

    if not converter_script.is_file():
        raise FileNotFoundError(
            f"Converter not found next to this script: {converter_script}"
        )

    (extracted_dir / "glbs").mkdir(parents=True, exist_ok=True)

    cmd = [sys.executable, str(converter_script), str(extracted_dir)]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)

"""
    Ruft merge_glbs.py 
"""
def run_merge(glb_dir: Path, output_file: Path) -> None:
    script_dir = Path(__file__).parent
    merge_script = script_dir / "merge_glbs.py"

    if not merge_script.is_file():
        raise FileNotFoundError(f"Merge script not found next to this script: {merge_script}")

    cmd = [sys.executable, str(merge_script), str(glb_dir), "-o", str(output_file)]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)

"""
    Pipeline for running the whole converting script from ZIP into GLB to use in the Webfrontend
"""
def main():
    ap = argparse.ArgumentParser(
        description="Pipeline: unzip *.zip in unpack_zips -> run bin_to_glb_merge_blocks.py -> run merge_glbs.py"
    )
    ap.add_argument("input", help="Path to a .zip file OR folder containing .zip files")
    ap.add_argument(
        "-d", "--dest",
        default="_work_unzipped",
        help="Where to unpack zips (default: _work_unzipped)"
    )
    ap.add_argument("--overwrite", action="store_true")
    # optional: merge an/aus default an
    ap.add_argument("--no-merge", action="store_true", help="Do not run merge_glbs.py")

    args = ap.parse_args()

    input_path = Path(args.input)
    dest_dir = Path(args.dest)

    extracted_dirs = unpack_many(input_path, dest_dir, overwrite=args.overwrite)

    for ed in extracted_dirs:
        # 1) Converter laufen lassen
        did_convert_anything = False

        root_bins = list(ed.glob("*.bin"))
        if root_bins:
            run_converter(ed)
            did_convert_anything = True

        subfolders_with_bins = sorted({p.parent for p in ed.rglob("*.bin")})
        for sf in subfolders_with_bins:
            run_converter(sf)
            did_convert_anything = True

        # 2. Danach Merge separat aufrufen
        if not args.no_merge and did_convert_anything:
            glb_dirs = sorted({p.parent for p in ed.rglob("*.glb")})
            for gd in glb_dirs:
                out = gd / "merged_single.glb"
                run_merge(gd, out)

    print("Done.")

if __name__ == "__main__":
    main()