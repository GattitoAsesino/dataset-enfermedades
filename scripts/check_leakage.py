"""Verify that no md5 / source_id appears in more than one split.

Exits with non-zero status if leakage is detected. Used as a CI gate.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPLITS = ROOT / "data" / "splits"


def load_split(name: str) -> list[dict]:
    p = SPLITS / f"{name}.csv"
    if not p.exists():
        return []
    with open(p, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    splits = {n: load_split(n) for n in ("train", "val", "test")}
    bad = 0
    for key in ("md5", "source_id"):
        sets = {n: {r[key] for r in rs if r.get(key)} for n, rs in splits.items()}
        for a, b in [("train", "val"), ("train", "test"), ("val", "test")]:
            ov = sets[a] & sets[b]
            if ov:
                bad += 1
                print(f"!! leakage on {key}: {a} ∩ {b} = {len(ov)} items")
                # show a few
                for x in list(ov)[:5]:
                    print(f"   - {x}")
    if bad == 0:
        for n, rs in splits.items():
            print(f"OK {n}: {len(rs)} rows")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
