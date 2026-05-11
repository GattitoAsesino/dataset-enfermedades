"""Quick CLI to spot-check N random samples of a class via an HTML page.

Usage:
    .venv/bin/python scripts/sample_grid.py --n 30 --class moho_verde
"""
from __future__ import annotations

import argparse
import csv
import html
import random
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT = ROOT / "data" / "manifest_processed.csv"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--class", dest="cls", required=True)
    ap.add_argument("--manifest", default=str(DEFAULT))
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    inp = Path(args.manifest)
    if not inp.exists():
        print(f"missing manifest: {inp}")
        sys.exit(1)
    with open(inp, "r", encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["class"] == args.cls]
    if not rows:
        print(f"no rows for class={args.cls}")
        sys.exit(1)
    rng = random.Random(args.seed)
    rng.shuffle(rows)
    sample = rows[: args.n]
    out = ROOT / "reports" / f"sample_{args.cls}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    parts = [
        "<!doctype html><meta charset='utf-8'>",
        f"<title>Sample {args.cls} N={len(sample)}</title>",
        "<style>body{background:#0f0f0f;color:#eee;font-family:system-ui;margin:1rem}"
        ".g{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:8px}"
        ".c{background:#1a1a1a;border:1px solid #333;border-radius:6px;overflow:hidden}"
        ".c img{width:100%;height:240px;object-fit:cover;display:block}"
        ".m{padding:6px;font-size:12px;color:#aaa}.m a{color:#7af;text-decoration:none}</style>",
        f"<h1>Sample — class={args.cls} N={len(sample)}</h1>",
        "<div class='g'>",
    ]
    for r in sample:
        src = f"../{r['filename']}"
        parts.append(
            f"<div class='c'><a href='{html.escape(r.get('source_url',''))}' target='_blank'>"
            f"<img src='{html.escape(src)}' loading='lazy'></a>"
            f"<div class='m'>{html.escape(r.get('source',''))} · {html.escape(r.get('license',''))}<br>"
            f"{html.escape(r.get('id',''))}</div></div>"
        )
    parts.append("</div>")
    out.write_text("".join(parts), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
