"""Offline tests for the release evidence package (src/evidence.py).

Consolidation and gate logic only — no EDGAR, no subprocesses. Retrieval-date
lookups (raw-file mtimes) are stubbed per test.

Run:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import sys
import tempfile
import unittest
import datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import evidence  # noqa: E402
from common import FilerSpan  # noqa: E402


def make_verification(acc="0000000001-26-000001", cik="1", rows="10",
                      entry_total="10", rows_match="True", value="1000",
                      value_total="1000", value_match="True"):
    return {"filer_cik": cik, "accession": acc, "form": "13F-HR",
            "filing_date": "2026-05-01", "report_date": "2026-03-31",
            "rows_parsed": rows, "table_entry_total": entry_total,
            "rows_match": rows_match, "value_parsed_usd": value,
            "table_value_total": value_total, "value_match": value_match,
            "filing_url": f"https://www.sec.gov/x/{acc}"}


def make_decision(acc="0000000001-26-000001", cik="1", role="BASE_ORIGINAL"):
    return {"filer_cik": cik, "quarter": "2026Q1", "accession": acc,
            "form": "13F-HR", "filing_date": "2026-05-01", "role": role,
            "in_book": str(role in {"BASE_ORIGINAL", "BASE_RESTATEMENT",
                                    "NEW_HOLDINGS"}), "detail": "d"}


def make_status(status="HOLDINGS", acc="0000000001-26-000001", cik="1",
                quarter="2026Q1", form="13F-HR"):
    return {"quarter": quarter, "manager": "M", "filer_cik": cik,
            "filer_name": "M LP", "status": status, "form": form,
            "accession": acc, "filing_date": "2026-05-01", "detail": "d"}


SPAN = {"1": FilerSpan("M", 1, "M LP", None, None)}


class RetrievalStub(unittest.TestCase):
    def setUp(self):
        self._raw = evidence.raw_retrieved_date
        self._sub = evidence.submissions_retrieved_date
        evidence.raw_retrieved_date = lambda cik, acc: "2026-08-17"
        evidence.submissions_retrieved_date = lambda cik: "2026-08-17"

    def tearDown(self):
        evidence.raw_retrieved_date = self._raw
        evidence.submissions_retrieved_date = self._sub


class TestCollectFilings(RetrievalStub):
    def test_happy_path_joins_role_and_retrieval(self):
        rows = evidence.collect_filings(
            [make_verification()], [make_decision()], [make_status()], [], SPAN)
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual((r["quarter"], r["manager"], r["role"],
                          r["retrieved_date"], r["exception_id"]),
                         ("2026Q1", "M", "BASE_ORIGINAL", "2026-08-17", ""))

    def test_mismatch_without_exception_hard_fails(self):
        v = make_verification(value="999", value_match="False")
        with self.assertRaises(SystemExit) as ctx:
            evidence.collect_filings([v], [make_decision()], [make_status()],
                                     [], SPAN)
        self.assertIn("known_exceptions", str(ctx.exception))

    def test_mismatch_with_exception_annotated(self):
        v = make_verification(value="999", value_match="False")
        exc = {"id": "EXC-009", "accession": v["accession"]}
        rows = evidence.collect_filings([v], [make_decision()],
                                        [make_status()], [exc], SPAN)
        self.assertEqual(rows[0]["exception_id"], "EXC-009")

    def test_missing_merge_decision_hard_fails(self):
        with self.assertRaises(SystemExit) as ctx:
            evidence.collect_filings([make_verification()], [],
                                     [make_status()], [], SPAN)
        self.assertIn("no merge decision", str(ctx.exception))

    def test_unmapped_cik_hard_fails(self):
        with self.assertRaises(SystemExit):
            evidence.collect_filings([make_verification(cik="999")],
                                     [make_decision(cik="999")],
                                     [make_status(cik="999")], [], {})

    def test_nt_notice_included_with_index_retrieval_date(self):
        nt = make_status(status="NT", acc="0000000001-26-000009",
                         form="13F-NT")
        rows = evidence.collect_filings([], [], [nt], [], SPAN)
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual((r["role"], r["form"], r["report_date"],
                          r["retrieved_date"], r["rows_parsed"]),
                         ("NT_NOTICE", "13F-NT", "2026-03-31",
                          "2026-08-17", ""))
        self.assertIn("0000000001-26-000009-index.htm", r["filing_url"])


class TestEffectiveRoles(unittest.TestCase):
    def test_last_decision_wins(self):
        merged = make_decision(role="BASE_ORIGINAL")
        dup = make_decision(role="DUPLICATE_BOOK")
        roles = evidence.effective_roles([merged, dup])
        self.assertEqual(roles[merged["accession"]]["role"], "DUPLICATE_BOOK")


class TestStatusCoverage(RetrievalStub):
    def test_complete_coverage_passes(self):
        filings = evidence.collect_filings(
            [make_verification()], [make_decision()], [make_status()], [], SPAN)
        evidence.check_status_coverage([make_status()], filings,
                                       list(SPAN.values()), ["2026Q1"])

    def test_missing_status_row_hard_fails(self):
        with self.assertRaises(SystemExit) as ctx:
            evidence.check_status_coverage([], [], list(SPAN.values()),
                                           ["2026Q1"])
        self.assertIn("no filer_status row", str(ctx.exception))

    def test_status_accession_missing_from_filings_hard_fails(self):
        with self.assertRaises(SystemExit) as ctx:
            evidence.check_status_coverage([make_status()], [],
                                           list(SPAN.values()), ["2026Q1"])
        self.assertIn("missing from the verification", str(ctx.exception))

    def test_span_outside_quarter_not_required(self):
        span = {"1": FilerSpan("M", 1, "M LP", "2026Q2", None)}
        evidence.check_status_coverage([], [], list(span.values()), ["2026Q1"])


class TestArchiveExisting(unittest.TestCase):
    def test_superseded_package_archived_not_deleted(self):
        saved_ev, saved_repo = evidence.EVIDENCE_DIR, evidence.REPO
        with tempfile.TemporaryDirectory() as tmp:
            evidence.REPO = Path(tmp)
            evidence.EVIDENCE_DIR = Path(tmp) / "docs" / "evidence"
            try:
                pkg = evidence.EVIDENCE_DIR / "2026Q2"
                pkg.mkdir(parents=True)
                (pkg / "report.md").write_text("old", encoding="utf-8")
                now = dt.datetime(2026, 8, 17, 12, 0,
                                  tzinfo=dt.timezone.utc)
                rel = evidence.archive_existing(pkg, now)
                self.assertFalse(pkg.exists())
                archived = Path(tmp) / rel
                self.assertEqual((archived / "report.md").read_text(
                    encoding="utf-8"), "old")
                self.assertIn("_archive", rel)
                self.assertIsNone(evidence.archive_existing(pkg, now))
            finally:
                evidence.EVIDENCE_DIR, evidence.REPO = saved_ev, saved_repo


class TestReportHelpers(unittest.TestCase):
    def test_fmt_int(self):
        self.assertEqual(evidence._fmt_int("1234567"), "1,234,567")
        self.assertEqual(evidence._fmt_int(""), "—")
        self.assertEqual(evidence._fmt_int(None), "—")

    def test_md_table(self):
        t = evidence._md_table(["a", "b"], [[1, "x"]])
        self.assertEqual(t.splitlines(),
                         ["| a | b |", "|---|---|", "| 1 | x |"])

    def test_sha256_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "f"
            p.write_bytes(b"abc")
            self.assertEqual(
                evidence.sha256_file(p),
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61"
                "f20015ad")


if __name__ == "__main__":
    unittest.main()
