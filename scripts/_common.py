"""Shared utilities: config loader, manifest writer, polite HTTP, image validation.

The manifest is the single source of truth — every fetcher appends rows to
data/manifest.csv via append_manifest_rows() so downstream scripts can dedup,
normalize, split, and document without re-touching the network.
"""
from __future__ import annotations

import csv
import hashlib
import io
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import requests
import yaml
from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "configs" / "sources.yaml"
MANIFEST_PATH = ROOT / "data" / "manifest.csv"

MANIFEST_FIELDS = [
    "id",
    "filename",
    "class",
    "source",
    "source_url",
    "source_id",
    "license",
    "author",
    "date_captured",
    "date_fetched",
    "original_resolution",
    "md5",
    "notes",
]


@dataclass
class ManifestRow:
    id: str
    filename: str  # path relative to repo root
    cls: str
    source: str
    source_url: str
    source_id: str
    license: str
    author: str
    date_captured: str
    date_fetched: str
    original_resolution: str
    md5: str
    notes: str = ""

    def as_csv_row(self) -> dict:
        d = asdict(self)
        d["class"] = d.pop("cls")
        return {k: d.get(k, "") for k in MANIFEST_FIELDS}


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_manifest_header() -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=MANIFEST_FIELDS).writeheader()


def append_manifest_rows(rows: list[ManifestRow]) -> None:
    if not rows:
        return
    ensure_manifest_header()
    with open(MANIFEST_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        for r in rows:
            w.writerow(r.as_csv_row())


def known_source_ids(source: str) -> set[str]:
    """Return source_ids already present in the manifest for a given source.

    Lets a fetcher resume without redownloading."""
    if not MANIFEST_PATH.exists():
        return set()
    seen: set[str] = set()
    with open(MANIFEST_PATH, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["source"] == source and row["source_id"]:
                seen.add(row["source_id"])
    return seen


class HttpClient:
    """Polite HTTP client: User-Agent, rate limit, retries, byte cap."""

    def __init__(self, cfg: dict):
        h = cfg["http"]
        self.timeout = h["timeout_seconds"]
        self.rate = h["rate_limit_seconds"]
        self.retries = h["retries"]
        self.backoff = h["backoff_seconds"]
        self.session = requests.Session()
        self.session.headers["User-Agent"] = h["user_agent"]
        self._last = 0.0
        self.max_bytes = cfg["image_rules"]["max_bytes"]

    def _wait(self) -> None:
        delta = time.time() - self._last
        if delta < self.rate:
            time.sleep(self.rate - delta)
        self._last = time.time()

    def get_json(self, url: str, params: dict | None = None) -> dict:
        for attempt in range(self.retries):
            self._wait()
            try:
                r = self.session.get(url, params=params, timeout=self.timeout)
                if r.status_code == 429:
                    time.sleep(self.backoff * (attempt + 2))
                    continue
                r.raise_for_status()
                return r.json()
            except requests.RequestException:
                if attempt == self.retries - 1:
                    raise
                time.sleep(self.backoff * (attempt + 1))
        return {}

    def get_bytes(self, url: str) -> bytes | None:
        for attempt in range(self.retries):
            self._wait()
            try:
                r = self.session.get(url, timeout=self.timeout, stream=True)
                if r.status_code == 429:
                    time.sleep(self.backoff * (attempt + 2))
                    continue
                if r.status_code == 404:
                    return None
                r.raise_for_status()
                buf = io.BytesIO()
                total = 0
                for chunk in r.iter_content(chunk_size=64 * 1024):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > self.max_bytes:
                        return None
                    buf.write(chunk)
                return buf.getvalue()
            except requests.RequestException:
                if attempt == self.retries - 1:
                    return None
                time.sleep(self.backoff * (attempt + 1))
        return None


def validate_and_save(
    blob: bytes,
    out_path: Path,
    image_rules: dict,
) -> tuple[bool, str, str]:
    """Validate image blob and write to disk if valid.

    Returns (ok, original_resolution_str, md5_hex)."""
    try:
        img = Image.open(io.BytesIO(blob))
        img.verify()
    except (UnidentifiedImageError, Exception):  # noqa: BLE001
        return False, "", ""
    img = Image.open(io.BytesIO(blob))
    w, h = img.size
    if w < image_rules["min_width"] or h < image_rules["min_height"]:
        return False, f"{w}x{h}", ""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    md5 = hashlib.md5(blob).hexdigest()
    out_path.write_bytes(blob)
    return True, f"{w}x{h}", md5


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def cap_log(prefix: str, msg: str) -> None:
    print(f"[{prefix}] {msg}", flush=True)
