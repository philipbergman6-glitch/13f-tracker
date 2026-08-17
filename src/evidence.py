"""Auditable evidence package for a quarterly release (Phase 3).

Consolidates a green pipeline run's outputs — filer_status.csv, validation.csv,
flags.csv, merge_decisions.csv, verification_rowcounts.csv, run_status.json,
the committed holdings/ref tables and the published dashboard — into one
durable, self-contained package under docs/evidence/<YYYYQn>/ that lets
another analyst reproduce the dashboard and explain every displayed number.
Nothing is re-derived here: every figure is copied from the run that produced
it and tied to that run via manifest.json.

Usage (release order: pipeline.py --force-refresh -> dashboard.py -> evidence.py):
    python src/evidence.py [--quarter 2026Q2]

Hard-fails (SystemExit) over a failed or missing pipeline run, a failing test
suite, a missing dashboard or one whose as-of quarter is not the release
quarter, missing raw source data (no retrieval date), or a cover-page
reconciliation mismatch with no entry in data/ref/known_exceptions.csv — an
unexplained number never ships. A superseded package is archived under
docs/evidence/_archive/, never deleted.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from common import (HOLDINGS, OUT, RAW, REF, REPO, load_manager_map,
                    quarter_end_date, quarter_range, report_date_to_qkey)
from edgar import filing_index_url

EVIDENCE_DIR = REPO / "docs" / "evidence"
DASHBOARD_HTML = REPO / "dashboard" / "index.html"
RUN_STATUS_PATH = OUT / "run_status.json"
EXCEPTIONS_PATH = REF / "known_exceptions.csv"

FILINGS_COLUMNS = [
    "quarter", "manager", "filer_cik", "filer_name", "form", "accession",
    "filing_date", "report_date", "retrieved_date", "role", "rows_parsed",
    "table_entry_total", "rows_match", "value_parsed_usd", "table_value_total",
    "value_match", "exception_id", "filing_url",
]

# Required-item checklist: (report section, package file) per Phase 3 item.
REQUIRED_ITEMS = [
    ("SEC filing URLs and retrieval dates", "filings.csv"),
    ("CIK and accession numbers", "filings.csv"),
    ("Filing dates and report periods", "filings.csv"),
    ("Original row counts and cover-page totals", "filings.csv"),
    ("Parsed-vs-source reconciliation (rows and values)", "filings.csv"),
    ("Amendment-merge and duplicate decisions", "merge_decisions.csv"),
    ("Multi-filer completeness", "filer_status.csv"),
    ("Automated test results", "test_results.json"),
    ("Known exceptions and reviewer sign-off", "exceptions.csv + report.md"),
    ("SHA-256 checksums and source version", "checksums.csv + manifest.json"),
]


def fail(msg: str) -> None:
    raise SystemExit(f"evidence: {msg}")


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        fail(f"{path} missing — run src/pipeline.py first")
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


def load_run_status() -> dict:
    if not RUN_STATUS_PATH.exists():
        fail(f"{RUN_STATUS_PATH} missing — run src/pipeline.py first")
    run = json.loads(RUN_STATUS_PATH.read_text(encoding="utf-8"))
    if not run.get("ok"):
        fail(f"last pipeline run FAILED ({run.get('completed_utc')}: "
             f"blocked={run.get('blocked')}, validation_errors="
             f"{run.get('validation_errors')}) — no evidence package over a "
             f"failed run")
    return run


def mtime_date(path: Path) -> str:
    return dt.date.fromtimestamp(path.stat().st_mtime).isoformat()


def raw_retrieved_date(cik: str, accession: str) -> str:
    """Retrieval date of the filing's raw documents = latest mtime in the
    accession's data/raw dir (fetch_cached never rewrites immutable docs)."""
    fdir = RAW / cik / accession.replace("-", "")
    files = [p for p in fdir.glob("*") if p.is_file()] if fdir.exists() else []
    if not files:
        fail(f"no raw documents under {fdir} for accession {accession} — "
             f"cannot establish a retrieval date; re-run src/pipeline.py")
    return max(mtime_date(p) for p in files)


