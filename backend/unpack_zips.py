#!/usr/bin/env python3
import argparse
import zipfile
from pathlib import Path
from typing import List

"""
    Entpackt eine einzelne ZIP in dest_dir/<zip_stem>/...
    Gibt den Zielordner zurück.
"""
def unpack_zip(zip_path: Path, dest_dir: Path, *, overwrite: bool = False) -> Path:
    if not zip_path.is_file():
        raise FileNotFoundError(zip_path)

    out_dir = dest_dir / zip_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.infolist()

        # Wenn nicht overwrite: überspringen
        if not overwrite:
            # enn bereits mind. 1 Datei existiert, nicht nochmal entpacken
            if any(out_dir.rglob("*")):
                return out_dir

        # Entpacken
        zf.extractall(out_dir)

    return out_dir

"""
    Nimmt eine ZIP-Datei oder einen Ordner mit ZIPs.
    Entpackt alles nach dest_dir/<zip_stem>/...
    Gibt Liste der entpackten Ordner zurück.
"""
def unpack_many(input_path: Path, dest_dir: Path, *, overwrite: bool = False) -> List[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)

    zips: List[Path]
    if input_path.is_file():
        zips = [input_path]
    else:
        zips = sorted(input_path.glob("*.zip"))

    if not zips:
        raise FileNotFoundError(f"Keine .zip Dateien gefunden in: {input_path}")

    out_dirs: List[Path] = []
    for zp in zips:
        out_dirs.append(unpack_zip(zp, dest_dir, overwrite=overwrite))
    return out_dirs


def main():
    ap = argparse.ArgumentParser(description="Unpack *.zip files into a target folder (each zip into its own subfolder).")
    ap.add_argument("input", help="Path to a .zip file OR a folder containing .zip files")
    ap.add_argument("-d", "--dest", default="_work_unzipped", help="Destination folder (default: _work_unzipped)")
    ap.add_argument("--overwrite", action="store_true", help="Force re-extract even if output folder already has files")
    args = ap.parse_args()

    input_path = Path(args.input)
    dest_dir = Path(args.dest)

    out_dirs = unpack_many(input_path, dest_dir, overwrite=args.overwrite)

    print("Unpacked to:")
    for od in out_dirs:
        print(" -", od)


if __name__ == "__main__":
    main()