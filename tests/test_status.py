"""Offline tests for the per-filer quarterly status model (src/status.py).

Every (manager, filer, quarter) must classify into exactly one explicit status;
the Pershing Square 2026Q2 case (LP files 13F-NT, Inc. files the combined
13F-HR) must come out NT, never LATE.

Run:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import datetime
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import status  # noqa: E402
from common import FilerSpan  # noqa: E402
from edgar import Filing, ParsedFiling  # noqa: E402


SPAN = FilerSpan(manager="Pershing Square", cik=1336528,
                 filer_name="Pershing Square Capital Management, L.P.",
                 from_quarter=None, to_quarter=None)


def make_parsed(acc="0000000001-26-000001", form="13F-HR", fdate="2026-08-10",
                n_rows=2):
    return ParsedFiling(
        filing=Filing(1336528, acc, form, fdate, "2026-06-30"),
        report_type="13F HOLDINGS REPORT", is_amendment=False,
        amendment_no=None, amendment_type=None,
        table_entry_total=n_rows, table_value_total=None,
        rows=[{"cusip": "037833100"}] * n_rows,
    )


def classify(merged=(), hr_filings=(), nt_filings=(), fetch_errors=(),
             duplicate_detail=None, today=datetime.date(2026, 8, 17)):
    return status.classify(SPAN, "2026Q2", merged=list(merged),
                           hr_filings=list(hr_filings),
                           nt_filings=list(nt_filings),
                           fetch_errors=list(fetch_errors),
                           duplicate_detail=duplicate_detail, today=today)


class TestFilingDeadline(unittest.TestCase):
    def test_weekday_deadline_unmoved(self):
        # 2026Q2: Jun 30 + 45d = Fri 2026-08-14
        self.assertEqual(status.filing_deadline("2026Q2"),
                         datetime.date(2026, 8, 14))

    def test_weekend_deadline_rolls_to_monday(self):
        # 2027Q2: Jun 30 + 45d = Sat 2027-08-14 -> Mon 2027-08-16
        self.assertEqual(status.filing_deadline("2027Q2"),
                         datetime.date(2027, 8, 16))


class TestClassify(unittest.TestCase):
    def test_holdings(self):
        p = make_parsed()
        st = classify(merged=[p], hr_filings=[p])
        self.assertEqual(st.status, "HOLDINGS")
        self.assertEqual(st.accession, p.filing.accession)
        self.assertIn("2 rows", st.detail)

    def test_holdings_multiple_filings_joined(self):
        base, add = make_parsed(acc="a1"), make_parsed(acc="a2", fdate="2026-08-12")
        st = classify(merged=[base, add], hr_filings=[base, add])
        self.assertEqual(st.status, "HOLDINGS")
        self.assertEqual(st.accession, "a1+a2")
        self.assertEqual(st.filing_date, "2026-08-12")

    def test_nt_explains_absence(self):
        nt = Filing(1336528, "0000000001-26-000009", "13F-NT",
                    "2026-08-13", "2026-06-30")
        st = classify(nt_filings=[nt])
        self.assertEqual(st.status, "NT")
        self.assertEqual(st.accession, nt.accession)
        self.assertIn("another filer", st.detail)

    def test_duplicate_takes_precedence_over_holdings(self):
        p = make_parsed()
        st = classify(merged=[p], hr_filings=[p],
                      duplicate_detail="book identical to filer 42 acc x (2 rows)")
        self.assertEqual(st.status, "DUPLICATE")
        self.assertIn("filer 42", st.detail)

    def test_error_on_unusable_hr(self):
        p = make_parsed()
        st = classify(hr_filings=[p])  # merge produced no base
        self.assertEqual(st.status, "ERROR")
        self.assertIn("no usable base filing", st.detail)

    def test_error_on_fetch_failure(self):
        st = classify(fetch_errors=["13F-HR acc: URLError: timeout"])
        self.assertEqual(st.status, "ERROR")
        self.assertIn("timeout", st.detail)

    def test_not_due_before_deadline(self):
        st = classify(today=datetime.date(2026, 8, 14))
        self.assertEqual(st.status, "NOT_DUE")
        self.assertIn("2026-08-14", st.detail)

    def test_late_after_deadline(self):
        st = classify(today=datetime.date(2026, 8, 17))
        self.assertEqual(st.status, "LATE")
        self.assertIn(st.status, status.BLOCKING)
        self.assertIn("deadline was 2026-08-14", st.detail)


if __name__ == "__main__":
    unittest.main()
