from pathlib import Path

def save_glb(glb_bytes: bytes) -> Path:
    """
    Speichert GLB-Dateien fortlaufend unter ./tempglbs/frame_XXXXXX.glb
    Gibt den tatsächlichen Pfad zurück.
    """

    base_dir = Path(__file__).resolve().parent
    out_dir = base_dir / "tempglbs"
    out_dir.mkdir(parents=True, exist_ok=True)

    # nächsten freien Index finden
    existing = sorted(out_dir.glob("frame_*.glb"))
    if not existing:
        next_index = 0
    else:
        last = existing[-1].stem  # z.B. frame_000123
        last_index = int(last.split("_")[1])
        next_index = last_index + 1

    out_path = out_dir / f"frame_{next_index:06d}.glb"
    out_path.write_bytes(glb_bytes)

    return out_path