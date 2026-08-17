"""Offline tests for the release orchestrator (src/release.py).

Publish-gate logic, promotion and rollback only — no network, no pipeline;
git checks run against throwaway repos. Every block condition trips.

Run:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import evidence  # noqa: E402
import release  # noqa: E402

QK = "2026Q2"
RUN_UTC = "2026-08-17T16:40:48+00:00"
NOW = dt.datetime(2026, 8, 17, 18, 0, tzinfo=dt.timezone.utc)
GIT = {"commit": "abc123", "commit_date": "2026-08-17T18:00:00+00:00"}

SIGNED = ("- Reviewer name: Philip\n"
          "- Review date (YYYY-MM-DD): 2026-08-17\n"
          "- Decision (approve / reject, with notes): approve — reviewed\n")


def write_csvf(path: Path, rows: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


class ReleaseRepo(unittest.TestCase):
    """A publishable tmp repo: green run, staging dashboard, evidence package
    with matching checksums, clean statuses, signed + committed report."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self._saved = [(release, n, getattr(release, n)) for n in
                       ("REPO", "EVIDENCE_DIR", "STAGING_HTML",
                        "PUBLISHED_HTML", "PUBLISHED_META", "DASH_ARCHIVE",
                        "RELEASES_CSV", "STATUS_CSV")]
        self._saved.append((evidence, "RUN_STATUS_PATH",
                            evidence.RUN_STATUS_PATH))
        release.REPO = self.root
        release.EVIDENCE_DIR = self.root / "docs" / "evidence"
        release.STAGING_HTML = self.root / "dashboard" / "staging" / "index.html"
        release.PUBLISHED_HTML = self.root / "dashboard" / "index.html"
        release.PUBLISHED_META = self.root / "dashboard" / "release.json"
        release.DASH_ARCHIVE = self.root / "dashboard" / "_archive"
        release.RELEASES_CSV = self.root / "docs" / "releases.csv"
        release.STATUS_CSV = self.root / "data" / "holdings" / "filer_status.csv"
        evidence.RUN_STATUS_PATH = self.root / "data" / "out" / "run_status.json"
        self.pkg = release.EVIDENCE_DIR / QK
        self.populate()

    def tearDown(self):
        for mod, n, v in self._saved:
            setattr(mod, n, v)
        self._tmp.cleanup()

    def git(self, *args: str) -> None:
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t",
                        *args], cwd=self.root, check=True,
                       capture_output=True)

    def write_run_status(self, ok=True, completed=RUN_UTC):
        evidence.RUN_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
        evidence.RUN_STATUS_PATH.write_text(json.dumps(
            {"ok": ok, "completed_utc": completed, "blocked": [],
             "validation_errors": 0 if ok else 2}), encoding="utf-8")

    def write_manifest(self, quarter=QK, run_utc=RUN_UTC):
        self.pkg.mkdir(parents=True, exist_ok=True)
        (self.pkg / "manifest.json").write_text(json.dumps(
            {"release_quarter": quarter, "generated_utc": "2026-08-17T17:00:00+00:00",
             "pipeline_run": {"completed_utc": run_utc}}), encoding="utf-8")

    def write_checksums(self):
        rows = [{"path": rel, "sha256": evidence.sha256_file(self.root / rel)}
                for rel in ("dashboard/staging/index.html",
                            "data/holdings/m/2026Q2.csv")]
        write_csvf(self.pkg / "checksums.csv", rows, ["path", "sha256"])

    def write_report(self, sign_off=SIGNED):
        self.pkg.mkdir(parents=True, exist_ok=True)
        (self.pkg / "report.md").write_text(
            "# Evidence\n\n## Reviewer sign-off\n\n" + sign_off,
            encoding="utf-8")

    def populate(self):
        self.write_run_status()
        release.STAGING_HTML.parent.mkdir(parents=True, exist_ok=True)
        release.STAGING_HTML.write_text(
            '<html>{"as_of":"2026Q2"}</html>', encoding="utf-8")
        release.PUBLISHED_HTML.write_text(
            '<html>prior release</html>', encoding="utf-8")
        holdings = self.root / "data" / "holdings" / "m" / "2026Q2.csv"
        holdings.parent.mkdir(parents=True, exist_ok=True)
        holdings.write_text("cusip,shares\nX,1\n", encoding="utf-8")
        write_csvf(release.STATUS_CSV, [
            {"quarter": QK, "manager": "M", "filer_cik": "1",
             "filer_name": "M LP", "status": "HOLDINGS", "form": "13F-HR",
             "accession": "a-1", "filing_date": "2026-08-01", "detail": "d"},
        ], ["quarter", "manager", "filer_cik", "filer_name", "status",
            "form", "accession", "filing_date", "detail"])
        self.write_manifest()
        self.write_checksums()
        write_csvf(self.pkg / "filings.csv", [
            {"quarter": QK, "manager": "M", "accession": "a-1",
             "retrieved_date": "2026-08-17",
             "filing_url": "https://www.sec.gov/x"},
        ], ["quarter", "manager", "accession", "retrieved_date",
            "filing_url"])
        self.write_report()
        self.git("init", "-q")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "fixture")

    def assertBlocks(self, fragment: str):
        with self.assertRaises(SystemExit) as ctx:
            release.verify_publish_gates(QK)
        self.assertIn(fragment, str(ctx.exception))
        return ctx.exception


