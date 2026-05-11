"""Generate YOLO-format dataset from our splits CSVs.

Adapted from https://github.com/DiCZDC/Uppa-Dataset/blob/master/make.py

Differences vs. reference:
- Input is OUR pipeline output (`data/splits/{train,val,test}.csv`), not FungiTastic.
- Class column is `class` (not `species`).
- Image filenames in the manifest are full paths like `data/processed/<class>/<id>.jpg`.
- Lowercase `.jpg` (reference uses `.JPG`).

Output structure (matches reference 1:1):

    dataset/uppa/
    ├── images/{train,val,test}/<id>.jpg     # copies of processed images
    ├── labels/{train,val,test}/<id>.txt     # one line per image: "<class_id> 0.5 0.5 1 1"
    ├── uppa.yaml                            # Ultralytics YAML
    ├── classes.txt                          # one class name per line
    ├── notes.json                           # JSON list of {id,name}
    └── {train,val,test}_labels.csv          # filename,class,class_id (the "csv de etiquetados")

The label format `<id> 0.5 0.5 1 1` is YOLO detection format with a bounding box
covering the WHOLE image — useful when training `yolo detect` for what is
conceptually a classification task.
"""
from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPLITS_DIR = ROOT / "data" / "splits"
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_ROOT = ROOT / "dataset" / "uppa"
SPLITS = ("train", "val", "test")


def mk_dirs() -> None:
    for sub in ("images", "labels"):
        for split in SPLITS:
            (OUT_ROOT / sub / split).mkdir(parents=True, exist_ok=True)


def collect_classes(splits_data: dict[str, list[dict]]) -> list[str]:
    """Stable, sorted, lowercase class names across all splits."""
    seen: set[str] = set()
    for rows in splits_data.values():
        for r in rows:
            cls = (r.get("class") or "").strip()
            if cls:
                seen.add(cls)
    # Stable order: sorted alphabetically. The class index becomes the YOLO class id.
    return sorted(seen)


def write_yaml(classes: list[str]) -> None:
    # Use absolute path so Ultralytics doesn't resolve against its global
    # `datasets_dir` setting (~/.config/Ultralytics/settings.json), which
    # otherwise looks for the dataset in the wrong place.
    lines = [
        "# Ultralytics YOLO dataset config — Úppa moho verde",
        f"path: {OUT_ROOT.resolve()}",
        "train: images/train",
        "val: images/val",
        "test: images/test",
        "names:",
    ]
    for i, cls in enumerate(classes):
        lines.append(f"  {i}: {cls}")
    (OUT_ROOT / "uppa.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_classes_txt(classes: list[str]) -> None:
    (OUT_ROOT / "classes.txt").write_text("\n".join(classes) + "\n", encoding="utf-8")


def write_notes_json(classes: list[str]) -> None:
    notes = {"categories": [{"id": i, "name": c} for i, c in enumerate(classes)]}
    (OUT_ROOT / "notes.json").write_text(json.dumps(notes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def process_split(
    split: str,
    rows: list[dict],
    class_to_id: dict[str, int],
) -> tuple[int, int]:
    """Copy images and write YOLO labels + per-split labels CSV.

    Returns (images_written, missing_count)."""
    img_dir = OUT_ROOT / "images" / split
    lbl_dir = OUT_ROOT / "labels" / split
    csv_path = OUT_ROOT / f"{split}_labels.csv"

    written = 0
    missing = 0
    with open(csv_path, "w", encoding="utf-8", newline="") as csv_f:
        w = csv.writer(csv_f)
        w.writerow(["filename", "class", "class_id"])

        for r in rows:
            cls = (r.get("class") or "").strip()
            if cls not in class_to_id:
                continue
            cid = class_to_id[cls]

            src = ROOT / r["filename"]
            if not src.exists():
                # try absolute path as a fallback
                src = Path(r["filename"])
            if not src.exists():
                missing += 1
                continue

            stem = src.stem
            dst_img = img_dir / f"{stem}.jpg"
            dst_lbl = lbl_dir / f"{stem}.txt"

            shutil.copy2(src, dst_img)
            dst_lbl.write_text(f"{cid} 0.5 0.5 1 1\n", encoding="utf-8")
            w.writerow([f"images/{split}/{stem}.jpg", cls, cid])
            written += 1
    return written, missing


def main() -> None:
    if not SPLITS_DIR.exists():
        print(f"missing splits dir: {SPLITS_DIR}")
        sys.exit(1)

    splits_data: dict[str, list[dict]] = {}
    for split in SPLITS:
        path = SPLITS_DIR / f"{split}.csv"
        if not path.exists():
            print(f"missing {path}; run make_splits.py first")
            sys.exit(1)
        with open(path, "r", encoding="utf-8", newline="") as f:
            splits_data[split] = list(csv.DictReader(f))

    mk_dirs()

    classes = collect_classes(splits_data)
    class_to_id = {c: i for i, c in enumerate(classes)}
    print(f"classes ({len(classes)}):")
    for c, i in class_to_id.items():
        print(f"  {i}: {c}")

    write_yaml(classes)
    write_classes_txt(classes)
    write_notes_json(classes)

    total_written = 0
    total_missing = 0
    for split, rows in splits_data.items():
        n, m = process_split(split, rows, class_to_id)
        print(f"  {split}: {n} images written, {m} missing")
        total_written += n
        total_missing += m

    print(f"DONE. images written: {total_written}  missing: {total_missing}")
    print(f"output: {OUT_ROOT}")
    print()
    print("To train with Ultralytics:")
    print("  pip install ultralytics")
    print(f"  yolo detect train data={OUT_ROOT}/uppa.yaml model=yolo11n.pt epochs=50 imgsz=640")


if __name__ == "__main__":
    main()
