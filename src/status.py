"""Per-filer quarterly status model: every (manager, filer, quarter) in scope gets
an explicit outcome, so a filer's absence is never silent and every exclusion has a
permanent record.

Statuses:
  HOLDINGS   filer's rows are in the committed manager-quarter CSV
  NT         13F-NT filed for the quarter: holdings reported in another filer's report
  DUPLICATE  13F-HR filed but excluded as a verified duplicate of a sibling filer's book
  NOT_DUE    nothing filed and the statutory deadline has not passed
  LATE       nothing filed and the deadline has passed - blocks publication
  ERROR      filings exist but fetch/parse/merge failed - blocks publication

Statuses are written to data/holdings/filer_status.csv (committed, so decisions
persist in git history rather than the gitignored data/out scratch).

Deadline rule (Rule 13f-1(a)(1)): 45 days after calendar quarter end, rolled to the
next Monday when it lands on a weekend. Federal holidays are not modelled; the only
effect is a filer being called LATE a business day early - a loud false alarm, never
a silent gap.
"""
from __future__ import annotations

import csv
import datetime
from dataclasses import dataclass, fields

from common import HOLDINGS, FilerSpan, quarter_end_date
from edgar import Filing, ParsedFiling

BLOCKING = {"LATE", "ERROR"}

STATUS_PATH = HOLDINGS / "filer_status.csv"


@dataclass
class FilerStatus:
    quarter: str
    manager: str
    filer_cik: int
    filer_name: str
    status: str          # HOLDINGS / NT / DUPLICATE / NOT_DUE / LATE / ERROR
    form: str            # form(s) behind the status, "" when nothing filed
    accession: str       # accession(s) behind the status, "+"-joined, "" if none
    filing_date: str     # latest relevant filing date, "" if none
    detail: str          # human-readable reason / comparison result


def filing_deadline(qkey: str) -> datetime.date:
    """45 days after quarter end, weekend rolled forward to Monday."""
    qend = datetime.date.fromisoformat(quarter_end_date(qkey))
    deadline = qend + datetime.timedelta(days=45)
    if deadline.weekday() >= 5:
        deadline += datetime.timedelta(days=7 - deadline.weekday())
    return deadline


def classify(span: FilerSpan, qkey: str, *,
             merged: list[ParsedFiling],
             hr_filings: list[ParsedFiling],
             nt_filings: list[Filing],
             fetch_errors: list[str],
             duplicate_detail: str | None,
             today: datetime.date) -> FilerStatus:
    """Explicit status for one (filer, quarter). Exactly one branch applies:

    merged rows kept -> HOLDINGS; dropped as duplicate -> DUPLICATE; 13F-HR present
    but unusable -> ERROR; fetch/parse failed -> ERROR; 13F-NT -> NT; otherwise
    NOT_DUE or LATE by the statutory deadline.
    """
    base = dict(quarter=qkey, manager=span.manager, filer_cik=span.cik,
                filer_name=span.filer_name)
    if duplicate_detail is not None:
        p = merged[0] if merged else hr_filings[0]
        return FilerStatus(**base, status="DUPLICATE", form=p.filing.form,
                           accession="+".join(m.filing.accession for m in merged),
                           filing_date=max(m.filing.filing_date for m in merged),
                           detail=duplicate_detail)
    if merged:
        n_rows = sum(len(p.rows) for p in merged)
        return FilerStatus(**base, status="HOLDINGS", form=merged[0].filing.form,
                           accession="+".join(p.filing.accession for p in merged),
                           filing_date=max(p.filing.filing_date for p in merged),
                           detail=f"{n_rows} rows from {len(merged)} filing(s)")
    if hr_filings:
        return FilerStatus(**base, status="ERROR", form=hr_filings[0].filing.form,
                           accession="+".join(p.filing.accession for p in hr_filings),
                           filing_date=max(p.filing.filing_date for p in hr_filings),
                           detail="13F-HR present but no usable base filing "
                                  "(see data/out/flags.csv)")
    if fetch_errors:
        return FilerStatus(**base, status="ERROR", form="", accession="",
                           filing_date="", detail="; ".join(fetch_errors))
    if nt_filings:
        latest = max(nt_filings, key=lambda f: f.filing_date)
        return FilerStatus(**base, status="NT", form=latest.form,
                           accession=latest.accession, filing_date=latest.filing_date,
                           detail="holdings reported in another filer's 13F "
                                  "(13F Notice)")
    deadline = filing_deadline(qkey)
    if today <= deadline:
        return FilerStatus(**base, status="NOT_DUE", form="", accession="",
                           filing_date="", detail=f"deadline {deadline.isoformat()}")
    return FilerStatus(**base, status="LATE", form="", accession="", filing_date="",
                       detail=f"no 13F-HR or 13F-NT as of {today.isoformat()} "
                              f"(deadline was {deadline.isoformat()})")


def write_status_csv(statuses: list[FilerStatus]) -> str:
    HOLDINGS.mkdir(parents=True, exist_ok=True)
    cols = [f.name for f in fields(FilerStatus)]
    ordered = sorted(statuses, key=lambda s: (s.quarter, s.manager, s.filer_cik))
    with open(STATUS_PATH, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for s in ordered:
            w.writerow([getattr(s, c) for c in cols])
    return str(STATUS_PATH)
