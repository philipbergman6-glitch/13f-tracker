"""Amendment merge to quarter-final holdings and emission of committed CSVs.

Quarter-final holdings (CONTEXT.md): latest RESTATEMENT (or the original 13F-HR if
none) plus all subsequent NEW HOLDINGS amendments in order.

Semantics confirmed against Form 13F Special Instruction 3
(https://www.sec.gov/files/form13f.pdf, pp. 4-5, retrieved 2026-08-12): an amendment
"must either restate the Form 13F report in its entirety or include only holdings
entries that are being reported in addition to those already reported".

Non-conforming amendment chains are flagged loudly: printed to stderr AND written to
data/out/amendment_flags.csv - never silently merged.
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict

from common import HOLDINGS, OUT, manager_slug
from edgar import ParsedFiling

HOLDINGS_COLUMNS = [
    "filer_cik", "accession", "cusip", "ticker", "issuer", "class", "put_call",
    "value_usd", "shares", "sh_prn_type", "discretion", "other_manager",
    "vote_sole", "vote_shared", "vote_none",
]

_flags: list[dict] = []


def flag(cik: int, qkey: str, accession: str, problem: str) -> None:
    print(f"!! AMENDMENT FLAG [{cik} {qkey} {accession}]: {problem}", file=sys.stderr)
    _flags.append({"filer_cik": cik, "quarter": qkey, "accession": accession,
                   "problem": problem})


def merge_quarter(cik: int, qkey: str, parsed: list[ParsedFiling]) -> list[ParsedFiling]:
    """Pick the filings whose rows make up quarter-final holdings, in merge order."""
    originals = [p for p in parsed if not p.is_amendment]
    amendments = sorted(
        (p for p in parsed if p.is_amendment),
        key=lambda p: (p.amendment_no or 0, p.filing.filing_date),
    )

    if len(originals) > 1:
        flag(cik, qkey, originals[-1].filing.accession,
             f"{len(originals)} original 13F-HRs for one quarter; using latest-filed")
    base = max(originals, key=lambda p: p.filing.filing_date) if originals else None

    restatements = [a for a in amendments if a.amendment_type == "RESTATEMENT"]
    for a in amendments:
        if a.amendment_type not in ("RESTATEMENT", "NEW HOLDINGS"):
            flag(cik, qkey, a.filing.accession,
                 f"amendment with missing/unknown amendmentType={a.amendment_type!r}; excluded")

    if restatements:
        base = restatements[-1]
        cutoff = base.amendment_no or 0
    else:
        cutoff = 0
        if base is None:
            flag(cik, qkey, amendments[0].filing.accession if amendments else "-",
                 "no original 13F-HR and no RESTATEMENT; quarter has no base filing")
            return []

    adds = [a for a in amendments
            if a.amendment_type == "NEW HOLDINGS" and (a.amendment_no or 0) > cutoff]
    return [base] + adds


def write_manager_quarter(manager: str, qkey: str,
                          merged_by_cik: dict[int, list[ParsedFiling]],
                          tickers: dict[str, str]) -> str:
    """Write data/holdings/<manager-slug>/<qkey>.csv (all filers of the manager)."""
    out_dir = HOLDINGS / manager_slug(manager)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{qkey}.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=HOLDINGS_COLUMNS)
        w.writeheader()
        for cik in sorted(merged_by_cik):
            for p in merged_by_cik[cik]:
                for row in p.rows:
                    w.writerow({
                        "filer_cik": cik,
                        "accession": p.filing.accession,
                        "ticker": tickers.get(row["cusip"], ""),
                        **row,
                    })
    return str(out_path)


def write_flags() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "amendment_flags.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["filer_cik", "quarter", "accession", "problem"])
        w.writeheader()
        w.writerows(_flags)


def write_rowcount_verification(parsed_all: list[ParsedFiling]) -> tuple[int, int]:
    """data/out/verification_rowcounts.csv: parsed row count vs cover-page
    tableEntryTotal for every fetched filing. Returns (n_match, n_mismatch)."""
    OUT.mkdir(parents=True, exist_ok=True)
    n_match = n_mismatch = 0
    with open(OUT / "verification_rowcounts.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["filer_cik", "accession", "form", "report_date",
                    "rows_parsed", "table_entry_total", "match"])
        for p in parsed_all:
            match = p.table_entry_total is not None and len(p.rows) == p.table_entry_total
            n_match += match
            n_mismatch += not match
            w.writerow([p.filing.cik, p.filing.accession, p.filing.form,
                        p.filing.report_date, len(p.rows), p.table_entry_total, match])
    return n_match, n_mismatch
