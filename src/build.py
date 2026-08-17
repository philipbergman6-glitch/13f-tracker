"""Amendment merge to quarter-final holdings and emission of committed CSVs.

Quarter-final holdings (CONTEXT.md): latest RESTATEMENT (or the original 13F-HR if
none) plus all subsequent NEW HOLDINGS amendments in order.

Semantics confirmed against Form 13F Special Instruction 3
(https://www.sec.gov/files/form13f.pdf, pp. 4-5, retrieved 2026-08-12): an amendment
"must either restate the Form 13F report in its entirety or include only holdings
entries that are being reported in addition to those already reported".

Non-conforming amendment chains and cross-filer duplicate books are flagged loudly:
printed to stderr AND written to data/out/flags.csv - never silently merged.
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict

from common import HOLDINGS, OUT, manager_slug
from edgar import ParsedFiling, filing_index_url

HOLDINGS_COLUMNS = [
    "filer_cik", "accession", "cusip", "ticker", "issuer", "class", "put_call",
    "value_usd", "shares", "sh_prn_type", "discretion", "other_manager",
    "vote_sole", "vote_shared", "vote_none",
]

_flags: list[dict] = []

# Every fetched 13F-HR gets an explicit merge decision (kept in / excluded from
# the quarter-final book, and why) so the release evidence package can explain
# each book's composition without re-running the merge. Written per run to
# data/out/merge_decisions.csv; dedupe_filers appends DUPLICATE_BOOK rows,
# which supersede the per-filer merge role for the same accession.
IN_BOOK_ROLES = {"BASE_ORIGINAL", "BASE_RESTATEMENT", "NEW_HOLDINGS"}

_merge_decisions: list[dict] = []


def flag(cik: int, qkey: str, accession: str, problem: str) -> None:
    print(f"!! AMENDMENT FLAG [{cik} {qkey} {accession}]: {problem}", file=sys.stderr)
    _flags.append({"filer_cik": cik, "quarter": qkey, "accession": accession,
                   "problem": problem})


def _decide(cik: int, qkey: str, p: ParsedFiling, role: str, detail: str) -> None:
    _merge_decisions.append({
        "filer_cik": cik, "quarter": qkey, "accession": p.filing.accession,
        "form": p.filing.form, "filing_date": p.filing.filing_date,
        "role": role, "in_book": role in IN_BOOK_ROLES, "detail": detail,
    })


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
            for p in parsed:
                _decide(cik, qkey, p, "EXCLUDED_NO_BASE",
                        "no original 13F-HR and no RESTATEMENT; quarter has no "
                        "base filing")
            return []

    adds = [a for a in amendments
            if a.amendment_type == "NEW HOLDINGS" and (a.amendment_no or 0) > cutoff]

    for p in parsed:
        if p is base:
            role = "BASE_RESTATEMENT" if p.is_amendment else "BASE_ORIGINAL"
            detail = ("latest RESTATEMENT restates the quarter in its entirety"
                      if p.is_amendment else "original 13F-HR is the base filing")
        elif p in adds:
            role = "NEW_HOLDINGS"
            detail = (f"NEW HOLDINGS amendment {p.amendment_no} appended after "
                      f"the base filing (Form 13F Special Instruction 3)")
        elif not p.is_amendment:
            role = "SUPERSEDED_ORIGINAL"
            detail = ("replaced by a later RESTATEMENT amendment" if restatements
                      else "duplicate original 13F-HR; latest-filed used as base")
        elif p.amendment_type == "RESTATEMENT":
            role = "SUPERSEDED_RESTATEMENT"
            detail = "a later RESTATEMENT is the quarter-final base"
        elif p.amendment_type == "NEW HOLDINGS":
            role = "PRE_RESTATEMENT_AMENDMENT"
            detail = (f"NEW HOLDINGS amendment {p.amendment_no} predates the "
                      f"base RESTATEMENT, whose full restatement subsumes it")
        else:
            role = "EXCLUDED_UNKNOWN_TYPE"
            detail = (f"amendmentType={p.amendment_type!r} is neither "
                      f"RESTATEMENT nor NEW HOLDINGS; excluded (see flags.csv)")
        _decide(cik, qkey, p, role, detail)

    return [base] + adds


_SIGNATURE_FIELDS = ("cusip", "class", "put_call", "sh_prn_type", "shares", "value_usd")


def _book_signature(plist: list[ParsedFiling]) -> tuple:
    """Order-independent fingerprint of a filer's economic book.

    Administrative columns (voting authority, discretion, other_manager) are
    excluded: duplicate sibling filings fill them inconsistently (Situational
    Awareness 2026Q1 differs only in vote_none on 5 option rows), while an
    identical CUSIP+shares+value multiset is still one book reported twice.
    """
    return tuple(sorted(tuple(row[f] for f in _SIGNATURE_FIELDS)
                        for p in plist for row in p.rows))


def dedupe_filers(manager: str, qkey: str,
                  merged_by_cik: dict[int, list[ParsedFiling]],
                  ) -> tuple[dict[int, list[ParsedFiling]], dict[int, str]]:
    """Drop filers whose position book is identical to an earlier-listed filer's.

    Two filers of one manager reporting the same rows share-for-share is one book
    reported twice (e.g. Situational Awareness LP / Partners LP, 2026Q1); summing
    them would double the manager. Precedence = manager_map row order.

    Returns (kept, dropped) where dropped maps each excluded CIK to a comparison
    record (kept filer's CIK + accession, row count) that the caller persists in
    the committed filer-status table; drops are also flagged to flags.csv.
    """
    kept: dict[int, list[ParsedFiling]] = {}
    sigs: dict[tuple, tuple[int, str]] = {}
    dropped: dict[int, str] = {}
    for cik, plist in merged_by_cik.items():
        sig = _book_signature(plist)
        if sig and sig in sigs:
            kept_cik, kept_acc = sigs[sig]
            detail = (f"book identical to filer {kept_cik} acc {kept_acc} "
                      f"({len(sig)} rows, CUSIP+class+put/call+type+shares+value "
                      f"multiset match); excluded to avoid double-counting {manager}")
            flag(cik, qkey, plist[0].filing.accession, f"{manager}: {detail}")
            for p in plist:
                _decide(cik, qkey, p, "DUPLICATE_BOOK", f"{manager}: {detail}")
            dropped[cik] = detail
            continue
        sigs[sig] = (cik, "+".join(p.filing.accession for p in plist))
        kept[cik] = plist
    return kept, dropped


def write_manager_quarter(manager: str, qkey: str,
                          merged_by_cik: dict[int, list[ParsedFiling]],
                          tickers: dict[str, str]) -> str:
    """Write data/holdings/<manager-slug>/<qkey>.csv (all filers of the manager).

    Callers pass already-deduped filers (dedupe_filers) so exclusions are
    recorded in the filer-status table before anything is written.
    """
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
    with open(OUT / "flags.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["filer_cik", "quarter", "accession", "problem"])
        w.writeheader()
        w.writerows(_flags)


MERGE_DECISION_COLUMNS = ["filer_cik", "quarter", "accession", "form",
                          "filing_date", "role", "in_book", "detail"]


def write_merge_decisions() -> None:
    """data/out/merge_decisions.csv: every fetched 13F-HR's role in (or
    exclusion from) its quarter-final book, in decision order. A later
    DUPLICATE_BOOK row supersedes an earlier per-filer merge role."""
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "merge_decisions.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=MERGE_DECISION_COLUMNS)
        w.writeheader()
        w.writerows(_merge_decisions)


def write_rowcount_verification(parsed_all: list[ParsedFiling]) -> tuple[int, int, int]:
    """data/out/verification_rowcounts.csv: parsed row count and summed value
    vs the cover page's tableEntryTotal / tableValueTotal for every fetched
    filing, with its EDGAR index URL. Returns (n_rows_match, n_rows_mismatch,
    n_value_mismatch); mismatches are filer-side cover-page errors unless a
    parse bug is at fault — each must be explained in
    data/ref/known_exceptions.csv before an evidence package can be built."""
    OUT.mkdir(parents=True, exist_ok=True)
    n_match = n_mismatch = n_value_mismatch = 0
    with open(OUT / "verification_rowcounts.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["filer_cik", "accession", "form", "filing_date", "report_date",
                    "rows_parsed", "table_entry_total", "rows_match",
                    "value_parsed_usd", "table_value_total", "value_match",
                    "filing_url"])
        for p in parsed_all:
            rows_match = (p.table_entry_total is not None
                          and len(p.rows) == p.table_entry_total)
            value_parsed = sum(int(float(r["value_usd"] or 0)) for r in p.rows)
            value_match = (p.table_value_total is not None
                           and value_parsed == p.table_value_total)
            n_match += rows_match
            n_mismatch += not rows_match
            n_value_mismatch += not value_match
            w.writerow([p.filing.cik, p.filing.accession, p.filing.form,
                        p.filing.filing_date, p.filing.report_date,
                        len(p.rows), p.table_entry_total, rows_match,
                        value_parsed, p.table_value_total, value_match,
                        filing_index_url(p.filing.cik, p.filing.accession)])
    return n_match, n_mismatch, n_value_mismatch
