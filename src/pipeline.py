"""13F pipeline entry point: fetch -> parse -> amendment-merge -> tickers -> CSVs.

Usage:
    python src/pipeline.py --start 2024Q2 --end 2026Q2 [--skip-figi] [--force-refresh]

Re-runnable: raw EDGAR responses are cached in data/raw/, the OpenFIGI cache in
data/ref/cusip_ticker.csv; committed holdings CSVs are rewritten each run.
--force-refresh bypasses the same-day cache on mutable SEC indexes — run with it
immediately before publication, since a filing arriving after the day's first
run is otherwise invisible until tomorrow.
Every run writes data/out/run_status.json; dashboard.py refuses to rebuild over
a failed run, so the previous approved dashboard survives bad data.
Note on units: since Jan 2023 the 13F 'value' column is whole dollars (previously
$thousands); every quarter this pipeline covers is whole-dollar.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import defaultdict

import build
import changes
import figi
import status
import validate
from common import (HOLDINGS, OUT, load_manager_map, quarter_end_date,
                    quarter_range, report_date_to_qkey)
from edgar import fetch_filing_docs, list_13f_filings, parse_filing

RUN_STATUS_PATH = OUT / "run_status.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2024Q2")
    ap.add_argument("--end", default="2026Q2")
    ap.add_argument("--skip-figi", action="store_true",
                    help="leave ticker column empty / cache-only")
    ap.add_argument("--force-refresh", action="store_true",
                    help="refetch mutable SEC indexes even when cached today "
                         "(required before publication)")
    args = ap.parse_args()

    window = quarter_range(args.start, args.end)
    earliest = quarter_end_date(args.start)
    spans = load_manager_map()
    today = dt.date.today()

    # 1) fetch + parse everything, grouped (cik, qkey) -> parsed filings.
    # 13F-NT notices are listed but not parsed (no holdings); a fetch/parse
    # failure becomes an ERROR status for that filer-quarter, not a crash.
    # A 13F filed for an in-window quarter outside the filer's mapped span
    # means manager_map.csv is stale (e.g. CIK 2038540 filing again after its
    # 2026Q1 scope-out): an HR blocks that manager-quarter, an NT only warns.
    parsed_all = []
    by_cik_quarter: dict[tuple[int, str], list] = defaultdict(list)
    nt_by_cik_quarter: dict[tuple[int, str], list] = defaultdict(list)
    errors_by_cik_quarter: dict[tuple[int, str], list[str]] = defaultdict(list)
    findings: list[validate.Finding] = []
    span_errors: dict[tuple[str, str], list[str]] = defaultdict(list)
    same_day: list[str] = []
    for span in spans:
        filings = list_13f_filings(span.cik, earliest,
                                   force_refresh=args.force_refresh)
        print(f"{span.manager} / {span.filer_name} (CIK {span.cik}): "
              f"{len(filings)} 13F filings since {earliest}")
        cik_spans = [s for s in spans if s.cik == span.cik]
        for f in filings:
            qkey = report_date_to_qkey(f.report_date)
            if qkey not in window:
                continue
            if f.filing_date == today.isoformat():
                same_day.append(f"{span.filer_name} {f.form} {f.accession}")
            if not span.covers(qkey):
                if any(s.covers(qkey) for s in cik_spans):
                    continue  # another span of the same CIK owns this quarter
                level = "WARN" if f.form.startswith("13F-NT") else "ERROR"
                finding = validate.Finding(
                    level, "out-of-span", qkey, span.manager, str(span.cik),
                    f.accession, "",
                    f"{f.form} filed {f.filing_date} for {qkey}, outside the "
                    f"mapped span {span.from_quarter or '..'}-"
                    f"{span.to_quarter or '..'} — revisit manager_map.csv")
                findings.append(finding)
                print(f"!! OUT-OF-SPAN FILING [{span.manager} {qkey}] "
                      f"CIK {span.cik} {finding.detail}", file=sys.stderr)
                if level == "ERROR":
                    span_errors[(span.manager, qkey)].append(finding.detail)
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
    # (incomplete, but not an error). Row-validation ERRORs and out-of-span
    # 13F-HRs withhold the CSV the same way.
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
            q_findings = validate.validate_rows(span_manager, qkey, kept)
            findings.extend(q_findings)
            row_errors = [f for f in q_findings if f.level == "ERROR"]
            oos_errors = span_errors.get((span_manager, qkey), [])
            if row_errors or oos_errors:
                for detail in ([f.detail for f in row_errors] + oos_errors):
                    print(f"!! PUBLICATION BLOCKED [{span_manager} {qkey}] "
                          f"validation: {detail}", file=sys.stderr)
                blocked.append(f"{span_manager} {qkey}")
                continue
            build.write_manager_quarter(span_manager, qkey, kept, tickers)
            n_files += 1

    # 5) verification + flags + merge decisions + statuses + validation + changes
    n_match, n_mismatch, n_value_mismatch = build.write_rowcount_verification(parsed_all)
    build.write_flags()
    build.write_merge_decisions()
    status_path = status.write_status_csv(statuses)
    findings.extend(validate.validate_identity(merged))
    findings.extend(validate.validate_tickers(tickers))
    findings.extend(validate.validate_qoq(HOLDINGS))
    validation_path = validate.write_validation_csv(findings)
    n_changes = changes.regenerate_all()

    unmapped = len(cusips) - sum(1 for c in cusips if tickers.get(c))
    print(f"\nDone: {len(parsed_all)} filings parsed, {n_files} holdings CSVs, "
          f"{n_changes} change tables.")
    print(f"Cover-page check: rows {n_match} match / {n_mismatch} mismatch, "
          f"value totals {n_value_mismatch} mismatch "
          f"(data/out/verification_rowcounts.csv)")
    print(f"CUSIPs: {len(cusips)} total, {unmapped} without ticker "
          f"(data/ref/cusip_ticker.csv)")
    counts = defaultdict(int)
    for st in statuses:
        counts[st.status] += 1
    print(f"Filer statuses ({status_path}): "
          + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    n_errors = sum(1 for f in findings if f.level == "ERROR")
    n_warns = sum(1 for f in findings if f.level == "WARN")
    disposition_coverage = validate.warning_disposition_coverage(
        findings, validate.load_warning_dispositions())
    unresolved_warnings = disposition_coverage["missing"]
    disposition_errors = (
        len(disposition_coverage["orphan_fingerprints"])
        + len(disposition_coverage["duplicate_fingerprints"])
        + disposition_coverage["incomplete_rows"]
    )
    n_dispositioned = n_warns - len(unresolved_warnings)
    print(f"Validation ({validation_path}): {n_errors} errors, {n_warns} warnings, "
          f"{n_dispositioned} dispositioned, "
          f"{len(unresolved_warnings)} unresolved, "
          f"{disposition_errors} invalid disposition row(s)")
    if withheld_not_due:
        print("Withheld (sibling filer not yet due): "
              + ", ".join(withheld_not_due))
    if same_day:
        print(f"\n!! {len(same_day)} filing(s) dated today — the SEC index may "
              f"gain more before midnight; re-run with --force-refresh "
              f"immediately before publication:", file=sys.stderr)
        for line in same_day:
            print(f"!!   {line}", file=sys.stderr)

    ok = (not blocked and n_errors == 0 and not unresolved_warnings
          and not disposition_errors)
    OUT.mkdir(parents=True, exist_ok=True)
    RUN_STATUS_PATH.write_text(json.dumps({
        "ok": ok,
        "completed_utc": dt.datetime.now(dt.timezone.utc).isoformat(
            timespec="seconds"),
        "window": [args.start, args.end],
        "force_refresh": args.force_refresh,
        "blocked": sorted(set(blocked)),
        "validation_errors": n_errors,
        "validation_warnings": n_warns,
        "validation_warnings_dispositioned": n_dispositioned,
        "unresolved_validation_warnings": [
            {"check": f.check, "quarter": f.quarter,
             "manager": f.manager, "cusip": f.cusip}
            for f in unresolved_warnings
        ],
        "invalid_warning_dispositions": disposition_errors,
        "same_day_filings": same_day,
    }, indent=2) + "\n", encoding="utf-8")
    if not ok:
        print(f"\nFAILED: {len(set(blocked))} manager-quarter(s) blocked "
              f"(LATE/ERROR status or validation), {n_errors} validation "
              f"error(s), {len(unresolved_warnings)} unresolved warning(s), "
              f"{disposition_errors} invalid warning disposition row(s): "
              f"{', '.join(sorted(set(blocked))) or '-'}",
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
