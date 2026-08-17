"""Formal quarterly release orchestrator (Phase 5): one gated sequence from
SEC refresh to publication, with an auditable staged/published separation.

The individual controls all live in the tools this script calls — pipeline.py
(LATE/ERROR + validation gates, --force-refresh, raw archiving), the test
suite, dashboard.py (run gate) and evidence.py (reconciliation, exception,
provenance and test gates). release.py only sequences them, stops at the
first failure, and adds the publication gates that sit between "staged" and
"published". Full sequence and block conditions: docs/release-runbook.md.

Subcommands:
  stage     steps 1-6: pipeline --force-refresh -> test suite -> staging
            dashboard (dashboard/staging/index.html, never the published
            copy) -> evidence package (docs/evidence/<Q>/, checksummed
            against the staging build).
  (step 7)  human review: fill the sign-off block in
            docs/evidence/<Q>/report.md and commit it.
  publish   steps 8-9: re-verify every gate (green run, tests, evidence
            freshness + checksums, filer statuses, provenance, committed
            sign-off), archive the prior published release under
            dashboard/_archive/<UTC>/ (superseded, never deleted), promote
            staging -> dashboard/index.html, record the release in
            dashboard/release.json and docs/releases.csv.
  rollback  re-promote the newest (or --to <stamp>) archived release; the
            replaced copy is archived first.

Usage:
    python src/release.py stage   --quarter 2026Q2 [--start 2024Q2 --end 2026Q2] [--skip-figi]
    python src/release.py publish --quarter 2026Q2
    python src/release.py rollback [--to 20260817T120000Z]
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import evidence
import status
from common import HOLDINGS, REPO

EVIDENCE_DIR = REPO / "docs" / "evidence"
STAGING_HTML = REPO / "dashboard" / "staging" / "index.html"
PUBLISHED_HTML = REPO / "dashboard" / "index.html"
PUBLISHED_META = REPO / "dashboard" / "release.json"
DASH_ARCHIVE = REPO / "dashboard" / "_archive"
RELEASES_CSV = REPO / "docs" / "releases.csv"
STATUS_CSV = HOLDINGS / "filer_status.csv"

RELEASE_COLUMNS = [
    "published_utc", "action", "quarter", "pipeline_run_utc", "source_commit",
    "dashboard_sha256", "evidence_package", "evidence_generated_utc",
    "reviewer", "review_date", "decision", "prior_archived_to", "note",
]

QKEY_RE = re.compile(r"^\d{4}Q[1-4]$")

# Must parse exactly the lines evidence.SIGN_OFF_LINES writes (verified by
# tests/test_release.py so the template and this gate can never drift apart).
SIGN_OFF_FIELDS = {
    "reviewer": re.compile(r"^- Reviewer name:\s*(.*)$", re.M),
    "review_date": re.compile(r"^- Review date \(YYYY-MM-DD\):\s*(.*)$", re.M),
    "decision": re.compile(
        r"^- Decision \(approve / reject, with notes\):\s*(.*)$", re.M),
}


def fail(msg: str) -> None:
    raise SystemExit(f"release: {msg}")


def read_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# --- stage (steps 1-6) ------------------------------------------------------

def run_step(n: int, total: int, name: str, cmd: list[str]) -> None:
    print(f"\n=== release stage {n}/{total}: {name}\n$ {' '.join(cmd)}",
          flush=True)
    proc = subprocess.run(cmd, cwd=REPO)
    if proc.returncode != 0:
        fail(f"step '{name}' failed (exit {proc.returncode}) — sequence "
             f"stopped, nothing published")


def cmd_stage(args: argparse.Namespace) -> None:
    q = args.quarter
    steps = [
        ("pipeline: refresh SEC indexes, download/archive filings, build "
         "holdings + changes (gates: LATE/ERROR statuses, validation, "
         "out-of-span)",
         [sys.executable, "src/pipeline.py", "--start", args.start,
          "--end", args.end, "--force-refresh"]
         + (["--skip-figi"] if args.skip_figi else [])),
        ("automated test suite",
         [sys.executable, "-m", "unittest", "discover", "-s", "tests"]),
        ("staging dashboard (published copy untouched)",
         [sys.executable, "src/dashboard.py", "--quarter", q,
          "--out", str(STAGING_HTML)]),
        ("evidence package (gates: reconciliation, exceptions, provenance, "
         "status coverage)",
         [sys.executable, "src/evidence.py", "--quarter", q,
          "--dashboard", str(STAGING_HTML)]),
    ]
    for i, (name, cmd) in enumerate(steps, 1):
        run_step(i, len(steps), name, cmd)
    report = EVIDENCE_DIR / q / "report.md"
    print(f"\nStaged {q}: dashboard {STAGING_HTML.relative_to(REPO)}, "
          f"evidence {report.parent.relative_to(REPO)}/")
    print(f"Next: review the staging dashboard and evidence report, fill the "
          f"sign-off block in {report.relative_to(REPO)}, commit it, then "
          f"run `python src/release.py publish --quarter {q}`.")


# --- publish gates (step 8 preconditions) -----------------------------------

def check_staging(qkey: str) -> None:
    if not STAGING_HTML.exists():
        fail(f"{STAGING_HTML} missing — run `release.py stage` first")
    as_of = evidence.dashboard_as_of(STAGING_HTML)
    if as_of != qkey:
        fail(f"staging dashboard is as of {as_of}, not {qkey} — re-stage")


def check_evidence_package(qkey: str, run: dict) -> dict:
    manifest_path = EVIDENCE_DIR / qkey / "manifest.json"
    if not manifest_path.exists():
        fail(f"no evidence package for {qkey} ({manifest_path} missing) — "
             f"run `release.py stage` first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("release_quarter") != qkey:
        fail(f"evidence package under docs/evidence/{qkey}/ declares release "
             f"quarter {manifest.get('release_quarter')} — corrupt package")
    pkg_run = (manifest.get("pipeline_run") or {}).get("completed_utc")
    if pkg_run != run.get("completed_utc"):
        fail(f"evidence package was built from pipeline run {pkg_run} but "
             f"the current run is {run.get('completed_utc')} — the package "
             f"is stale; re-stage and re-review before publishing")
    return manifest


def check_filer_statuses() -> None:
    """Every filer status must be explained; LATE/ERROR never publish."""
    if not STATUS_CSV.exists():
        fail(f"{STATUS_CSV} missing — run `release.py stage` first")
    bad = [r for r in read_csv(STATUS_CSV) if r["status"] in status.BLOCKING]
    if bad:
        fail(f"{len(bad)} unexplained filer status(es): " + "; ".join(
            f"{r['manager']} {r['quarter']} CIK {r['filer_cik']} "
            f"{r['status']} ({r['detail']})" for r in bad[:5]))


def check_provenance(qkey: str) -> None:
    """Every filing in the package must carry its source URL and the date the
    raw data was retrieved from SEC EDGAR."""
    filings_path = EVIDENCE_DIR / qkey / "filings.csv"
    if not filings_path.exists():
        fail(f"{filings_path} missing — incomplete evidence package")
    bad = [r for r in read_csv(filings_path)
           if not r["retrieved_date"] or not r["filing_url"]]
    if bad:
        fail(f"source provenance missing for {len(bad)} filing(s), e.g. "
             f"{bad[0]['manager']} {bad[0]['quarter']} "
             f"{bad[0]['accession']} — re-stage")


def check_checksums(qkey: str) -> str:
    """Every artifact being published must still match the digest recorded in
    the reviewed evidence package (= the output is reproducible as approved).
    Returns the staging dashboard's digest."""
    checksums_path = EVIDENCE_DIR / qkey / "checksums.csv"
    if not checksums_path.exists():
        fail(f"{checksums_path} missing — incomplete evidence package")
    dash_rel = str(STAGING_HTML.relative_to(REPO)).replace("\\", "/")
    dash_sha = None
    missing, mismatched = [], []
    for r in read_csv(checksums_path):
        p = REPO / r["path"]
        if not p.exists():
            missing.append(r["path"])
            continue
        digest = evidence.sha256_file(p)
        if digest != r["sha256"]:
            mismatched.append(r["path"])
        if r["path"] == dash_rel:
            dash_sha = digest
    if missing or mismatched:
        fail(f"artifacts changed since the evidence package was built — "
             f"{len(mismatched)} digest mismatch(es) "
             f"{mismatched[:5]}, {len(missing)} missing {missing[:5]}; "
             f"re-stage and re-review")
    if dash_sha is None:
        fail(f"{dash_rel} is not among the package checksums — the package "
             f"does not evidence the staging build; re-stage")
    return dash_sha


