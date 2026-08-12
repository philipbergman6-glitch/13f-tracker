"""13F pipeline entry point: fetch -> parse -> amendment-merge -> tickers -> CSVs.

Usage:
    python src/pipeline.py --start 2024Q2 --end 2026Q2 [--skip-figi]

Re-runnable: raw EDGAR responses are cached in data/raw/, the OpenFIGI cache in
data/ref/cusip_ticker.csv; committed holdings CSVs are rewritten each run.
Note on units: since Jan 2023 the 13F 'value' column is whole dollars (previously
$thousands); every quarter this pipeline covers is whole-dollar.
"""
from __future__ import annotations

import argparse
import datetime as dt
from collections import defaultdict

import build
import changes
import figi
from common import load_manager_map, quarter_end_date, quarter_range
from edgar import fetch_filing_docs, list_13f_filings, parse_filing


def report_date_to_qkey(rdate: str) -> str:
    year, month = int(rdate[:4]), int(rdate[5:7])
    return f"{year}Q{(month + 2) // 3}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2024Q2")
    ap.add_argument("--end", default="2026Q2")
    ap.add_argument("--skip-figi", action="store_true",
                    help="leave ticker column empty / cache-only")
    args = ap.parse_args()

    window = quarter_range(args.start, args.end)
    earliest = quarter_end_date(args.start)
    spans = load_manager_map()

    # 1) fetch + parse everything, grouped (cik, qkey) -> parsed filings
    parsed_all = []
    by_cik_quarter: dict[tuple[int, str], list] = defaultdict(list)
    for span in spans:
        filings = list_13f_filings(span.cik, earliest)
        print(f"{span.manager} / {span.filer_name} (CIK {span.cik}): "
              f"{len(filings)} 13F filings since {earliest}")
        for f in filings:
            qkey = report_date_to_qkey(f.report_date)
            if qkey not in window or not span.covers(qkey):
                continue
            cover, infotable = fetch_filing_docs(f)
            p = parse_filing(f, cover, infotable)
            parsed_all.append(p)
            by_cik_quarter[(span.cik, qkey)].append(p)

    # 2) amendment merge -> quarter-final filings per (cik, quarter)
    merged: dict[tuple[int, str], list] = {}
    for (cik, qkey), plist in sorted(by_cik_quarter.items()):
        merged[(cik, qkey)] = build.merge_quarter(cik, qkey, plist)

    # 3) CUSIP -> ticker
    cusips = {row["cusip"] for plist in merged.values() for p in plist for row in p.rows}
    if args.skip_figi:
        cache = figi.load_cache()
        tickers = {c: figi.effective_ticker(cache[c]) for c in cusips if c in cache}
    else:
        tickers = figi.resolve(cusips, today=dt.date.today().isoformat())

    # 4) committed per-manager-quarter CSVs (filers of one manager combined)
    n_files = 0
    for span_manager in sorted({s.manager for s in spans}):
        mgr_spans = [s for s in spans if s.manager == span_manager]
        for qkey in window:
            per_cik = {s.cik: merged[(s.cik, qkey)] for s in mgr_spans
                       if merged.get((s.cik, qkey))}
            if not per_cik:
                continue
            build.write_manager_quarter(span_manager, qkey, per_cik, tickers)
            n_files += 1

    # 5) verification + flags + change tables
    n_match, n_mismatch = build.write_rowcount_verification(parsed_all)
    build.write_flags()
    n_changes = changes.regenerate_all()

    unmapped = len(cusips) - sum(1 for c in cusips if tickers.get(c))
    print(f"\nDone: {len(parsed_all)} filings parsed, {n_files} holdings CSVs, "
          f"{n_changes} change tables.")
    print(f"Row-count check: {n_match} match / {n_mismatch} mismatch "
          f"(data/out/verification_rowcounts.csv)")
    print(f"CUSIPs: {len(cusips)} total, {unmapped} without ticker "
          f"(data/ref/cusip_ticker.csv)")


if __name__ == "__main__":
    main()
