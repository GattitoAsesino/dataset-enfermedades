"""Fetch CC-licensed photos from Wikimedia Commons for the Úppa dataset.

Strategy:
- Use action=query, generator=categorymembers + generator=search
- Resolve image info (URL, license, author) via prop=imageinfo&iiprop=url|user|extmetadata
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from _common import (  # noqa: E402
    HttpClient,
    ManifestRow,
    append_manifest_rows,
    cap_log,
    known_source_ids,
    load_config,
    now_iso,
    validate_and_save,
)

API = "https://commons.wikimedia.org/w/api.php"
SOURCE = "wikimedia"


def normalize_license(raw: str) -> str | None:
    s = (raw or "").lower()
    if "public domain" in s or "cc0" in s or "pd-self" in s:
        return "CC0-1.0"
    if "cc-by-nc-sa" in s or "cc by-nc-sa" in s:
        return "CC-BY-NC-SA-4.0"
    if "cc-by-nc" in s or "cc by-nc" in s:
        return "CC-BY-NC-4.0"
    if "cc-by-sa" in s or "cc by-sa" in s:
        return "CC-BY-SA-4.0"
    if "cc-by" in s or "cc by" in s:
        return "CC-BY-4.0"
    return None


def search_titles(http: HttpClient, query: str, limit: int) -> list[str]:
    titles: list[str] = []
    sroffset = 0
    while len(titles) < limit:
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": f'filetype:bitmap "{query}"',
            "srnamespace": 6,  # File namespace
            "srlimit": min(50, limit - len(titles)),
            "sroffset": sroffset,
        }
        data = http.get_json(API, params)
        results = data.get("query", {}).get("search", []) or []
        if not results:
            break
        titles.extend(r["title"] for r in results)
        sroffset += len(results)
        if "continue" not in data:
            break
    return titles


def get_imageinfo(http: HttpClient, titles: list[str]) -> list[dict]:
    out: list[dict] = []
    # batch in groups of 50 (API limit)
    for i in range(0, len(titles), 50):
        batch = titles[i : i + 50]
        params = {
            "action": "query",
            "format": "json",
            "titles": "|".join(batch),
            "prop": "imageinfo",
            "iiprop": "url|user|extmetadata|size|mime",
        }
        data = http.get_json(API, params)
        pages = data.get("query", {}).get("pages", {}) or {}
        for _, page in pages.items():
            ii = page.get("imageinfo") or []
            if not ii:
                continue
            info = ii[0]
            info["_title"] = page.get("title") or ""
            info["_pageid"] = page.get("pageid")
            out.append(info)
    return out


def fetch_for_query(http: HttpClient, cfg: dict, cls: str, query: str, budget: int) -> int:
    seen = known_source_ids(SOURCE)
    raw_dir = ROOT / "data" / "raw" / SOURCE / cls
    raw_dir.mkdir(parents=True, exist_ok=True)
    image_rules = cfg["image_rules"]

    titles = search_titles(http, query, budget * 3)  # over-fetch to account for license filter
    cap_log(SOURCE, f"  query='{query}' candidates={len(titles)}")
    infos = get_imageinfo(http, titles)

    saved = 0
    rows: list[ManifestRow] = []
    for info in infos:
        if saved >= budget:
            break
        url = info.get("url")
        mime = info.get("mime") or ""
        if not url or "image/" not in mime:
            continue
        source_id = str(info.get("_pageid") or info.get("_title") or url)
        if source_id in seen:
            continue
        ext = info.get("extmetadata") or {}
        lic_raw = ((ext.get("LicenseShortName") or {}).get("value") or "")
        lic = normalize_license(lic_raw)
        if not lic:
            continue
        author_raw = (ext.get("Artist") or {}).get("value") or info.get("user") or ""
        # strip HTML tags from author
        import re
        author = re.sub(r"<[^>]+>", "", str(author_raw)).strip()[:200]
        date_captured = (ext.get("DateTimeOriginal") or {}).get("value") or ""

        blob = http.get_bytes(url)
        if blob is None:
            continue
        # filename derived from page id to avoid collisions / unicode trouble
        fname = raw_dir / f"{source_id.replace('/', '_').replace(' ', '_')[:80]}.jpg"
        ok, res, md5 = validate_and_save(blob, fname, image_rules)
        if not ok:
            continue
        rows.append(
            ManifestRow(
                id=f"{SOURCE}_{source_id.replace('/', '_').replace(' ', '_')[:80]}",
                filename=str(fname.relative_to(ROOT)),
                cls=cls,
                source=SOURCE,
                source_url=url,
                source_id=source_id,
                license=lic,
                author=author,
                date_captured=str(date_captured)[:32],
                date_fetched=now_iso(),
                original_resolution=res,
                md5=md5,
                notes=query,
            )
        )
        saved += 1
        seen.add(source_id)
        if len(rows) >= 50:
            append_manifest_rows(rows)
            rows = []

    append_manifest_rows(rows)
    return saved


def main() -> None:
    cfg = load_config()
    http = HttpClient(cfg)
    queries = {
        "sano": ["Agaricus bisporus"],
        "moho_verde": ["Trichoderma aggressivum", "Trichoderma harzianum", "Trichoderma viride", "Trichoderma green mold mushroom"],
    }
    total = 0
    for cls in cfg["classes"]:
        budget = cfg["limits"][SOURCE][cls]
        qs = queries.get(cls, [])
        if not qs:
            continue
        per_q = max(1, budget // len(qs))
        for q in qs:
            cap_log(SOURCE, f"class={cls} q='{q}' budget={per_q}")
            got = fetch_for_query(http, cfg, cls, q, per_q)
            cap_log(SOURCE, f"  -> saved {got} for '{q}'")
            total += got
    cap_log(SOURCE, f"DONE. total saved this run: {total}")


if __name__ == "__main__":
    main()