def check_sign_off(report_text: str, report_rel: str) -> dict:
    values = {}
    for field, rx in SIGN_OFF_FIELDS.items():
        m = rx.search(report_text)
        if not m:
            fail(f"sign-off line for '{field}' missing from {report_rel} — "
                 f"the block was edited out; restore it")
        v = m.group(1).strip()
        if not v or "___" in v:
            fail(f"sign-off '{field}' is blank in {report_rel} — a human "
                 f"reviewer must complete and commit the sign-off block "
                 f"before publication")
        values[field] = v
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", values["review_date"]):
        fail(f"sign-off review date {values['review_date']!r} is not "
             f"YYYY-MM-DD")
    if not values["decision"].lower().startswith("approve"):
        fail(f"sign-off decision is not an approval: {values['decision']!r}")
    return values


def check_report_committed(report_rel: str) -> None:
    """Approval must live in git history, not just the working tree."""
    proc = subprocess.run(["git", "status", "--porcelain", "--", report_rel],
                          cwd=REPO, capture_output=True, text=True)
    if proc.returncode != 0:
        fail(f"git status failed for {report_rel}: {proc.stderr.strip()}")
    if proc.stdout.strip():
        fail(f"{report_rel} is uncommitted ({proc.stdout.strip()!r}) — "
             f"commit the signed report before publishing")


