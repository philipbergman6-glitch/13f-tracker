"""Shared plumbing for the 13F pipeline: paths, quarter math, manager map, EDGAR HTTP.

Source-of-truth decisions: docs/adr/0001-edgar-only-source-of-truth.md and
.scratch/13f-tracker/issues/03-source-of-truth-and-schema.md. Terminology: CONTEXT.md.
"""
from __future__ import annotations

import csv
import datetime
import json
import re
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
RAW = DATA / "raw"
OUT = DATA / "out"
REF = DATA / "ref"
HOLDINGS = DATA / "holdings"

# SEC fair-use policy (https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data):
# max 10 req/s with a declared User-Agent. We stay well under.
USER_AGENT = "GEMS Investment Research gemsai62@gmail.com"
MIN_INTERVAL_S = 0.15

_last_request_at = 0.0


def http_get(url: str, retries: int = 3) -> bytes:
    """Rate-limited GET with the declared UA. Raises on final failure."""
    global _last_request_at
    for attempt in range(retries + 1):
        wait = MIN_INTERVAL_S - (time.monotonic() - _last_request_at)
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
        })
        _last_request_at = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    import gzip
                    body = gzip.decompress(body)
                return body
        except Exception as exc:  # noqa: BLE001 - retry any transport error
            if attempt == retries:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def fetch_cached(url: str, dest: Path, mutable: bool = False) -> Path:
    """Download url to dest unless a usable cached copy exists (data/raw is a cache).

    Immutable artifacts (accession documents) are cached forever. Mutable indexes
    (mutable=True, e.g. submissions JSON — SEC updates them in place) are re-fetched
    unless the cached copy was already retrieved today; a superseded copy is archived
    under data/raw/_archive/superseded/<retrieval-date>/ before being replaced.
    """
    if dest.exists() and dest.stat().st_size > 0:
        retrieved = datetime.date.fromtimestamp(dest.stat().st_mtime)
        if not mutable or retrieved == datetime.date.today():
            return dest
        body = http_get(url)
        if body == dest.read_bytes():
            dest.touch()  # unchanged upstream; restamp the retrieval date
            return dest
        archive = (RAW / "_archive" / "superseded" / retrieved.isoformat()
                   / dest.relative_to(RAW))
        archive.parent.mkdir(parents=True, exist_ok=True)
        dest.replace(archive)
        dest.write_bytes(body)
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(http_get(url))
    return dest


# --- quarters ---------------------------------------------------------------

QUARTER_END = {1: "03-31", 2: "06-30", 3: "09-30", 4: "12-31"}


def quarter_key(year: int, q: int) -> str:
    return f"{year}Q{q}"


def quarter_end_date(qkey: str) -> str:
    """'2026Q2' -> '2026-06-30' (matches EDGAR reportDate)."""
    year, q = int(qkey[:4]), int(qkey[5])
    return f"{year}-{QUARTER_END[q]}"


def quarter_range(start: str, end: str) -> list[str]:
    """Inclusive list of quarter keys from start to end, e.g. 2024Q2..2026Q2."""
    y, q = int(start[:4]), int(start[5])
    ey, eq = int(end[:4]), int(end[5])
    quarters = []
    while (y, q) <= (ey, eq):
        quarters.append(quarter_key(y, q))
        q += 1
        if q == 5:
            y, q = y + 1, 1
    return quarters


def qkey_le(a: str, b: str) -> bool:
    return (int(a[:4]), int(a[5])) <= (int(b[:4]), int(b[5]))


# --- manager map ------------------------------------------------------------

@dataclass
class FilerSpan:
    manager: str
    cik: int
    filer_name: str
    from_quarter: str | None
    to_quarter: str | None

    def covers(self, qkey: str) -> bool:
        if self.from_quarter and not qkey_le(self.from_quarter, qkey):
            return False
        if self.to_quarter and not qkey_le(qkey, self.to_quarter):
            return False
        return True


def load_manager_map() -> list[FilerSpan]:
    spans = []
    with open(REF / "manager_map.csv", newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            spans.append(FilerSpan(
                manager=row["manager"],
                cik=int(row["filer_cik"]),
                filer_name=row["filer_name"],
                from_quarter=row["from_quarter"] or None,
                to_quarter=row["to_quarter"] or None,
            ))
    return spans


def manager_slug(manager: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", manager.lower()).strip("-")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))
