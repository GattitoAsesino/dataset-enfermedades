"""Build reports/source_yields.md with per-source, per-class counts and licenses."""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT = ROOT / "data" / "manifest.csv"
OUT = ROOT / "reports" / "source_yields.md"


def main() -> None:
    inp = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    if not inp.exists():
        print(f"missing {inp}")
        return
    with open(inp, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    by_src_cls: dict[tuple[str, str], int] = defaultdict(int)
    by_lic: Counter = Counter()
    by_cls: Counter = Counter()
    for r in rows:
        by_src_cls[(r["source"], r["class"])] += 1
        by_lic[r["license"]] += 1
        by_cls[r["class"]] += 1

    sources = sorted({s for s, _ in by_src_cls.keys()})
    classes = sorted({c for _, c in by_src_cls.keys()})

    lines: list[str] = []
    lines.append(f"# Source Yields — {inp.name}\n")
    lines.append(f"Total images: **{len(rows)}**\n")
    lines.append("## Counts per source × class\n")
    header = "| source | " + " | ".join(classes) + " | total |"
    sep = "|---" * (len(classes) + 2) + "|"
    lines.append(header)
    lines.append(sep)
    for s in sources:
        cells = [f"{by_src_cls.get((s, c), 0)}" for c in classes]
        total = sum(by_src_cls.get((s, c), 0) for c in classes)
        lines.append(f"| {s} | " + " | ".join(cells) + f" | **{total}** |")
    cls_totals = [str(by_cls[c]) for c in classes]
    lines.append(f"| **total** | " + " | ".join(cls_totals) + f" | **{len(rows)}** |\n")

    lines.append("## License distribution\n")
    lines.append("| license | count |\n|---|---|")
    for lic, n in by_lic.most_common():
        lines.append(f"| {lic or '(unknown)'} | {n} |")
    lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