def run_tests() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=REPO, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = "\n".join(((proc.stderr or "") + (proc.stdout or ""))
                         .strip().splitlines()[-10:])
        fail(f"test suite failed — publication blocked:\n{tail}")


def verify_publish_gates(qkey: str) -> dict:
    """All step-8 preconditions; any failure is a SystemExit before anything
    is touched. Returns what the release record needs."""
    run = evidence.load_run_status()  # green pipeline run, or SystemExit
    check_staging(qkey)
    manifest = check_evidence_package(qkey, run)
    check_filer_statuses()
    check_provenance(qkey)
    dash_sha = check_checksums(qkey)
    report_path = EVIDENCE_DIR / qkey / "report.md"
    report_rel = str(report_path.relative_to(REPO)).replace("\\", "/")
    sign = check_sign_off(report_path.read_text(encoding="utf-8"), report_rel)
    check_report_committed(report_rel)
    return {"run": run, "manifest": manifest, "dashboard_sha256": dash_sha,
            "sign_off": sign}


# --- promote / record (steps 8-9) -------------------------------------------

def archive_published(now_utc: dt.datetime) -> str | None:
    """Copy the live release (dashboard + its release record) into
    dashboard/_archive/<UTC>/ — superseded, never deleted."""
    if not PUBLISHED_HTML.exists():
        return None
    dest = DASH_ARCHIVE / now_utc.strftime("%Y%m%dT%H%M%SZ")
    if dest.exists():
        fail(f"archive collision at {dest} — retry in a second")
    dest.mkdir(parents=True)
    shutil.copy2(PUBLISHED_HTML, dest / "index.html")
    if PUBLISHED_META.exists():
        shutil.copy2(PUBLISHED_META, dest / "release.json")
    else:
        (dest / "release.json").write_text(json.dumps({
            "note": "published before release governance (Phase 5) — "
                    "no recorded run or sign-off"}, indent=2) + "\n",
            encoding="utf-8")
    return str(dest.relative_to(REPO))


def append_release_row(meta: dict) -> None:
    RELEASES_CSV.parent.mkdir(parents=True, exist_ok=True)
    new = not RELEASES_CSV.exists()
    with open(RELEASES_CSV, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=RELEASE_COLUMNS)
        if new:
            w.writeheader()
        w.writerow({c: str(meta.get(c) or "") for c in RELEASE_COLUMNS})


def do_publish(qkey: str, gates: dict, git: dict,
               now_utc: dt.datetime) -> dict:
    prior = archive_published(now_utc)
    PUBLISHED_HTML.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(STAGING_HTML, PUBLISHED_HTML)
    if evidence.sha256_file(PUBLISHED_HTML) != gates["dashboard_sha256"]:
        fail("published copy does not match the approved digest — aborting")
    meta = {
        "published_utc": now_utc.isoformat(timespec="seconds"),
        "action": "publish",
        "quarter": qkey,
        "pipeline_run_utc": gates["run"]["completed_utc"],
        "source_commit": git["commit"],
        "dashboard_sha256": gates["dashboard_sha256"],
        "evidence_package": str((EVIDENCE_DIR / qkey).relative_to(REPO)),
        "evidence_generated_utc": gates["manifest"]["generated_utc"],
        "reviewer": gates["sign_off"]["reviewer"],
        "review_date": gates["sign_off"]["review_date"],
        "decision": gates["sign_off"]["decision"],
        "prior_archived_to": prior,
        "note": "",
    }
    PUBLISHED_META.write_text(json.dumps(meta, indent=2) + "\n",
                              encoding="utf-8")
    append_release_row(meta)
    return meta


