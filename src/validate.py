"""Holdings validation: field integrity, CUSIP checks, identity + QoQ sanity.

Two severities, written to data/out/validation.csv every run:
  ERROR  the row cannot be trusted (malformed CUSIP, unparseable value/shares,
         unknown share type) — blocks publication of that manager-quarter and
         fails the run, mirroring the LATE/ERROR filer-status gate.
  WARN   suspicious but present in real accepted filings — recorded for review,
         never blocks. Calibrated against the committed 2024Q2-2026Q2 history
         (2026-08-17): CUSIP check-digit failures occur in accepted filings
         (e.g. 78462F953 SPDR institutional series), issuer renames are routine
         (CHESAPEAKE -> EXPAND), BRK-A prices ~ $750k/share, splits move implied
         prices 10x — thresholds sit just outside all of that.

Checks:
  cusip-format        not 9 alphanumeric chars                          ERROR
  cusip-check-digit   ISO 6166 modulus-10 double-add-double mismatch    WARN
  field               issuer empty / shares-value unparseable-negative  ERROR
  share-type          sh_prn_type not SH/PRN, put_call unknown          ERROR
  price-bounds        implied $/share outside [0.001, 2,000,000]        WARN
  ticker-format       cached ticker with characters outside the
                      observed FIGI vocabulary                          WARN
  identity            one CUSIP, issuer names disagreeing in their
                      first 4 normalized chars (catches cross-labels
                      like 023135106 AMAZON vs ASTERA LABS)             WARN
  qoq-shares          continuing position share count moved >100x       WARN
  qoq-price           continuing position implied price moved >10x      WARN
"""
from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, fields
from pathlib import Path

from common import OUT
from edgar import ParsedFiling

VALIDATION_PATH = OUT / "validation.csv"

PRICE_MIN, PRICE_MAX = 0.001, 2_000_000
QOQ_SHARE_RATIO = 100
QOQ_PRICE_RATIO = 10

_CUSIP_RE = re.compile(r"[0-9A-Z]{9}")
# FIGI tickers include bond descriptors ("WDC 3 11/15/28") and when-issued
# markers ("MASI*") — both present in the committed cache, both legitimate.
_TICKER_RE = re.compile(r"[A-Za-z0-9./\-* ]{1,24}")


@dataclass
class Finding:
    level: str      # ERROR / WARN
    check: str
    quarter: str
    manager: str
    filer_cik: str
    accession: str
    cusip: str
    detail: str


def _warn(f: Finding) -> None:
    print(f"!! VALIDATION {f.level} [{f.manager} {f.quarter} {f.cusip}] "
          f"{f.check}: {f.detail}", file=sys.stderr)


def cusip_check_digit(cusip: str) -> str | None:
    """ISO 6166 check digit for the first 8 chars; None if uncomputable."""
    total = 0
    for i, ch in enumerate(cusip[:8]):
        if ch.isdigit():
            v = int(ch)
        elif "A" <= ch <= "Z":
            v = ord(ch) - 55
        elif ch == "*":
            v = 36
        elif ch == "@":
            v = 37
        elif ch == "#":
            v = 38
        else:
            return None
        if i % 2 == 1:
            v *= 2
        total += v // 10 + v % 10
    return str((10 - total % 10) % 10)


def _norm_issuer(name: str) -> str:
    return re.sub(r"[^A-Z0-9 ]", "", (name or "").upper()).strip()


def validate_rows(manager: str, qkey: str,
                  merged_by_cik: dict[int, list[ParsedFiling]]) -> list[Finding]:
    """Row-integrity checks on a manager-quarter about to be published.
    Returned ERROR findings must withhold the CSV; WARNs are recorded only."""
    findings: list[Finding] = []

    def add(level: str, check: str, cik: int, acc: str, cusip: str, detail: str):
        f = Finding(level, check, qkey, manager, str(cik), acc, cusip, detail)
        findings.append(f)
        _warn(f)

    for cik, plist in merged_by_cik.items():
        for p in plist:
            acc = p.filing.accession
            for row in p.rows:
                cusip = row["cusip"]
                if not _CUSIP_RE.fullmatch(cusip):
                    add("ERROR", "cusip-format", cik, acc, cusip,
                        f"not 9 alphanumeric chars (issuer {row['issuer']!r})")
                else:
                    expect = cusip_check_digit(cusip)
                    if expect != cusip[8]:
                        add("WARN", "cusip-check-digit", cik, acc, cusip,
                            f"check digit {cusip[8]} != computed {expect} "
                            f"(issuer {row['issuer']!r})")
                if not (row["issuer"] or "").strip():
                    add("ERROR", "field", cik, acc, cusip, "empty issuer name")
                try:
                    value = float(row["value_usd"])
                    shares = float(row["shares"])
                except (TypeError, ValueError):
                    add("ERROR", "field", cik, acc, cusip,
                        f"unparseable value/shares "
                        f"({row['value_usd']!r}/{row['shares']!r})")
                    continue
                if value < 0 or shares < 0:
                    add("ERROR", "field", cik, acc, cusip,
                        f"negative value/shares ({value}/{shares})")
                    continue
                if row["sh_prn_type"] not in ("SH", "PRN"):
                    add("ERROR", "share-type", cik, acc, cusip,
                        f"sh_prn_type {row['sh_prn_type']!r} not SH/PRN")
                if (row["put_call"] or "").capitalize() not in ("", "Put", "Call"):
                    add("ERROR", "share-type", cik, acc, cusip,
                        f"put_call {row['put_call']!r} unknown")
                if (row["sh_prn_type"] == "SH" and not row["put_call"]
                        and shares > 0):
                    price = value / shares
                    if not PRICE_MIN <= price <= PRICE_MAX:
                        add("WARN", "price-bounds", cik, acc, cusip,
                            f"implied ${price:,.4f}/share (value {value:,.0f}, "
                            f"shares {shares:,.0f}, issuer {row['issuer']!r})")
    return findings


