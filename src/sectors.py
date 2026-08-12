"""CUSIP -> sector via SEC SIC codes, committed to data/ref/sectors.csv.

Chain: cusip -> ticker (data/ref/cusip_ticker.csv, OpenFIGI cache) -> CIK
(SEC company_tickers.json) -> SIC code (data.sec.gov/submissions) -> sector
(SIC_SECTOR rollup below). Primary source throughout: SEC EDGAR. The rollup
from SIC major groups to GICS-style sector names is our own mapping (defined
here, not an official concordance) - the dashboard labels it "SIC-derived".

SIC code list: https://www.sec.gov/corpfin/division-of-corporation-finance-standard-industrial-classification-sic-code-list
Raw submissions JSONs are cached under data/raw/sectors/ (re-fetchable).

Usage:
    python src/sectors.py            # fetch missing rows, rewrite sectors.csv
"""
from __future__ import annotations

import csv
import datetime as dt
import json

import figi
from common import RAW, REF, fetch_cached, load_json

SECTORS_PATH = REF / "sectors.csv"
SECTOR_COLUMNS = ["cusip", "ticker", "cik", "sic", "sic_desc", "sector",
                  "method", "retrieved"]

# Ordered (lo, hi, sector): first match wins, so specific carve-outs come
# before the broad range they punch a hole in.
SIC_SECTOR = [
    (100, 999, "Consumer Staples"),           # agriculture
    (1000, 1299, "Materials"),                # metal mining, coal
    (1300, 1399, "Energy"),                   # oil & gas extraction/services
    (1400, 1499, "Materials"),
    (1500, 1799, "Industrials"),              # construction
    (2000, 2199, "Consumer Staples"),         # food, beverage, tobacco
    (2200, 2399, "Consumer Discretionary"),   # textiles, apparel
    (2400, 2699, "Materials"),                # lumber, paper
    (2700, 2799, "Communication Services"),   # printing & publishing
    (2830, 2836, "Health Care"),              # drugs, biologics
    (2800, 2899, "Materials"),                # chemicals ex-pharma
    (2900, 2999, "Energy"),                   # petroleum refining
    (3000, 3099, "Materials"),                # rubber, plastics
    (3100, 3199, "Consumer Discretionary"),   # leather
    (3200, 3499, "Materials"),                # stone, glass, metals
    (3570, 3579, "Information Technology"),   # computers, storage
    (3500, 3599, "Industrials"),              # machinery
    (3600, 3659, "Industrials"),              # electrical equipment
    (3660, 3699, "Information Technology"),   # comms equipment, semis
    (3710, 3716, "Consumer Discretionary"),   # autos
    (3700, 3799, "Industrials"),              # aerospace, rail, ships
    (3820, 3859, "Health Care"),              # lab/medical instruments
    (3800, 3899, "Industrials"),              # other instruments, defense
    (3900, 3999, "Consumer Discretionary"),   # misc manufacturing
    (4000, 4799, "Industrials"),              # transportation, airlines
    (4800, 4899, "Communication Services"),   # telecom, cable
    (4900, 4999, "Utilities"),
    (5122, 5122, "Health Care"),              # wholesale drugs (McKesson etc.)
    (5000, 5199, "Consumer Discretionary"),   # wholesale trade
    (5411, 5411, "Consumer Staples"),         # grocery stores
    (5912, 5912, "Consumer Staples"),         # drug stores
    (5200, 5999, "Consumer Discretionary"),   # retail
    (6500, 6599, "Real Estate"),
    (6798, 6798, "Real Estate"),              # REITs
    (6000, 6999, "Financials"),
    (7000, 7099, "Consumer Discretionary"),   # hotels
    (7370, 7379, "Information Technology"),   # software, data processing
    (7100, 7699, "Industrials"),              # business & repair services
    (7800, 7999, "Communication Services"),   # movies, entertainment
    (8000, 8099, "Health Care"),              # health services
    (8100, 8999, "Industrials"),              # legal, engineering, consulting
]

# OpenFIGI security types that are funds rather than single issuers.
FUND_TYPES = {"ETP", "Closed-End Fund", "Open-End Fund", "Unit Inv Tst"}

COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


def sic_to_sector(sic: int) -> str:
    for lo, hi, sector in SIC_SECTOR:
        if lo <= sic <= hi:
            return sector
    return "Unclassified"


def normalize_ticker(ticker: str) -> str:
    """FIGI 'BRK/B' -> EDGAR 'BRK-B' style."""
    return ticker.upper().replace("/", "-").replace(" ", "-")


def load_ticker_cik_map() -> dict[str, int]:
    path = fetch_cached(COMPANY_TICKERS_URL, RAW / "sectors" / "company_tickers.json")
    data = load_json(path)
    return {normalize_ticker(row["ticker"]): int(row["cik_str"])
            for row in data.values()}


def fetch_sic(cik: int) -> tuple[str, str]:
    """Return (sic, sicDescription) from the cached EDGAR submissions JSON."""
    url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
    path = fetch_cached(url, RAW / "sectors" / f"CIK{cik:010d}.json")
    data = load_json(path)
    return str(data.get("sic") or ""), data.get("sicDescription") or ""


def load_sectors() -> dict[str, dict]:
    if not SECTORS_PATH.exists():
        return {}
    with open(SECTORS_PATH, newline="", encoding="utf-8") as fh:
        return {row["cusip"]: row for row in csv.DictReader(fh)}


def save_sectors(rows: dict[str, dict]) -> None:
    with open(SECTORS_PATH, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=SECTOR_COLUMNS)
        w.writeheader()
        for cusip in sorted(rows):
            w.writerow({c: rows[cusip].get(c, "") for c in SECTOR_COLUMNS})


def classify_cusip(cusip: str, figi_entry: dict, cik_map: dict[str, int],
                   today: str) -> dict:
    ticker = figi.effective_ticker(figi_entry)
    sec_type = figi_entry.get("security_type", "")
    row = {"cusip": cusip, "ticker": ticker, "cik": "", "sic": "",
           "sic_desc": "", "sector": "Unclassified", "method": "unmapped",
           "retrieved": today}
    if sec_type in FUND_TYPES:
        row.update(sector="Funds & ETFs", method="figi_type")
        return row
    cik = cik_map.get(normalize_ticker(ticker)) if ticker else None
    if cik:
        sic, sic_desc = fetch_sic(cik)
        row.update(cik=str(cik), sic=sic, sic_desc=sic_desc, method="sec_sic")
        if sic.isdigit():
            row["sector"] = sic_to_sector(int(sic))
    return row


def us_ticker_lookup(cusips: list[str]) -> dict[str, str]:
    """Re-query OpenFIGI pinned to US listings for CUSIPs whose cached best
    match was a foreign listing (or none). Returns cusip -> US ticker."""
    import time
    import urllib.request
    out: dict[str, str] = {}
    for i in range(0, len(cusips), figi.JOBS_PER_REQUEST):
        batch = cusips[i:i + figi.JOBS_PER_REQUEST]
        jobs = [{"idType": "ID_CUSIP", "idValue": c, "exchCode": "US"}
                for c in batch]
        req = urllib.request.Request(
            figi.MAPPING_URL, data=json.dumps(jobs).encode(),
            headers={"Content-Type": "application/json"})
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
            if best.get("ticker"):
                out[cusip] = best["ticker"]
        time.sleep(figi.REQUEST_INTERVAL_S)
    return out


