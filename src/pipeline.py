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
import sys
from collections import defaultdict

import build
import changes
import figi
import status
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

    # 1) fetch + parse everything, grouped (cik, qkey) -> parsed filings.
    # 13F-NT notices are listed but not parsed (no holdings); a fetch/parse
    # failure becomes an ERROR status for that filer-quarter, not a crash.
    parsed_all = []
    by_cik_quarter: dict[tuple[int, str], list] = defaultdict(list)
    nt_by_cik_quarter: dict[tuple[int, str], list] = defaultdict(list)
    errors_by_cik_quarter: dict[tuple[int, str], list[str]] = defaultdict(list)
    for span in spans:
        filings = list_13f_filings(span.cik, earliest)
        print(f"{span.manager} / {span.filer_name} (CIK {span.cik}): "
              f"{len(filings)} 13F filings since {earliest}")
        for f in filings:
            qkey = report_date_to_qkey(f.report_date)
            if qkey not in window or not span.covers(qkey):
                continue
            if f.form.startswith("13F-NT"):
                nt_by_cik_quarter[(span.cik, qkey)].append(f)
                continue
            try:
                cover, infotable = fetch_filing_docs(f)
                p = parse_filing(f, cover, infotable)
            except Exception as exc:  # noqa: BLE001 - recorded, blocks publication
                msg = f"{f.form} {f.accession}: {type(exc).__name__}: {exc}"
                print(f"!! FETCH/PARSE ERROR [{span.cik} {qkey}] {msg}",
                      file=sys.stderr)
                errors_by_cik_quarter[(span.cik, qkey)].append(msg)
                continue
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

    # 4) per-filer statuses + committed per-manager-quarter CSVs.
    # A manager-quarter is only written when every mapped filer covering it is
    # accounted for (HOLDINGS / NT / DUPLICATE); an unexplained absence (LATE)
    # or processing failure (ERROR) withholds the CSV and fails the run - a
    # partial manager book is never silently published. A quarter where some
    # filers reported but a sibling is merely NOT_DUE is likewise withheld
    # (incomplete, but not an error).
    today = dt.date.today()
    statuses: list[status.FilerStatus] = []
    blocked: list[str] = []
    withheld_not_due: list[str] = []
    n_files = 0
    for span_manager in sorted({s.manager for s in spans}):
        mgr_spans = [s for s in spans if s.manager == span_manager]
        for qkey in window:
            covering = [s for s in mgr_spans if s.covers(qkey)]
            if not covering:
                continue
            per_cik = {s.cik: merged[(s.cik, qkey)] for s in covering
                       if merged.get((s.cik, qkey))}
            kept, dropped = build.dedupe_filers(span_manager, qkey, per_cik)
            q_statuses = [
                status.classify(
                    s, qkey,
                    merged=per_cik.get(s.cik, []),
                    hr_filings=by_cik_quarter.get((s.cik, qkey), []),
                    nt_filings=nt_by_cik_quarter.get((s.cik, qkey), []),
                    fetch_errors=errors_by_cik_quarter.get((s.cik, qkey), []),
                    duplicate_detail=dropped.get(s.cik),
                    today=today,
                ) for s in covering
            ]
            statuses.extend(q_statuses)
            blocking = [st for st in q_statuses if st.status in status.BLOCKING]
            if blocking:
                for st in blocking:
                    print(f"!! PUBLICATION BLOCKED [{span_manager} {qkey}] "
                          f"filer {st.filer_cik} {st.status}: {st.detail}",
                          file=sys.stderr)
                blocked.append(f"{span_manager} {qkey}")
                continue
            if not kept:
                continue
            if any(st.status == "NOT_DUE" for st in q_statuses):
                withheld_not_due.append(f"{span_manager} {qkey}")
                continue
            build.write_manager_quarter(span_manager, qkey, kept, tickers)
            n_files += 1

    # 5) verification + flags + statuses + change tables
    n_match, n_mismatch = build.write_rowcount_verification(parsed_all)
    build.write_flags()
    status_path = status.write_status_csv(statuses)
    n_changes = changes.regenerate_all()

    unmapped = len(cusips) - sum(1 for c in cusips if tickers.get(c))
    print(f"\nDone: {len(parsed_all)} filings parsed, {n_files} holdings CSVs, "
          f"{n_changes} change tables.")
    print(f"Row-count check: {n_match} match / {n_mismatch} mismatch "
          f"(data/out/verification_rowcounts.csv)")
    print(f"CUSIPs: {len(cusips)} total, {unmapped} without ticker "
          f"(data/ref/cusip_ticker.csv)")
    counts = defaultdict(int)
    for st in statuses:
        counts[st.status] += 1
    print(f"Filer statuses ({status_path}): "
          + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    if withheld_not_due:
        print("Withheld (sibling filer not yet due): "
              + ", ".join(withheld_not_due))
    if blocked:
        print(f"\nFAILED: {len(blocked)} manager-quarter(s) blocked by "
              f"LATE/ERROR filer status: {', '.join(sorted(set(blocked)))}",
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