class TestPublishGates(ReleaseRepo):
    def test_all_gates_pass(self):
        gates = release.verify_publish_gates(QK)
        self.assertEqual(gates["sign_off"]["reviewer"], "Philip")
        self.assertEqual(gates["run"]["completed_utc"], RUN_UTC)
        self.assertTrue(gates["dashboard_sha256"])

    def test_failed_pipeline_run_blocks(self):
        self.write_run_status(ok=False)
        self.assertBlocks("FAILED")

    def test_missing_staging_blocks(self):
        release.STAGING_HTML.unlink()
        self.assertBlocks("missing")

    def test_staging_wrong_quarter_blocks(self):
        release.STAGING_HTML.write_text('{"as_of":"2026Q1"}',
                                        encoding="utf-8")
        self.assertBlocks("as of 2026Q1, not 2026Q2")

    def test_missing_evidence_package_blocks(self):
        (self.pkg / "manifest.json").unlink()
        self.assertBlocks("no evidence package")

    def test_stale_evidence_package_blocks(self):
        self.write_run_status(completed="2026-08-18T00:00:00+00:00")
        self.assertBlocks("stale")

    def test_wrong_quarter_manifest_blocks(self):
        self.write_manifest(quarter="2026Q1")
        self.assertBlocks("declares release quarter 2026Q1")

    def test_late_filer_status_blocks(self):
        rows = release.read_csv(release.STATUS_CSV)
        rows[0]["status"] = "LATE"
        write_csvf(release.STATUS_CSV, rows, list(rows[0]))
        self.assertBlocks("unexplained filer status")

    def test_error_filer_status_blocks(self):
        rows = release.read_csv(release.STATUS_CSV)
        rows[0]["status"] = "ERROR"
        write_csvf(release.STATUS_CSV, rows, list(rows[0]))
        self.assertBlocks("unexplained filer status")

    def test_missing_provenance_blocks(self):
        rows = release.read_csv(self.pkg / "filings.csv")
        rows[0]["retrieved_date"] = ""
        write_csvf(self.pkg / "filings.csv", rows, list(rows[0]))
        self.assertBlocks("provenance missing")

    def test_tampered_artifact_blocks(self):
        (self.root / "data" / "holdings" / "m" / "2026Q2.csv").write_text(
            "cusip,shares\nX,2\n", encoding="utf-8")
        self.assertBlocks("digest mismatch")

    def test_missing_artifact_blocks(self):
        (self.root / "data" / "holdings" / "m" / "2026Q2.csv").unlink()
        self.assertBlocks("missing")

    def test_dashboard_not_checksummed_blocks(self):
        write_csvf(self.pkg / "checksums.csv",
                   [{"path": "data/holdings/m/2026Q2.csv",
                     "sha256": evidence.sha256_file(
                         self.root / "data/holdings/m/2026Q2.csv")}],
                   ["path", "sha256"])
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "x")
        self.assertBlocks("not among the package checksums")