def submissions_retrieved_date(cik: str) -> str:
    path = RAW / cik / "submissions.json"
    if not path.exists():
        fail(f"{path} missing — cannot establish index retrieval date")
    return mtime_date(path)


# --- consolidation ----------------------------------------------------------

def effective_roles(merge_decisions: list[dict]) -> dict[str, dict]:
    """Last decision wins per accession: dedupe_filers appends DUPLICATE_BOOK
    rows after merge_quarter's per-filer roles for the same filing."""
    return {d["accession"]: d for d in merge_decisions}


def collect_filings(verification: list[dict], merge_decisions: list[dict],
                    filer_status: list[dict], exceptions: list[dict],
                    cik_to_span: dict[str, object]) -> list[dict]:
    """One row per filing used: every parsed 13F-HR (verification) plus every
    13F-NT notice (filer_status). Reconciliation mismatches must map to a
    known-exception entry by accession, or the package refuses to build."""
    roles = effective_roles(merge_decisions)
    exc_by_acc = {e["accession"]: e for e in exceptions if e["accession"]}
    rows = []
    for v in verification:
        cik = v["filer_cik"]
        span = cik_to_span.get(cik)
        if span is None:
            fail(f"CIK {cik} in verification_rowcounts.csv has no "
                 f"manager_map.csv entry")
        role = roles.get(v["accession"])
        if role is None:
            fail(f"parsed filing {v['accession']} has no merge decision — "
                 f"stale data/out/merge_decisions.csv; re-run src/pipeline.py")
        mismatch = v["rows_match"] != "True" or v["value_match"] != "True"
        exc = exc_by_acc.get(v["accession"]) if mismatch else None
        if mismatch and exc is None:
            fail(f"cover-page reconciliation mismatch for {v['accession']} "
                 f"(rows {v['rows_parsed']} vs {v['table_entry_total']}, value "
                 f"{v['value_parsed_usd']} vs {v['table_value_total']}) has no "
                 f"entry in {EXCEPTIONS_PATH} — document it before releasing")
        rows.append({
            "quarter": report_date_to_qkey(v["report_date"]),
            "manager": span.manager, "filer_cik": cik,
            "filer_name": span.filer_name, "form": v["form"],
            "accession": v["accession"], "filing_date": v["filing_date"],
            "report_date": v["report_date"],
            "retrieved_date": raw_retrieved_date(cik, v["accession"]),
            "role": role["role"], "rows_parsed": v["rows_parsed"],
            "table_entry_total": v["table_entry_total"],
            "rows_match": v["rows_match"],
            "value_parsed_usd": v["value_parsed_usd"],
            "table_value_total": v["table_value_total"],
            "value_match": v["value_match"],
            "exception_id": exc["id"] if exc else "",
            "filing_url": v["filing_url"],
        })
    known = {r["accession"] for r in rows}
    for s in filer_status:
        if s["status"] != "NT" or s["accession"] in known:
            continue
        rows.append({
            "quarter": s["quarter"], "manager": s["manager"],
            "filer_cik": s["filer_cik"], "filer_name": s["filer_name"],
            "form": s["form"], "accession": s["accession"],
            "filing_date": s["filing_date"],
            "report_date": quarter_end_date(s["quarter"]),
            "retrieved_date": submissions_retrieved_date(s["filer_cik"]),
            "role": "NT_NOTICE", "rows_parsed": "", "table_entry_total": "",
            "rows_match": "", "value_parsed_usd": "", "table_value_total": "",
            "value_match": "", "exception_id": "",
            "filing_url": filing_index_url(int(s["filer_cik"]), s["accession"]),
        })
    rows.sort(key=lambda r: (r["quarter"], r["manager"], r["filer_cik"],
                             r["accession"]))
    return rows


