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
import urllib.request

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


def resolve(cusips: set[str], today: str) -> dict[str, str]:
    """Return cusip->ticker for all cusips, querying OpenFIGI only for cache misses."""
    cache = load_cache()
    missing = sorted(c for c in cusips if c not in cache)
    if missing:
        est_min = len(missing) / JOBS_PER_REQUEST * REQUEST_INTERVAL_S / 60
        print(f"OpenFIGI: {len(missing)} uncached CUSIPs (~{est_min:.0f} min at free rate)")
    for i in range(0, len(missing), JOBS_PER_REQUEST):
        batch = missing[i:i + JOBS_PER_REQUEST]
        jobs = [{"idType": "ID_CUSIP", "idValue": c} for c in batch]
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
        for cusip, result in zip(batch, results):
            best = (result.get("data") or [{}])[0]
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
        done = i + len(batch)
        if done % 200 < JOBS_PER_REQUEST or done == len(missing):
            print(f"  OpenFIGI progress: {done}/{len(missing)}")
        time.sleep(REQUEST_INTERVAL_S)
    return {c: effective_ticker(cache[c]) for c in cusips if c in cache}
