"""Fetch CC-licensed photos from iNaturalist for the Úppa dataset.

Strategy:
- For each (class, taxon_id), page through /v1/observations with quality_grade=research
  and a photo license filter.
- Each observation may have multiple photos; we save the original-size URL.
- Resume safely: source_id = f"{taxon_id}:{observation_id}:{photo_id}".
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

API = "https://api.inaturalist.org/v1/observations"
SOURCE = "inaturalist"

# Map iNaturalist photo_license codes to canonical SPDX-ish strings
LICENSE_MAP = {
    "cc0": "CC0-1.0",
    "cc-by": "CC-BY-4.0",
    "cc-by-nc": "CC-BY-NC-4.0",
    "cc-by-sa": "CC-BY-SA-4.0",
    "cc-by-nd": "CC-BY-ND-4.0",
    "cc-by-nc-sa": "CC-BY-NC-SA-4.0",
    "cc-by-nc-nd": "CC-BY-NC-ND-4.0",
}


def original_url(photo_url: str) -> str:
    """iNaturalist returns a 'square' or 'medium' URL; swap to 'original'."""
    for size in ("square", "small", "medium", "large"):
        photo_url = photo_url.replace(f"/{size}.", "/original.")
    return photo_url


def fetch_for_taxon(http: HttpClient, cfg: dict, cls: str, taxon_id: int, budget: int) -> int:
    seen = known_source_ids(SOURCE)
    raw_dir = ROOT / "data" / "raw" / SOURCE / cls
    raw_dir.mkdir(parents=True, exist_ok=True)

    licenses = ",".join(cfg["limits"]["inaturalist"]["photo_licenses"])
    per_page = cfg["limits"]["inaturalist"]["per_page"]
    image_rules = cfg["image_rules"]

    saved = 0
    page = 1
    rows: list[ManifestRow] = []

    while saved < budget:
        params = {
            "taxon_id": taxon_id,
            "quality_grade": "research",
            "photo_license": licenses,
            "per_page": per_page,
            "page": page,
            "order": "desc",
            "order_by": "created_at",
        }
        try:
            data = http.get_json(API, params)
        except Exception as e:  # noqa: BLE001
            cap_log(SOURCE, f"  page {page} failed: {e}")
            break
        results = data.get("results", [])
        if not results:
            cap_log(SOURCE, f"  no more results at page {page}")
            break

        for obs in results:
            if saved >= budget:
                break
            obs_id = obs.get("id")
            captured = obs.get("observed_on") or ""
            for photo in obs.get("photos", []):
                if saved >= budget:
                    break
                photo_id = photo.get("id")
                lic_code = (photo.get("license_code") or "").lower()
                if lic_code not in LICENSE_MAP:
                    continue
                source_id = f"{taxon_id}:{obs_id}:{photo_id}"
                if source_id in seen:
                    continue
                url_med = photo.get("url") or ""
                if not url_med:
                    continue
                url_orig = original_url(url_med)
                blob = http.get_bytes(url_orig)
                if blob is None:
                    blob = http.get_bytes(url_med)
                if blob is None:
                    continue
                ext = ".jpg"
                fname = raw_dir / f"{source_id.replace(':', '_')}{ext}"
                ok, res, md5 = validate_and_save(blob, fname, image_rules)
                if not ok:
                    continue
                rows.append(
                    ManifestRow(
                        id=f"{SOURCE}_{source_id.replace(':', '_')}",
                        filename=str(fname.relative_to(ROOT)),
                        cls=cls,
                        source=SOURCE,
                        source_url=url_orig,
                        source_id=source_id,
                        license=LICENSE_MAP[lic_code],
                        author=str((photo.get("attribution") or "").strip())[:200],
                        date_captured=captured,
                        date_fetched=now_iso(),
                        original_resolution=res,
                        md5=md5,
                    )
                )
                saved += 1
                seen.add(source_id)
                if len(rows) >= 50:
                    append_manifest_rows(rows)
                    rows = []

        cap_log(SOURCE, f"  taxon={taxon_id} cls={cls} page={page} saved={saved}/{budget}")
        page += 1
        # iNat caps deep paging at ~10000 / per_page; bail before that
        if page * per_page > 9000:
            break

    append_manifest_rows(rows)
    return saved


def main() -> None:
    cfg = load_config()
    http = HttpClient(cfg)
    total = 0
    for cls in cfg["classes"]:
        budget_left = cfg["limits"][SOURCE][cls]
        taxa = cfg["taxa"][cls].get("inaturalist", [])
        if not taxa:
            continue
        per_taxon = max(1, budget_left // len(taxa))
        for t in taxa:
            cap_log(SOURCE, f"class={cls} taxon={t['name']}({t['taxon_id']}) budget={per_taxon}")
            got = fetch_for_taxon(http, cfg, cls, t["taxon_id"], per_taxon)
            cap_log(SOURCE, f"  -> saved {got} for {t['name']}")
            total += got
    cap_log(SOURCE, f"DONE. total saved this run: {total}")


if __name__ == "__main__":
    main()