def repair_unmapped(rows: dict[str, dict], figi_cache: dict[str, dict],
                    cik_map: dict[str, int], today: str) -> int:
    """Second pass over method=unmapped rows via the US-listing lookup.
    Winning tickers are also written to the cusip_ticker.csv override column,
    so the committed holdings CSVs pick them up on the next pipeline run."""
    todo = sorted(c for c, r in rows.items() if r["method"] == "unmapped")
    if not todo:
        return 0
    print(f"sectors: retrying {len(todo)} unmapped CUSIPs against US listings "
          f"(~{len(todo) / figi.JOBS_PER_REQUEST * figi.REQUEST_INTERVAL_S / 60:.0f} min)")
    found = us_ticker_lookup(todo)
    n_fixed = 0
    for cusip, ticker in found.items():
        cik = cik_map.get(normalize_ticker(ticker))
        if not cik:
            continue
        sic, sic_desc = fetch_sic(cik)
        rows[cusip].update(ticker=ticker, cik=str(cik), sic=sic,
                           sic_desc=sic_desc, method="sec_sic_usfigi",
                           retrieved=today)
        if sic.isdigit():
            rows[cusip]["sector"] = sic_to_sector(int(sic))
        if figi.effective_ticker(figi_cache[cusip]) != ticker:
            figi_cache[cusip]["override"] = ticker
        n_fixed += 1
    for cusip in todo:  # don't re-query known misses on every run
        if rows[cusip]["method"] == "unmapped":
            rows[cusip]["method"] = "no_us_listing"
    figi.save_cache(figi_cache)
    save_sectors(rows)
    print(f"sectors: US-listing retry fixed {n_fixed}/{len(todo)}")
    return n_fixed


def apply_manual_overrides(rows: dict[str, dict], figi_cache: dict[str, dict],
                           today: str) -> int:
    """data/ref/sector_overrides.csv: hand-resolved cusip -> CIK for issuers
    OpenFIGI cannot map (foreign-domiciled CINS). The SIC/sector still comes
    from EDGAR, and each row's expect_name is checked against the EDGAR
    entity name so a mistyped CIK fails loudly instead of misclassifying."""
    path = REF / "sector_overrides.csv"
    if not path.exists():
        return 0
    n = 0
    with open(path, newline="", encoding="utf-8") as fh:
        for ov in csv.DictReader(fh):
            cusip, cik = ov["cusip"], int(ov["cik"])
            url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
            data = load_json(fetch_cached(url, RAW / "sectors" / f"CIK{cik:010d}.json"))
            name = (data.get("name") or "").upper()
            if ov["expect_name"].upper() not in name:
                raise SystemExit(
                    f"sector_overrides.csv: CIK {cik} resolves to {name!r}, "
                    f"expected it to contain {ov['expect_name']!r} ({cusip})")
            sic = str(data.get("sic") or "")
            rows.setdefault(cusip, {"cusip": cusip})
            rows[cusip].update(
                ticker=ov["ticker"], cik=str(cik), sic=sic,
                sic_desc=data.get("sicDescription") or "",
                sector=sic_to_sector(int(sic)) if sic.isdigit() else "Unclassified",
                method="manual_cik", retrieved=today)
            if cusip in figi_cache and \
                    figi.effective_ticker(figi_cache[cusip]) != ov["ticker"]:
                figi_cache[cusip]["override"] = ov["ticker"]
                n += 1
    figi.save_cache(figi_cache)
    save_sectors(rows)
    return n


def refresh() -> dict[str, dict]:
    """Classify every CUSIP in the ticker cache; keep existing rows as cache."""
    today = dt.date.today().isoformat()
    figi_cache = figi.load_cache()
    rows = load_sectors()
    missing = [c for c in figi_cache if c not in rows]
    cik_map = load_ticker_cik_map()
    if not missing:
        print(f"sectors.csv rows up to date ({len(rows)} rows)")
        repair_unmapped(rows, figi_cache, cik_map, today)
        apply_manual_overrides(rows, figi_cache, today)
        return rows
    print(f"sectors: classifying {len(missing)} CUSIPs "
          f"({len(rows)} already cached)")
    for i, cusip in enumerate(sorted(missing), 1):
        rows[cusip] = classify_cusip(cusip, figi_cache[cusip], cik_map, today)
        if i % 100 == 0 or i == len(missing):
            save_sectors(rows)  # checkpoint; reruns resume from the file
            print(f"  sectors progress: {i}/{len(missing)}")
    save_sectors(rows)
    repair_unmapped(rows, figi_cache, cik_map, today)
    apply_manual_overrides(rows, figi_cache, today)
    from collections import Counter
    print(Counter(r["sector"] for r in rows.values()).most_common())
    return rows


if __name__ == "__main__":
    refresh()
