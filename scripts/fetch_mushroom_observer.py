"""Fetch CC-licensed photos from Mushroom Observer for the Úppa dataset.

API docs: https://mushroomobserver.org/articles/20
We use the public images endpoint filtered by name.
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

API = "https://mushroomobserver.org/api2/images"
SOURCE = "mushroom_observer"

ACCEPTED_LICENSES = {
    "Creative Commons Wikipedia Compatible v3.0",
    "Creative Commons Non-commercial v3.0",
    "Creative Commons Non-commercial v4.0",
    "Creative Commons Wikipedia Compatible v4.0",
    "Creative Commons Attribution v3.0",
    "Creative Commons Attribution v4.0",
    "Creative Commons Attribution-Share Alike v3.0",
    "Creative Commons Attribution-Share Alike v4.0",
    "Public Domain",
}


def normalize_license(raw: str) -> str | None:
    if not raw:
        return None
    if "Public Domain" in raw:
        return "CC0-1.0"
    if "Non-commercial" in raw and "Share Alike" in raw:
        return "CC-BY-NC-SA-4.0"
    if "Non-commercial" in raw:
        return "CC-BY-NC-4.0"
    if "Share Alike" in raw:
        return "CC-BY-SA-4.0"
    if "Attribution" in raw:
        return "CC-BY-4.0"
    if "Wikipedia Compatible" in raw:
        return "CC-BY-SA-4.0"
    return None


def fetch_by_name(http: HttpClient, cfg: dict, cls: str, taxon_name: str, budget: int) -> int:
    seen = known_source_ids(SOURCE)
    raw_dir = ROOT / "data" / "raw" / SOURCE / cls
    raw_dir.mkdir(parents=True, exist_ok=True)
    image_rules = cfg["image_rules"]
    per_page = cfg["limits"][SOURCE]["per_page"]

    saved = 0
    page = 1
    rows: list[ManifestRow] = []
    _ = per_page  # API does not accept per_page; default ~100/page

    while saved < budget:
        params = {
            "name": taxon_name,
            "format": "json",
            "detail": "high",
            "page": page,
        }
        try:
            data = http.get_json(API, params)
        except Exception as e:  # noqa: BLE001
            cap_log(SOURCE, f"  page {page} failed: {e}")
            break
        results = data.get("results", []) or []
        if not results:
            cap_log(SOURCE, f"  no more results at page {page}")
            break

        for img in results:
            if saved >= budget:
                break
            img_id = img.get("id")
            if not img_id:
                continue
            source_id = str(img_id)
            if source_id in seen:
                continue
            lic_raw = (img.get("license") or {}).get("name") if isinstance(img.get("license"), dict) else img.get("license")
            lic = normalize_license(str(lic_raw or ""))
            if not lic:
                continue
            # Mushroom Observer: original size at /orig/{id}.jpg; large at /1280/
            url_orig = f"https://mushroomobserver.org/images/orig/{img_id}.jpg"
            url_alt = f"https://mushroomobserver.org/images/1280/{img_id}.jpg"
            blob = http.get_bytes(url_orig) or http.get_bytes(url_alt)
            if blob is None:
                continue
            fname = raw_dir / f"{source_id}.jpg"
            ok, res, md5 = validate_and_save(blob, fname, image_rules)
            if not ok:
                continue
            owner = img.get("owner") or {}
            author = ""
            if isinstance(owner, dict):
                author = owner.get("legal_name") or owner.get("login_name") or ""
            rows.append(
                ManifestRow(
                    id=f"{SOURCE}_{source_id}",
                    filename=str(fname.relative_to(ROOT)),
                    cls=cls,
                    source=SOURCE,
                    source_url=url_orig,
                    source_id=source_id,
                    license=lic,
                    author=str(author)[:200],
                    date_captured=str(img.get("date") or ""),
                    date_fetched=now_iso(),
                    original_resolution=res,
                    md5=md5,
                    notes=taxon_name,
                )
            )
            saved += 1
            seen.add(source_id)
            if len(rows) >= 50:
                append_manifest_rows(rows)
                rows = []

        cap_log(SOURCE, f"  name={taxon_name} cls={cls} page={page} saved={saved}/{budget}")
        page += 1
        if page > 50:  # safety
            break

    append_manifest_rows(rows)
    return saved


def main() -> None:
    cfg = load_config()
    http = HttpClient(cfg)
    # Mushroom Observer uses scientific names; reuse from gbif taxa
    name_for = {
        "sano": ["Agaricus bisporus"],
        "moho_verde": ["Trichoderma aggressivum", "Trichoderma harzianum", "Trichoderma viride"],
    }
    total = 0
    for cls in cfg["classes"]:
        budget = cfg["limits"][SOURCE][cls]
        names = name_for.get(cls, [])
        if not names:
            continue
        per_name = max(1, budget // len(names))
        for n in names:
            cap_log(SOURCE, f"class={cls} name={n} budget={per_name}")
            got = fetch_by_name(http, cfg, cls, n, per_name)
            cap_log(SOURCE, f"  -> saved {got} for {n}")
            total += got
    cap_log(SOURCE, f"DONE. total saved this run: {total}")


if __name__ == "__main__":
    main()
