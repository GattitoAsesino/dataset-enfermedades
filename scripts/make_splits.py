"""Generate stratified, anti-leak train/val/test splits.

Anti-leak strategy:
- Group by 'group_key' = best-effort observation/sample identifier so multiple
  photos of the same subject NEVER cross splits.
  - inaturalist: source_id = "{taxon_id}:{obs_id}:{photo_id}" -> group on obs_id
  - gbif:        source_id = "{taxon}:{occ}:{i}"             -> group on occ
  - mushroom_observer: source_id is image id; observation_ids list in API but
    we did not persist it; fall back to image id (i.e. each is its own group)
  - wikimedia:   source_id is page id (each its own group)
- Stratify by class.
- 70/15/15.
- Drop groups with no images.
"""
from __future__ import annotations

import csv
import random
import sys
from collections import defaultdict
from pathlib import Path

from sklearn.model_selection import GroupShuffleSplit

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from _common import MANIFEST_FIELDS  # noqa: E402

INPUT = ROOT / "data" / "manifest_processed.csv"
OUT = ROOT / "data" / "splits"
SEED = 1729
RATIOS = (0.70, 0.15, 0.15)


def group_key(row: dict) -> str:
    src = row.get("source", "")
    sid = row.get("source_id", "")
    if src == "inaturalist":
        # taxon:obs:photo -> observation
        parts = sid.split(":")
        return f"inat:{parts[1]}" if len(parts) >= 2 else f"inat:{sid}"
    if src == "gbif":
        parts = sid.split(":")
        return f"gbif:{parts[1]}" if len(parts) >= 2 else f"gbif:{sid}"
    if src == "mushroom_observer":
        return f"mo:{sid}"
    if src == "wikimedia":
        return f"wm:{sid}"
    return f"{src}:{sid}"


def split_class(rows: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    if not rows:
        return [], [], []
    groups = [group_key(r) for r in rows]
    rng = random.Random(SEED)
    # First split: train vs (val+test)
    gss1 = GroupShuffleSplit(n_splits=1, test_size=RATIOS[1] + RATIOS[2], random_state=SEED)
    idx_train, idx_rest = next(gss1.split(rows, groups=groups))
    rest = [rows[i] for i in idx_rest]
    rest_groups = [groups[i] for i in idx_rest]
    # Second split: val vs test inside the remainder
    val_frac_in_rest = RATIOS[1] / (RATIOS[1] + RATIOS[2])
    gss2 = GroupShuffleSplit(n_splits=1, test_size=1 - val_frac_in_rest, random_state=SEED + 1)
    idx_val, idx_test = next(gss2.split(rest, groups=rest_groups))
    train = [rows[i] for i in idx_train]
    val = [rest[i] for i in idx_val]
    test = [rest[i] for i in idx_test]
    return train, val, test


def write_split(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in MANIFEST_FIELDS})


def main() -> None:
    if not INPUT.exists():
        print(f"missing {INPUT}; run normalize.py first")
        return
    with open(INPUT, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    by_cls: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_cls[r["class"]].append(r)

    splits: dict[str, list[dict]] = {"train": [], "val": [], "test": []}
    for cls, rs in by_cls.items():
        tr, va, te = split_class(rs)
        splits["train"].extend(tr)
        splits["val"].extend(va)
        splits["test"].extend(te)
        print(f"class={cls}: total={len(rs)}  train={len(tr)} val={len(va)} test={len(te)}")

    for name, rs in splits.items():
        out = OUT / f"{name}.csv"
        write_split(rs, out)
        print(f"wrote {out} ({len(rs)} rows)")

    # Anti-leak verification
    train_g = {group_key(r) for r in splits["train"]}
    val_g = {group_key(r) for r in splits["val"]}
    test_g = {group_key(r) for r in splits["test"]}
    overlaps = (
        ("train∩val", train_g & val_g),
        ("train∩test", train_g & test_g),
        ("val∩test", val_g & test_g),
    )
    bad = False
    for name, ov in overlaps:
        if ov:
            bad = True
            print(f"!! {name} group overlap: {len(ov)} groups")
    if not bad:
        print("OK: no group overlap across splits")


if __name__ == "__main__":
    main()
