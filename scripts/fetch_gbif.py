"""Fetch CC-licensed photos from GBIF for the Úppa dataset.

GBIF media licenses are heterogeneous; we accept only CC0/CC-BY/CC-BY-NC and skip
all-rights-reserved or unspecified.
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

API = "https://api.gbif.org/v1/occurrence/search"
SOURCE = "gbif"

# GBIF stores license as URL or a short code; map common cases
def normalize_license(raw: str | None) -> str | None:
    if not raw:
        return None
    s = raw.lower()
    if "cc0" in s or "publicdomain" in s:
        return "CC0-1.0"
    if "by-nc-sa" in s:
        return "CC-BY-NC-SA-4.0"
    if "by-nc-nd" in s:
        return "CC-BY-NC-ND-4.0"
    if "by-nc" in s:
        return "CC-BY-NC-4.0"
    if "by-sa" in s:
        return "CC-BY-SA-4.0"
    if "by-nd" in s:
        return "CC-BY-ND-4.0"
    if "by/" in s or s.endswith("by") or "creativecommons.org/licenses/by/" in s:
        return "CC-BY-4.0"
    return None  # reject unknown / restrictive


def fetch_for_taxon(http: HttpClient, cfg: dict, cls: str, taxon_key: int, budget: int) -> int:
    seen = known_source_ids(SOURCE)
    raw_dir = ROOT / "data" / "raw" / SOURCE / cls
    raw_dir.mkdir(parents=True, exist_ok=True)
    image_rules = cfg["image_rules"]
    per_page = cfg["limits"][SOURCE]["per_page"]
    media_type = cfg["limits"][SOURCE]["media_type"]

    saved = 0
    offset = 0
    rows: list[ManifestRow] = []

    while saved < budget:
        params = {
            "taxonKey": taxon_key,
            "mediaType": media_type,
            "limit": per_page,
            "offset": offset,
        }
        try:
            data = http.get_json(API, params)
        except Exception as e:  # noqa: BLE001
            cap_log(SOURCE, f"  offset {offset} failed: {e}")
            break
        results = data.get("results", [])
        if not results:
            cap_log(SOURCE, f"  no more results at offset {offset}")
            break

        for occ in results:
            if saved >= budget:
                break
            occ_id = occ.get("key") or occ.get("gbifID")
            captured = occ.get("eventDate") or ""
            for i, m in enumerate(occ.get("media", []) or []):
                if saved >= budget:
                    break
                if (m.get("type") or "") != "StillImage":
                    continue
                identifier = m.get("identifier") or m.get("references")
                if not identifier:
                    continue
                lic = normalize_license(m.get("license") or occ.get("license"))
                if not lic:
                    continue
                source_id = f"{taxon_key}:{occ_id}:{i}"
                if source_id in seen:
                    continue
                blob = http.get_bytes(identifier)
                if blob is None:
                    continue
                fname = raw_dir / f"{source_id.replace(':', '_')}.jpg"
                ok, res, md5 = validate_and_save(blob, fname, image_rules)
                if not ok:
                    continue
                rows.append(
                    ManifestRow(
                        id=f"{SOURCE}_{source_id.replace(':', '_')}",
                        filename=str(fname.relative_to(ROOT)),
                        cls=cls,
                        source=SOURCE,
                        source_url=identifier,
                        source_id=source_id,
                        license=lic,
                        author=str((m.get("creator") or m.get("rightsHolder") or "")).strip()[:200],
                        date_captured=captured,
                        date_fetched=now_iso(),
                        original_resolution=res,
                        md5=md5,
                        notes=str(occ.get("country") or ""),
                    )
                )
                saved += 1
                seen.add(source_id)
                if len(rows) >= 50:
                    append_manifest_rows(rows)
                    rows = []

        cap_log(SOURCE, f"  taxon={taxon_key} cls={cls} offset={offset} saved={saved}/{budget}")
        offset += per_page
        if data.get("endOfRecords"):
            break

    append_manifest_rows(rows)
    return saved


def main() -> None:
    cfg = load_config()
    http = HttpClient(cfg)
    total = 0
    for cls in cfg["classes"]:
        budget = cfg["limits"][SOURCE][cls]
        taxa = cfg["taxa"][cls].get("gbif", [])
        if not taxa:
            continue
        per_taxon = max(1, budget // len(taxa))
        for t in taxa:
            cap_log(SOURCE, f"class={cls} taxon={t['name']}({t['taxon_key']}) budget={per_taxon}")
            got = fetch_for_taxon(http, cfg, cls, t["taxon_key"], per_taxon)
            cap_log(SOURCE, f"  -> saved {got} for {t['name']}")
            total += got
    cap_log(SOURCE, f"DONE. total saved this run: {total}")


if __name__ == "__main__":
    main()