def check_status_coverage(filer_status: list[dict], filings: list[dict],
                          spans: list, window: list[str]) -> None:
    """Multi-filer completeness: every mapped (manager, filer, quarter) has a
    status row, and every HR accession behind a status is in filings.csv."""
    have = {(s["manager"], s["filer_cik"], s["quarter"]) for s in filer_status}
    for span in spans:
        for qkey in window:
            if span.covers(qkey) and (span.manager, str(span.cik), qkey) not in have:
                fail(f"no filer_status row for {span.manager} / CIK {span.cik} "
                     f"/ {qkey} — statuses are stale; re-run src/pipeline.py")
    filed = {f["accession"] for f in filings}
    for s in filer_status:
        if s["status"] in ("HOLDINGS", "DUPLICATE"):
            for acc in s["accession"].split("+"):
                if acc not in filed:
                    fail(f"status accession {acc} ({s['manager']} "
                         f"{s['quarter']}) missing from the verification "
                         f"table — re-run src/pipeline.py")


# --- environment evidence ---------------------------------------------------

def run_test_suite() -> dict:
    """Run the full unit-test suite and record the outcome; a failing suite
    blocks the package."""
    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=REPO, capture_output=True, text=True)
    output = (proc.stderr or "") + (proc.stdout or "")
    m = re.search(r"Ran (\d+) tests", output)
    passed = proc.returncode == 0 and m is not None
    result = {
        "suite": "python -m unittest discover -s tests",
        "python": sys.version.split()[0],
        "tests_ran": int(m.group(1)) if m else None,
        "passed": passed,
        "run_utc": started,
        "output_tail": output.strip().splitlines()[-3:],
    }
    if not passed:
        fail(f"test suite failed — no evidence package over failing tests:\n"
             f"{output.strip().splitlines()[-15:]}")
    return result


def git_info() -> dict:
    def run(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=REPO, capture_output=True,
                              text=True, check=True).stdout.strip()
    dirty = [line for line in run("status", "--porcelain").splitlines() if line]
    return {"commit": run("rev-parse", "HEAD"),
            "commit_date": run("show", "-s", "--format=%cI", "HEAD"),
            "dirty_files": dirty}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def checksum_targets() -> list[Path]:
    """The published dashboard and every data file it derives from, plus the
    run's gate outputs."""
    targets = [DASHBOARD_HTML]
    targets += sorted(HOLDINGS.rglob("*.csv"))
    targets += sorted(REF.glob("*.csv"))
    targets += sorted((OUT / "changes").rglob("*.csv"))
    targets += [OUT / n for n in ("flags.csv", "merge_decisions.csv",
                                  "validation.csv", "verification_rowcounts.csv",
                                  "run_status.json")]
    missing = [t for t in targets if not t.exists()]
    if missing:
        fail(f"checksum targets missing: {[str(m) for m in missing]}")
    return targets


def dashboard_as_of() -> str:
    if not DASHBOARD_HTML.exists():
        fail(f"{DASHBOARD_HTML} missing — run src/dashboard.py first")
    m = re.search(r'"as_of":"(\d{4}Q\d)"',
                  DASHBOARD_HTML.read_text(encoding="utf-8"))
    if not m:
        fail(f"could not find the as-of quarter in {DASHBOARD_HTML}")
    return m.group(1)


