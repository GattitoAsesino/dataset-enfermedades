"""Build a static HTML grid for visual review of the curated dataset.

Lets the user spot-check labels by eye before committing to splits. One file
per class, plus an index page. Embeds thumbnails by reference (relative paths).

Usage:
    .venv/bin/python scripts/build_review_grid.py [manifest_path]
Default manifest: data/manifest_processed.csv
"""
from __future__ import annotations

import csv
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "data" / "manifest_processed.csv"
OUT_DIR = ROOT / "reports"


def render_grid(rows: list[dict], cls: str) -> str:
    parts = [
        "<!doctype html><meta charset='utf-8'>",
        f"<title>Review — {cls}</title>",
        "<style>"
        "body{font-family:system-ui,sans-serif;margin:1rem;background:#0f0f0f;color:#eee}"
        "h1{margin:0 0 1rem}"
        ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:8px}"
        ".card{background:#1a1a1a;border:1px solid #333;border-radius:6px;overflow:hidden}"
        ".card img{width:100%;height:200px;object-fit:cover;display:block}"
        ".meta{padding:6px;font-size:11px;color:#aaa;line-height:1.3}"
        ".meta a{color:#7af;text-decoration:none}"
        ".meta .src{color:#fc7;text-transform:uppercase;font-weight:bold}"
        "</style>",
        f"<h1>Review — class={cls} ({len(rows)} images)</h1>",
        "<div class='grid'>",
    ]
    for r in rows:
        rel = r["filename"]  # relative to repo root
        # path from reports/ to repo root is ../
        src_path = f"../{rel}"
        link = html.escape(r.get("source_url") or "")
        parts.append(
            "<div class='card'>"
            f"<a href='{link}' target='_blank'><img src='{html.escape(src_path)}' loading='lazy'></a>"
            "<div class='meta'>"
            f"<span class='src'>{html.escape(r.get('source',''))}</span> · "
            f"{html.escape(r.get('license',''))}<br>"
            f"id: {html.escape(r.get('id',''))}<br>"
            f"author: {html.escape(r.get('author',''))[:60]}<br>"
            f"date: {html.escape(r.get('date_captured',''))} · {html.escape(r.get('original_resolution',''))}"
            "</div></div>"
        )
    parts.append("</div>")
    return "".join(parts)


def render_index(counts: dict[str, int]) -> str:
    items = "".join(
        f"<li><a href='review_{cls}.html'>{html.escape(cls)}</a> — {n} images</li>"
        for cls, n in counts.items()
    )
    return (
        "<!doctype html><meta charset='utf-8'><title>Review index</title>"
        "<style>body{font-family:system-ui;margin:2rem;background:#0f0f0f;color:#eee}"
        "a{color:#7af}h1{margin:0 0 1rem}</style>"
        "<h1>Úppa dataset — review index</h1>"
        f"<ul>{items}</ul>"
        "<p style='color:#888;font-size:13px;margin-top:2rem'>"
        "Open the per-class pages in a browser to spot-check labels. "
        "Click any image to open the original source.</p>"
    )


def main() -> None:
    inp = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    if not inp.exists():
        print(f"missing manifest: {inp}")
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    by_cls: dict[str, list[dict]] = {}
    with open(inp, "r", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            by_cls.setdefault(r["class"], []).append(r)
    counts = {cls: len(rows) for cls, rows in by_cls.items()}
    for cls, rows in by_cls.items():
        out = OUT_DIR / f"review_{cls}.html"
        out.write_text(render_grid(rows, cls), encoding="utf-8")
        print(f"wrote {out} ({len(rows)} cards)")
    idx = OUT_DIR / "review_index.html"
    idx.write_text(render_index(counts), encoding="utf-8")
    print(f"wrote {idx}")


if __name__ == "__main__":
    main()
