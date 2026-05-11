"""Fetch relevant Kaggle datasets if a kaggle.json token is configured.

Skips gracefully if no token. Kaggle datasets vary in structure; this script
downloads them as zip, extracts, and the user (or curate step) decides which
folders correspond to 'sano' vs 'moho_verde'.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from _common import cap_log, load_config  # noqa: E402

SOURCE = "kaggle"
KAGGLE_JSON = Path.home() / ".kaggle" / "kaggle.json"

# Curated list of Kaggle datasets that may contain Agaricus bisporus or
# Trichoderma / mushroom disease imagery. The user can prune this in sources.yaml.
CANDIDATE_DATASETS = [
    "shubhammeshram579/mushrooms-classification",
    "harperd17/mushroom-pictures",
    "lizhecheng/mushroom-classification",
    "maysee/mushrooms-classification-common-genuss-images",
    "shrutidey1503/mushroom-disease-detection",
]


def have_kaggle_token() -> bool:
    return KAGGLE_JSON.exists()


def main() -> None:
    cfg = load_config()
    if not cfg["limits"][SOURCE].get("enabled", False) and not have_kaggle_token():
        cap_log(SOURCE, "skipped: no kaggle.json present and not enabled in config")
        return
    try:
        import kaggle  # noqa: F401
    except ImportError:
        cap_log(SOURCE, "skipped: 'kaggle' package not installed (pip install kaggle)")
        return

    out_root = ROOT / "data" / "raw" / SOURCE / "_unsorted"
    out_root.mkdir(parents=True, exist_ok=True)
    saved = 0
    for slug in CANDIDATE_DATASETS:
        target = out_root / slug.replace("/", "__")
        if target.exists():
            cap_log(SOURCE, f"  already downloaded: {slug}")
            continue
        target.mkdir(parents=True, exist_ok=True)
        cap_log(SOURCE, f"  downloading {slug}")
        proc = subprocess.run(
            ["kaggle", "datasets", "download", "-d", slug, "-p", str(target), "--unzip"],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            cap_log(SOURCE, f"    FAILED: {proc.stderr.strip()[:200]}")
            shutil.rmtree(target, ignore_errors=True)
            continue
        n_imgs = sum(
            1 for p in target.rglob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        )
        cap_log(SOURCE, f"    OK: {n_imgs} images extracted")
        saved += n_imgs

    cap_log(SOURCE, f"DONE. images extracted (unsorted): {saved}")
    cap_log(
        SOURCE,
        "  NOTE: kaggle images are NOT auto-added to manifest. Manual curation step "
        "needed to map directory structures to {sano, moho_verde}. See KAGGLE_CURATION.md.",
    )


if __name__ == "__main__":
    main()