class TestSignOffGate(ReleaseRepo):
    def recommit_report(self, sign_off):
        self.write_report(sign_off)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "report")

    def test_template_blanks_block(self):
        # The exact lines evidence.py writes must parse as blank — guards
        # against the template and the gate regexes drifting apart.
        self.recommit_report("\n".join(evidence.SIGN_OFF_LINES) + "\n")
        self.assertBlocks("blank")

    def test_reject_decision_blocks(self):
        self.recommit_report(SIGNED.replace("approve — reviewed",
                                            "reject — bad data"))
        self.assertBlocks("not an approval")

    def test_bad_review_date_blocks(self):
        self.recommit_report(SIGNED.replace("2026-08-17", "17 Aug 2026"))
        self.assertBlocks("not YYYY-MM-DD")

    def test_missing_sign_off_line_blocks(self):
        self.recommit_report("- Reviewer name: Philip\n")
        self.assertBlocks("missing")

    def test_uncommitted_sign_off_blocks(self):
        self.write_report(SIGNED + "\nlate edit\n")  # dirty vs fixture commit
        self.assertBlocks("uncommitted")


class TestPromoteAndRollback(ReleaseRepo):
    def publish(self):
        gates = release.verify_publish_gates(QK)
        return release.do_publish(QK, gates, GIT, NOW)

    def test_publish_promotes_archives_and_records(self):
        prior_bytes = release.PUBLISHED_HTML.read_bytes()
        meta = self.publish()
        self.assertEqual(release.PUBLISHED_HTML.read_bytes(),
                         release.STAGING_HTML.read_bytes())
        archived = self.root / meta["prior_archived_to"]
        self.assertEqual((archived / "index.html").read_bytes(), prior_bytes)
        pre = json.loads((archived / "release.json")
                         .read_text(encoding="utf-8"))
        self.assertIn("before release governance", pre["note"])
        rows = release.read_csv(release.RELEASES_CSV)
        self.assertEqual((rows[-1]["action"], rows[-1]["quarter"],
                          rows[-1]["reviewer"], rows[-1]["pipeline_run_utc"]),
                         ("publish", QK, "Philip", RUN_UTC))
        live = json.loads(release.PUBLISHED_META.read_text(encoding="utf-8"))
        self.assertEqual(live["dashboard_sha256"], meta["dashboard_sha256"])

    def test_first_publish_without_prior(self):
        release.PUBLISHED_HTML.unlink()
        meta = self.publish()
        self.assertEqual(meta["prior_archived_to"], None)
        self.assertTrue(release.PUBLISHED_HTML.exists())

    def test_rollback_restores_prior_and_archives_current(self):
        prior_bytes = release.PUBLISHED_HTML.read_bytes()
        published = self.publish()
        meta = release.do_rollback(
            None, NOW + dt.timedelta(seconds=5))
        self.assertEqual(release.PUBLISHED_HTML.read_bytes(), prior_bytes)
        # the rolled-back-from copy is retained, and the original archive too
        rolled_from = self.root / meta["prior_archived_to"]
        self.assertEqual((rolled_from / "index.html").read_bytes(),
                         release.STAGING_HTML.read_bytes())
        self.assertTrue((self.root / published["prior_archived_to"]
                         / "index.html").exists())
        rows = release.read_csv(release.RELEASES_CSV)
        self.assertEqual(rows[-1]["action"], "rollback")
        self.assertIn("re-promoted", rows[-1]["note"])

    def test_rollback_to_named_stamp(self):
        published = self.publish()
        stamp = Path(published["prior_archived_to"]).name
        release.do_rollback(stamp, NOW + dt.timedelta(seconds=5))
        self.assertEqual(release.PUBLISHED_HTML.read_text(encoding="utf-8"),
                         '<html>prior release</html>')

    def test_rollback_with_nothing_archived_fails(self):
        with self.assertRaises(SystemExit) as ctx:
            release.do_rollback(None, NOW)
        self.assertIn("no archived release", str(ctx.exception))

    def test_rollback_to_unknown_stamp_fails(self):
        self.publish()
        with self.assertRaises(SystemExit) as ctx:
            release.do_rollback("19700101T000000Z",
                                NOW + dt.timedelta(seconds=5))
        self.assertIn("no archived release at", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
