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
from collections import Counter
from dataclasses import dataclass

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


def us_ticker_lookup(cusips: list[str]) -> dict[str, str]:
    """Re-query OpenFIGI pinned to US listings for CUSIPs whose cached best
    match was a foreign listing (or none). Returns cusip -> US ticker."""
    out: dict[str, str] = {}
    for results in figi.map_batch(cusips, exch_code="US"):
        for cusip, result in results:
            ticker = figi.best_match(result).get("ticker")
            if ticker:
                out[cusip] = ticker
    return out


@dataclass
class SectorRefresh:
    """One pass over sectors.csv, holding the state every step shares: the
    sector rows being built, the OpenFIGI ticker cache they classify (and may
    gain overrides), the EDGAR ticker->CIK map, and the retrieval date stamped
    on every row written this pass."""

    rows: dict[str, dict]
    figi_cache: dict[str, dict]
    cik_map: dict[str, int]
    today: str

    @classmethod
    def load(cls) -> SectorRefresh:
        return cls(rows=load_sectors(), figi_cache=figi.load_cache(),
                   cik_map=load_ticker_cik_map(),
                   today=dt.date.today().isoformat())

    def save(self) -> None:
        figi.save_cache(self.figi_cache)
        save_sectors(self.rows)

    def classify_cusip(self, cusip: str) -> dict:
        figi_entry = self.figi_cache[cusip]
        ticker = figi.effective_ticker(figi_entry)
        sec_type = figi_entry.get("security_type", "")
        row = {"cusip": cusip, "ticker": ticker, "cik": "", "sic": "",
               "sic_desc": "", "sector": "Unclassified", "method": "unmapped",
               "retrieved": self.today}
        if sec_type in FUND_TYPES:
            row.update(sector="Funds & ETFs", method="figi_type")
            return row
        cik = self.cik_map.get(normalize_ticker(ticker)) if ticker else None
        if cik:
            sic, sic_desc = fetch_sic(cik)
            row.update(cik=str(cik), sic=sic, sic_desc=sic_desc,
                       method="sec_sic")
            if sic.isdigit():
                row["sector"] = sic_to_sector(int(sic))
        return row

    def classify_missing(self) -> int:
        """First pass: classify every cached CUSIP with no sectors.csv row."""
        missing = [c for c in self.figi_cache if c not in self.rows]
        if not missing:
            print(f"sectors.csv rows up to date ({len(self.rows)} rows)")
            return 0
        print(f"sectors: classifying {len(missing)} CUSIPs "
              f"({len(self.rows)} already cached)")
        for i, cusip in enumerate(sorted(missing), 1):
            self.rows[cusip] = self.classify_cusip(cusip)
            if i % 100 == 0 or i == len(missing):
                save_sectors(self.rows)  # checkpoint; reruns resume from the file
                print(f"  sectors progress: {i}/{len(missing)}")
        save_sectors(self.rows)
        return len(missing)

    def repair_unmapped(self) -> int:
        """Second pass over method=unmapped rows via the US-listing lookup.
        Winning tickers are also written to the cusip_ticker.csv override
        column, so the committed holdings CSVs pick them up on the next
        pipeline run."""
        todo = sorted(c for c, r in self.rows.items()
                      if r["method"] == "unmapped")
        if not todo:
            return 0
        print(f"sectors: retrying {len(todo)} unmapped CUSIPs against US listings "
              f"(~{len(todo) / figi.JOBS_PER_REQUEST * figi.REQUEST_INTERVAL_S / 60:.0f} min)")
        found = us_ticker_lookup(todo)
        n_fixed = 0
        for cusip, ticker in found.items():
            cik = self.cik_map.get(normalize_ticker(ticker))
            if not cik:
                continue
            sic, sic_desc = fetch_sic(cik)
            self.rows[cusip].update(ticker=ticker, cik=str(cik), sic=sic,
                                    sic_desc=sic_desc, method="sec_sic_usfigi",
                                    retrieved=self.today)
            if sic.isdigit():
                self.rows[cusip]["sector"] = sic_to_sector(int(sic))
            if figi.effective_ticker(self.figi_cache[cusip]) != ticker:
                self.figi_cache[cusip]["override"] = ticker
            n_fixed += 1
        for cusip in todo:  # don't re-query known misses on every run
            if self.rows[cusip]["method"] == "unmapped":
                self.rows[cusip]["method"] = "no_us_listing"
        self.save()
        print(f"sectors: US-listing retry fixed {n_fixed}/{len(todo)}")
        return n_fixed

    def apply_manual_overrides(self) -> int:
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
                data = load_json(
                    fetch_cached(url, RAW / "sectors" / f"CIK{cik:010d}.json"))
                name = (data.get("name") or "").upper()
                if ov["expect_name"].upper() not in name:
                    raise SystemExit(
                        f"sector_overrides.csv: CIK {cik} resolves to {name!r}, "
                        f"expected it to contain {ov['expect_name']!r} ({cusip})")
                sic = str(data.get("sic") or "")
                self.rows.setdefault(cusip, {"cusip": cusip})
                self.rows[cusip].update(
                    ticker=ov["ticker"], cik=str(cik), sic=sic,
                    sic_desc=data.get("sicDescription") or "",
                    sector=sic_to_sector(int(sic)) if sic.isdigit() else "Unclassified",
                    method="manual_cik", retrieved=self.today)
                if cusip in self.figi_cache and \
                        figi.effective_ticker(self.figi_cache[cusip]) != ov["ticker"]:
                    self.figi_cache[cusip]["override"] = ov["ticker"]
                    n += 1
        self.save()
        return n


def refresh() -> dict[str, dict]:
    """Classify every CUSIP in the ticker cache; keep existing rows as cache."""
    refresh_pass = SectorRefresh.load()
    n_classified = refresh_pass.classify_missing()
    refresh_pass.repair_unmapped()
    refresh_pass.apply_manual_overrides()
    if n_classified:
        print(Counter(r["sector"] for r in refresh_pass.rows.values()).most_common())
    return refresh_pass.rows


if __name__ == "__main__":
    refresh()
