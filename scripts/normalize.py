"""Normalize images to a uniform processed/ tree.

- Convert to RGB sRGB JPG, quality 92
- Resize so max(width, height) == 1024 px (preserve aspect)
- Strip ALL EXIF (privacy compliance)
- Output: data/processed/<class>/<id>.jpg
- Writes data/manifest_processed.csv with the new filenames
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

from PIL import Image, ImageOps
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from _common import MANIFEST_FIELDS  # noqa: E402

INPUT = ROOT / "data" / "manifest_deduped.csv"
OUTPUT = ROOT / "data" / "manifest_processed.csv"
MAX_SIDE = 1024


def normalize_one(src: Path, dst: Path) -> tuple[bool, str]:
    try:
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im)  # respect orientation BEFORE stripping EXIF
            im = im.convert("RGB")
            w, h = im.size
            if max(w, h) > MAX_SIDE:
                scale = MAX_SIDE / float(max(w, h))
                new = (int(round(w * scale)), int(round(h * scale)))
                im = im.resize(new, Image.LANCZOS)
            dst.parent.mkdir(parents=True, exist_ok=True)
            # save without EXIF
            im.save(dst, format="JPEG", quality=92, optimize=True, exif=b"")
            return True, f"{im.size[0]}x{im.size[1]}"
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:120]


def main() -> None:
    if not INPUT.exists():
        print(f"missing {INPUT}; run dedupe.py first")
        return
    with open(INPUT, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    out_rows: list[dict] = []
    failed = 0
    for r in tqdm(rows, desc="normalize"):
        src = ROOT / r["filename"]
        if not src.exists():
            failed += 1
            continue
        dst = ROOT / "data" / "processed" / r["class"] / f"{r['id']}.jpg"
        ok, info = normalize_one(src, dst)
        if not ok:
            failed += 1
            continue
        new_row = dict(r)
        new_row["filename"] = str(dst.relative_to(ROOT))
        # original_resolution stays as the *source* resolution; processed
        # resolution is implied = max side <= 1024
        new_row["notes"] = (r.get("notes") or "") + f" | processed:{info}"
        out_rows.append(new_row)

    print(f"normalized: {len(out_rows)}  failed: {failed}")
    with open(OUTPUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        w.writeheader()
        for r in out_rows:
            w.writerow({k: r.get(k, "") for k in MANIFEST_FIELDS})
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