def archive_existing(pkg_dir: Path, now_utc: dt.datetime) -> str | None:
    """Superseded packages are archived, never deleted (firm-wide rule)."""
    if not pkg_dir.exists():
        return None
    dest = (EVIDENCE_DIR / "_archive" / pkg_dir.name
            / now_utc.strftime("%Y%m%dT%H%M%SZ"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    pkg_dir.replace(dest)
    return str(dest.relative_to(REPO))


# --- report -----------------------------------------------------------------

def _fmt_int(x: str | None) -> str:
    """Thousands-grouped integer, em-dash for a blank (e.g. an absent
    cover-page total or an NT notice's empty counts)."""
    return f"{int(x):,}" if x not in ("", None) else "—"


def _md_table(columns: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(columns) + " |",
             "|" + "|".join("---" for _ in columns) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def render_report(qkey: str, run: dict, filings: list[dict],
                  merge_decisions: list[dict], filer_status: list[dict],
                  validation: list[dict], exceptions: list[dict],
                  tests: dict, git: dict, checksums: dict[str, str],
                  generated_utc: str) -> str:
    window = run["window"]
    q_filings = [f for f in filings if f["quarter"] == qkey]
    q_status = [s for s in filer_status if s["quarter"] == qkey]
    mismatches = [f for f in filings
                  if f["role"] != "NT_NOTICE"
                  and (f["rows_match"] != "True" or f["value_match"] != "True")]
    nontrivial = [d for d in merge_decisions if d["role"] != "BASE_ORIGINAL"]
    parsed = [f for f in filings if f["role"] != "NT_NOTICE"]
    n_rows_ok = sum(1 for f in parsed if f["rows_match"] == "True")
    n_value_ok = sum(1 for f in parsed if f["value_match"] == "True")
    status_counts = defaultdict(int)
    for s in filer_status:
        status_counts[s["status"]] += 1
    val_counts = defaultdict(int)
    for v in validation:
        val_counts[v["level"]] += 1
    dirty = git["dirty_files"]

    lines = [
        f"# Evidence package — {qkey} release",
        "",
        f"Generated {generated_utc} from pipeline run {run['completed_utc']} "
        f"(window {window[0]}–{window[1]}, force_refresh="
        f"{run['force_refresh']}), source commit `{git['commit'][:12]}`"
        + (f" with {len(dirty)} uncommitted change(s) at generation time"
           if dirty else " (clean tree)") + ".",
        "",
        "Every figure below is copied from that run's outputs "
        "(nothing re-derived); machine-readable appendices sit next to this "
        "report. Required-item checklist:",
        "",
        _md_table(["#", "Required item", "Where"],
                  [[i + 1, item, f"`{where}`"]
                   for i, (item, where) in enumerate(REQUIRED_ITEMS)]),
        "",
        "## 1. Filings used",
        "",
        f"{len(filings)} filings across {window[0]}–{window[1]} "
        f"({sum(1 for f in filings if f['role'] != 'NT_NOTICE')} parsed 13F-HR/"
        f"13F-HR/A, {sum(1 for f in filings if f['role'] == 'NT_NOTICE')} "
        f"13F-NT notices). `filings.csv` lists, per filing: manager, filer "
        f"CIK, form, accession, filing date, report period, SEC EDGAR URL, "
        f"raw-data retrieval date, merge role, and cover-page reconciliation. "
        f"Retrieval dates are the raw documents' download dates under "
        f"`data/raw/` (immutable once fetched); 13F-NT retrieval dates are "
        f"those of the SEC submissions index that evidences the notice.",
        "",
        f"### {qkey} filings ({len(q_filings)})",
        "",
        _md_table(
            ["Manager", "CIK", "Form", "Accession (EDGAR link)", "Filed",
             "Retrieved", "Rows", "Value ($)"],
            [[f["manager"], f["filer_cik"], f["form"],
              f"[{f['accession']}]({f['filing_url']})", f["filing_date"],
              f["retrieved_date"], f["rows_parsed"] or "—",
              _fmt_int(f["value_parsed_usd"])] for f in q_filings]),
        "",
        "## 2. Parsed-vs-source reconciliation",
        "",
        f"For every parsed filing, the committed rows are reconciled against "
        f"the filing's own cover page: parsed row count vs `tableEntryTotal` "
        f"and summed `value_usd` vs `tableValueTotal`. Result: "
        f"**{n_rows_ok} of {len(parsed)} filings match on rows and "
        f"{n_value_ok} of {len(parsed)} on value totals**; every mismatch "
        f"maps to a documented known exception:",
        "",
        _md_table(
            ["Filing", "Rows parsed / declared", "Value parsed / declared",
             "Exception"],
            [[f"{f['manager']} {f['quarter']} `{f['accession']}`",
              f"{f['rows_parsed']} / {f['table_entry_total'] or '—'}",
              f"{_fmt_int(f['value_parsed_usd'])} / "
              f"{_fmt_int(f['table_value_total'])}",
              f["exception_id"]] for f in mismatches])
        if mismatches else "(no mismatches)",
        "",
        "## 3. Amendment-merge and duplicate decisions",
        "",
        f"`merge_decisions.csv` records, for each of the "
        f"{len(merge_decisions)} decision rows, whether the filing is in its "
        f"quarter-final book and why (quarter-final = latest RESTATEMENT, or "
        f"the original 13F-HR, plus subsequent NEW HOLDINGS amendments — Form "
        f"13F Special Instruction 3). Decisions other than a lone original "
        f"13F-HR base:",
        "",
        _md_table(["CIK", "Quarter", "Accession", "Role", "Why"],
                  [[d["filer_cik"], d["quarter"], f"`{d['accession']}`",
                    d["role"], d["detail"]] for d in nontrivial])
        if nontrivial else "(every book is a single original 13F-HR)",
        "",
        "## 4. Multi-filer completeness",
        "",
        f"Every mapped (manager, filer, quarter) in the window has an "
        f"explicit committed status (verified programmatically at package "
        f"build): " + ", ".join(f"{k}={v}" for k, v in sorted(status_counts.items()))
        + f". None is LATE or ERROR (both block publication). Full table in "
          f"`filer_status.csv`.",
        "",
        f"### {qkey} statuses",
        "",
        _md_table(["Manager", "Filer", "CIK", "Status", "Detail"],
                  [[s["manager"], s["filer_name"], s["filer_cik"], s["status"],
                    s["detail"]] for s in q_status]),
        "",
        "## 5. Validation findings",
        "",
        f"{val_counts.get('ERROR', 0)} errors, {val_counts.get('WARN', 0)} "
        f"warnings (`validation.csv`; errors block publication). Warning "
        f"classes are calibrated against accepted SEC filings — see "
        f"`notes/phase2-production-controls.md`.",
        "",
        "## 6. Automated tests",
        "",
        f"`{tests['suite']}` (Python {tests['python']}): "
        f"**{tests['tests_ran']} tests, "
        f"{'PASS' if tests['passed'] else 'FAIL'}**, run {tests['run_utc']} "
        f"(`test_results.json`). A failing suite blocks this package.",
        "",
        "## 7. Known exceptions",
        "",
        "Accepted filer-side discrepancies and scope decisions, from the "
        "committed register `data/ref/known_exceptions.csv` (each cites its "
        "source URL and retrieval date):",
        "",
        _md_table(["ID", "Quarter", "Manager", "Category", "Summary",
                   "Resolution"],
                  [[e["id"], e["quarter"], e["manager"], e["category"],
                    e["summary"], e["resolution"]] for e in exceptions]),
        "",
        "## 8. Checksums and versions",
        "",
        f"`checksums.csv` holds SHA-256 digests for the published dashboard "
        f"and all {len(checksums) - 1} source data files it derives from "
        f"(holdings CSVs, filer statuses, reference tables, change tables, "
        f"run gate outputs). Source code version: commit `{git['commit']}` "
        f"({git['commit_date']}).",
        "",
        f"- `dashboard/index.html` — SHA-256 "
        f"`{checksums['dashboard/index.html']}`",
        "",
        "## 9. How to reproduce this release",
        "",
        "```",
        f"git checkout {git['commit']}",
        f"python src/pipeline.py --start {window[0]} --end {window[1]} "
        f"--force-refresh   # add --skip-figi to reuse the committed ticker cache",
        f"python src/dashboard.py --quarter {qkey}",
        f"python src/evidence.py --quarter {qkey}",
        "```",
        "",
        "Raw EDGAR responses cache under `data/raw/` (re-fetchable; superseded "
        "mutable indexes are archived, not overwritten). Re-running against "
        "live EDGAR after the release date can differ only if a filer amends: "
        "compare the regenerated holdings CSVs against the digests in "
        "`checksums.csv` to detect any drift.",
        "",
        "## Reviewer sign-off",
        "",
        "Completed by a human reviewer before the release is considered "
        "approved; the signed copy is committed in place.",
        "",
        "- Reviewer name: ______________________",
        "- Review date: ______________________",
        "- Decision (approve / reject, with notes): ______________________",
        "",
    ]
    return "\n".join(lines)


# --- entry ------------------------------------------------------------------

def build_package(qkey: str) -> Path:
    run = load_run_status()
    window_q = run["window"]
    window = quarter_range(window_q[0], window_q[1])
    if qkey not in window:
        fail(f"release quarter {qkey} outside the run window "
             f"{window_q[0]}–{window_q[1]}")
    as_of = dashboard_as_of()
    if as_of != qkey:
        fail(f"dashboard/index.html is as of {as_of}, not {qkey} — rebuild it "
             f"with `python src/dashboard.py --quarter {qkey}` first")

    spans = load_manager_map()
    cik_to_span = {str(s.cik): s for s in spans}
    verification = read_csv(OUT / "verification_rowcounts.csv")
    merge_decisions = read_csv(OUT / "merge_decisions.csv")
    filer_status = read_csv(HOLDINGS / "filer_status.csv")
    validation = read_csv(OUT / "validation.csv")
    flags = read_csv(OUT / "flags.csv")
    exceptions = read_csv(EXCEPTIONS_PATH)

    filings = collect_filings(verification, merge_decisions, filer_status,
                              exceptions, cik_to_span)
    check_status_coverage(filer_status, filings, spans, window)
    if not any(f["quarter"] == qkey for f in filings):
        fail(f"no filings for release quarter {qkey}")

    tests = run_test_suite()
    git = git_info()
    targets = checksum_targets()
    checksums = {str(t.relative_to(REPO)).replace("\\", "/"): sha256_file(t)
                 for t in targets}

    now = dt.datetime.now(dt.timezone.utc)
    generated_utc = now.isoformat(timespec="seconds")
    pkg_dir = EVIDENCE_DIR / qkey
    archived = archive_existing(pkg_dir, now)
    if archived:
        print(f"superseded package archived to {archived}")
    pkg_dir.mkdir(parents=True)

    write_csv(pkg_dir / "filings.csv", filings, FILINGS_COLUMNS)
    write_csv(pkg_dir / "merge_decisions.csv", merge_decisions,
              list(merge_decisions[0]) if merge_decisions else
              ["filer_cik", "quarter", "accession", "form", "filing_date",
               "role", "in_book", "detail"])
    write_csv(pkg_dir / "filer_status.csv", filer_status, list(filer_status[0]))
    write_csv(pkg_dir / "validation.csv", validation,
              list(validation[0]) if validation else
              ["level", "check", "quarter", "manager", "filer_cik",
               "accession", "cusip", "detail"])
    write_csv(pkg_dir / "flags.csv", flags,
              list(flags[0]) if flags else
              ["filer_cik", "quarter", "accession", "problem"])
    write_csv(pkg_dir / "exceptions.csv", exceptions, list(exceptions[0]))
    write_csv(pkg_dir / "checksums.csv",
              [{"path": p, "sha256": h} for p, h in sorted(checksums.items())],
              ["path", "sha256"])
    (pkg_dir / "test_results.json").write_text(
        json.dumps(tests, indent=2) + "\n", encoding="utf-8")
    (pkg_dir / "manifest.json").write_text(json.dumps({
        "release_quarter": qkey,
        "generated_utc": generated_utc,
        "source_commit": git["commit"],
        "source_commit_date": git["commit_date"],
        "uncommitted_changes_at_generation": git["dirty_files"],
        "pipeline_run": run,
        "n_filings": len(filings),
        "n_checksummed_files": len(checksums),
        "package_files": sorted(p.name for p in pkg_dir.iterdir()) + ["report.md"],
    }, indent=2) + "\n", encoding="utf-8")
    (pkg_dir / "report.md").write_text(
        render_report(qkey, run, filings, merge_decisions, filer_status,
                      validation, exceptions, tests, git, checksums,
                      generated_utc),
        encoding="utf-8")
    return pkg_dir


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quarter", default=None,
                    help="release quarter, e.g. 2026Q2 (default: the "
                         "dashboard's as-of quarter)")
    args = ap.parse_args()
    qkey = args.quarter or dashboard_as_of()
    pkg_dir = build_package(qkey)
    files = sorted(p.name for p in pkg_dir.iterdir())
    print(f"Evidence package: {pkg_dir.relative_to(REPO)} "
          f"({len(files)} files: {', '.join(files)})")


if __name__ == "__main__":
    main()
