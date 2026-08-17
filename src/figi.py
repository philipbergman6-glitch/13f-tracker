"""CUSIP -> ticker via OpenFIGI, with a committed cache at data/ref/cusip_ticker.csv.

Terms confirmed 2026-08-12 (https://www.openfigi.com/api/documentation): the API is
free and open to the public; without an API key the mapping endpoint allows
25 requests/minute with max 10 jobs per request. We run unauthenticated and pace
accordingly. The cache has a manual-override column ('override'); a non-empty
override always wins and is never touched by refreshes.
"""
from __future__ import annotations

import csv
import json
import time
import urllib.error
import urllib.request
from collections.abc import Iterator

from common import REF

MAPPING_URL = "https://api.openfigi.com/v3/mapping"
CACHE_PATH = REF / "cusip_ticker.csv"
CACHE_COLUMNS = ["cusip", "ticker", "figi_name", "exch_code", "security_type",
                 "status", "retrieved", "override"]
JOBS_PER_REQUEST = 10
REQUEST_INTERVAL_S = 60 / 25 + 0.1  # unauthenticated: 25 req/min


def load_cache() -> dict[str, dict]:
    if not CACHE_PATH.exists():
        return {}
    with open(CACHE_PATH, newline="", encoding="utf-8") as fh:
        return {row["cusip"]: row for row in csv.DictReader(fh)}


def save_cache(cache: dict[str, dict]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CACHE_COLUMNS)
        w.writeheader()
        for cusip in sorted(cache):
            w.writerow({c: cache[cusip].get(c, "") for c in CACHE_COLUMNS})


def effective_ticker(entry: dict) -> str:
    return entry.get("override") or entry.get("ticker") or ""


def best_match(result: dict) -> dict:
    """OpenFIGI's first (best) match for one job, or {} when there is none."""
    return (result.get("data") or [{}])[0]


def map_batch(cusips: list[str], *,
              exch_code: str | None = None) -> Iterator[list[tuple[str, dict]]]:
    """Map CUSIPs through the OpenFIGI mapping endpoint.

    Yields one [(cusip, result), ...] list per HTTP request — result is the raw
    per-job object, so callers can read both the match (via best_match) and the
    'error' field. Batching to JOBS_PER_REQUEST, the free-tier pace and the 429
    back-off live here; yielding per request lets callers checkpoint and report
    progress. exch_code pins matches to one exchange, e.g. "US".
    """
    for i in range(0, len(cusips), JOBS_PER_REQUEST):
        batch = cusips[i:i + JOBS_PER_REQUEST]
        job = {"idType": "ID_CUSIP"}
        if exch_code:
            job["exchCode"] = exch_code
        jobs = [dict(job, idValue=c) for c in batch]
        req = urllib.request.Request(
            MAPPING_URL,
            data=json.dumps(jobs).encode(),
            headers={"Content-Type": "application/json"},
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    results = json.loads(resp.read())
                break
            except urllib.error.HTTPError as exc:
                if exc.code == 429 and attempt < 3:
                    time.sleep(30 * (attempt + 1))
                else:
                    raise
        yield list(zip(batch, results))
        time.sleep(REQUEST_INTERVAL_S)


def resolve(cusips: set[str], today: str) -> dict[str, str]:
    """Return cusip->ticker for all cusips, querying OpenFIGI only for cache misses."""
    cache = load_cache()
    missing = sorted(c for c in cusips if c not in cache)
    if missing:
        est_min = len(missing) / JOBS_PER_REQUEST * REQUEST_INTERVAL_S / 60
        print(f"OpenFIGI: {len(missing)} uncached CUSIPs (~{est_min:.0f} min at free rate)")
    done = 0
    for results in map_batch(missing):
        for cusip, result in results:
            best = best_match(result)
            cache[cusip] = {
                "cusip": cusip,
                "ticker": best.get("ticker", ""),
                "figi_name": best.get("name", ""),
                "exch_code": best.get("exchCode", ""),
                "security_type": best.get("securityType", ""),
                "status": "ok" if result.get("data") else result.get("error", "no match"),
                "retrieved": today,
                "override": "",
            }
        save_cache(cache)  # checkpoint each batch; reruns resume from cache
        done += len(results)
        if done % 200 < JOBS_PER_REQUEST or done == len(missing):
            print(f"  OpenFIGI progress: {done}/{len(missing)}")
    return {c: effective_ticker(cache[c]) for c in cusips if c in cache}