def cmd_publish(args: argparse.Namespace) -> None:
    q = args.quarter
    run_tests()
    gates = verify_publish_gates(q)
    meta = do_publish(q, gates, evidence.git_info(),
                      dt.datetime.now(dt.timezone.utc))
    print(f"Published {q}: {PUBLISHED_HTML.relative_to(REPO)} "
          f"(sha256 {meta['dashboard_sha256'][:12]}…), approved by "
          f"{meta['reviewer']} on {meta['review_date']}, from pipeline run "
          f"{meta['pipeline_run_utc']}.")
    if meta["prior_archived_to"]:
        print(f"Prior release archived to {meta['prior_archived_to']}.")
    print(f"Release recorded in {RELEASES_CSV.relative_to(REPO)} and "
          f"{PUBLISHED_META.relative_to(REPO)} — commit both together with "
          f"the published dashboard and the archive.")


# --- rollback ---------------------------------------------------------------

def do_rollback(to_stamp: str | None, now_utc: dt.datetime) -> dict:
    stamps = sorted(p for p in DASH_ARCHIVE.iterdir()
                    if p.is_dir() and (p / "index.html").exists()) \
        if DASH_ARCHIVE.exists() else []
    if not stamps:
        fail(f"no archived release under {DASH_ARCHIVE} to roll back to")
    if to_stamp:
        src = DASH_ARCHIVE / to_stamp
        if not (src / "index.html").exists():
            fail(f"no archived release at {src} — available: "
                 f"{[p.name for p in stamps]}")
    else:
        src = stamps[-1]
    prior = archive_published(now_utc)
    restored = {}
    if (src / "release.json").exists():
        restored = json.loads((src / "release.json")
                              .read_text(encoding="utf-8"))
    shutil.copy2(src / "index.html", PUBLISHED_HTML)
    meta = {
        **restored,
        "published_utc": now_utc.isoformat(timespec="seconds"),
        "action": "rollback",
        "prior_archived_to": prior,
        "note": f"re-promoted archived release {src.name}"
                + (f" (originally published "
                   f"{restored['published_utc']})"
                   if restored.get("published_utc") else ""),
    }
    PUBLISHED_META.write_text(json.dumps(meta, indent=2) + "\n",
                              encoding="utf-8")
    append_release_row(meta)
    return meta


def cmd_rollback(args: argparse.Namespace) -> None:
    meta = do_rollback(args.to, dt.datetime.now(dt.timezone.utc))
    print(f"Rolled back: {meta['note']}; replaced copy archived to "
          f"{meta['prior_archived_to']}. Recorded in "
          f"{RELEASES_CSV.relative_to(REPO)} — commit the restored dashboard "
          f"and the archive.")


# --- entry ------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)
    st = sub.add_parser("stage", help="steps 1-6: pipeline, tests, staging "
                                      "dashboard, evidence package")
    st.add_argument("--quarter", required=True, help="release quarter, e.g. "
                                                     "2026Q2")
    st.add_argument("--start", default="2024Q2")
    st.add_argument("--end", default="2026Q2")
    st.add_argument("--skip-figi", action="store_true",
                    help="reuse the committed ticker cache")
    pb = sub.add_parser("publish", help="steps 8-9: verify all gates, "
                                        "promote staging, archive prior")
    pb.add_argument("--quarter", required=True)
    rb = sub.add_parser("rollback", help="re-promote an archived release")
    rb.add_argument("--to", default=None,
                    help="archive timestamp under dashboard/_archive/ "
                         "(default: newest)")
    args = ap.parse_args()
    q = getattr(args, "quarter", None)
    if q and not QKEY_RE.fullmatch(q):
        fail(f"--quarter {q!r} is not of the form YYYYQn")
    {"stage": cmd_stage, "publish": cmd_publish,
     "rollback": cmd_rollback}[args.command](args)


if __name__ == "__main__":
    main()