def validate_identity(merged_all: dict[tuple[int, str], list[ParsedFiling]],
                      ) -> list[Finding]:
    """One CUSIP should be one issuer. Name variants are routine, so only flag
    when the normalized names disagree in their first 4 chars — the level of
    the observed Amazon/Astera Labs cross-label, not TSMC spelling drift."""
    names: dict[str, set[str]] = defaultdict(set)
    where: dict[str, list[str]] = defaultdict(list)
    for (cik, qkey), plist in merged_all.items():
        for p in plist:
            for row in p.rows:
                n = _norm_issuer(row["issuer"])
                if n and n not in names[row["cusip"]]:
                    names[row["cusip"]].add(n)
                    where[row["cusip"]].append(
                        f"{n!r} ({cik} {qkey} {p.filing.accession})")
    findings = []
    for cusip, variants in sorted(names.items()):
        if len({v[:4] for v in variants}) > 1:
            f = Finding("WARN", "identity", "", "", "", "", cusip,
                        "issuer names disagree: " + "; ".join(sorted(where[cusip])))
            findings.append(f)
            _warn(f)
    return findings


def validate_tickers(tickers: dict[str, str]) -> list[Finding]:
    findings = []
    for cusip, ticker in sorted(tickers.items()):
        if ticker and not _TICKER_RE.fullmatch(ticker):
            f = Finding("WARN", "ticker-format", "", "", "", "", cusip,
                        f"unexpected ticker {ticker!r} in cusip_ticker cache")
            findings.append(f)
            _warn(f)
    return findings


def _main_book(path: Path) -> dict[str, tuple[int, int]]:
    book: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["sh_prn_type"] != "SH" or row["put_call"]:
                continue
            book[row["cusip"]][0] += int(float(row["shares"] or 0))
            book[row["cusip"]][1] += int(float(row["value_usd"] or 0))
    return {c: (s, v) for c, (s, v) in book.items()}


def validate_qoq(holdings_dir: Path) -> list[Finding]:
    """Extreme quarter-over-quarter movements across all committed holdings
    CSVs on disk (units errors and CUSIP swaps look like impossible jumps)."""
    findings = []
    for mgr_dir in sorted(holdings_dir.iterdir()):
        if not mgr_dir.is_dir():
            continue
        quarters = sorted(p.stem for p in mgr_dir.glob("*.csv"))
        for prev_q, cur_q in zip(quarters, quarters[1:]):
            prev = _main_book(mgr_dir / f"{prev_q}.csv")
            cur = _main_book(mgr_dir / f"{cur_q}.csv")
            for cusip in sorted(set(prev) & set(cur)):
                (ps, pv), (cs, cv) = prev[cusip], cur[cusip]
                if not (ps and cs):
                    continue
                ratio = cs / ps
                if ratio > QOQ_SHARE_RATIO or ratio < 1 / QOQ_SHARE_RATIO:
                    f = Finding("WARN", "qoq-shares", cur_q, mgr_dir.name,
                                "", "", cusip,
                                f"shares {ps:,} -> {cs:,} ({ratio:,.1f}x) "
                                f"vs {prev_q}")
                    findings.append(f)
                    _warn(f)
                if pv and cv:
                    pratio = (cv / cs) / (pv / ps)
                    if pratio > QOQ_PRICE_RATIO or pratio < 1 / QOQ_PRICE_RATIO:
                        f = Finding("WARN", "qoq-price", cur_q, mgr_dir.name,
                                    "", "", cusip,
                                    f"implied price ${pv / ps:,.2f} -> "
                                    f"${cv / cs:,.2f} vs {prev_q} "
                                    f"(split or units error?)")
                        findings.append(f)
                        _warn(f)
    return findings


def write_validation_csv(findings: list[Finding]) -> str:
    OUT.mkdir(parents=True, exist_ok=True)
    cols = [f.name for f in fields(Finding)]
    ordered = sorted(findings, key=lambda f: (f.level != "ERROR", f.check,
                                              f.quarter, f.manager, f.cusip))
    with open(VALIDATION_PATH, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for f in ordered:
            w.writerow([getattr(f, c) for c in cols])
    return str(VALIDATION_PATH)
