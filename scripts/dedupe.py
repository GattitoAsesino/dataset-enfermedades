"""Deduplicate images in the manifest.

Strategy:
1. Drop exact duplicates by md5 (keep earliest fetched).
2. Drop near-duplicates by perceptual hash (phash, hamming distance <= 5).

Writes data/manifest_deduped.csv. Original manifest is preserved.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import imagehash
from PIL import Image
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from _common import MANIFEST_FIELDS  # noqa: E402

MANIFEST = ROOT / "data" / "manifest.csv"
DEDUPED = ROOT / "data" / "manifest_deduped.csv"
PHASH_THRESHOLD = 5  # hamming distance


def load_rows() -> list[dict]:
    if not MANIFEST.exists():
        print("no manifest found")
        return []
    with open(MANIFEST, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_rows(rows: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in MANIFEST_FIELDS})


def main() -> None:
    rows = load_rows()
    print(f"input rows: {len(rows)}")

    # Step 1: drop exact md5 duplicates
    seen_md5: dict[str, dict] = {}
    after_md5: list[dict] = []
    md5_dropped = 0
    for r in rows:
        md5 = r.get("md5") or ""
        if md5 and md5 in seen_md5:
            md5_dropped += 1
            continue
        if md5:
            seen_md5[md5] = r
        after_md5.append(r)
    print(f"  md5 duplicates dropped: {md5_dropped}")
    print(f"  after md5 dedup: {len(after_md5)}")

    # Step 2: perceptual hash dedup (per class — never cross-class merge,
    # those are real label conflicts that need manual review, not dedup)
    by_class: dict[str, list[dict]] = {}
    for r in after_md5:
        by_class.setdefault(r["class"], []).append(r)

    final: list[dict] = []
    phash_dropped_total = 0
    for cls, rows_cls in by_class.items():
        kept_phashes: list[tuple[imagehash.ImageHash, dict]] = []
        dropped = 0
        for r in tqdm(rows_cls, desc=f"phash {cls}"):
            p = ROOT / r["filename"]
            if not p.exists():
                final.append(r)  # missing file — leave as-is for now
                continue
            try:
                with Image.open(p) as img:
                    ph = imagehash.phash(img.convert("RGB"))
            except Exception:  # noqa: BLE001
                final.append(r)
                continue
            is_dup = False
            for kp, _ in kept_phashes:
                if (ph - kp) <= PHASH_THRESHOLD:
                    is_dup = True
                    break
            if is_dup:
                dropped += 1
                continue
            kept_phashes.append((ph, r))
            final.append(r)
        print(f"  class={cls}: kept={len(rows_cls)-dropped} dropped={dropped}")
        phash_dropped_total += dropped

    print(f"phash duplicates dropped: {phash_dropped_total}")
    print(f"final rows: {len(final)}")
    write_rows(final, DEDUPED)
    print(f"wrote {DEDUPED}")


if __name__ == "__main__":
    main()
