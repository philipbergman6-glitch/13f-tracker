"""Offline tests for amendment merge and cross-filer dedupe (src/build.py).

merge_quarter picks quarter-final filings (Form 13F Special Instruction 3);
dedupe_filers drops a filer whose book is row-identical to an earlier-listed
filer's (the Situational Awareness LP / Partners LP 2026Q1 double-count).

Run:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import build  # noqa: E402
from edgar import Filing, ParsedFiling  # noqa: E402


def make_row(cusip="037833100", shares="100", value="1000", put_call=""):
    return {
        "issuer": "APPLE INC", "class": "COM", "cusip": cusip,
        "value_usd": value, "shares": shares, "sh_prn_type": "SH",
        "put_call": put_call, "discretion": "SOLE", "other_manager": "",
        "vote_sole": shares, "vote_shared": "0", "vote_none": "0",
    }


def make_parsed(cik=1, acc="0000000001-26-000001", fdate="2026-05-01",
                is_amendment=False, amendment_no=None, amendment_type=None,
                rows=None):
    return ParsedFiling(
        filing=Filing(cik, acc, "13F-HR/A" if is_amendment else "13F-HR",
                      fdate, "2026-03-31"),
        report_type="13F HOLDINGS REPORT",
        is_amendment=is_amendment,
        amendment_no=amendment_no,
        amendment_type=amendment_type,
        table_entry_total=len(rows or []),
        table_value_total=None,
        rows=rows if rows is not None else [make_row()],
    )


class FlagCapture(unittest.TestCase):
    """Run each test with a clean flag list and captured stderr."""

    def setUp(self):
        self._saved_flags = build._flags[:]
        build._flags.clear()
        self._stderr = redirect_stderr(io.StringIO())
        self._stderr.__enter__()

    def tearDown(self):
        self._stderr.__exit__(None, None, None)
        build._flags[:] = self._saved_flags

    @property
    def flags(self):
        return build._flags


class TestMergeQuarter(FlagCapture):
    def test_original_only(self):
        p = make_parsed()
        self.assertEqual(build.merge_quarter(1, "2026Q1", [p]), [p])
        self.assertEqual(self.flags, [])

    def test_restatement_replaces_original(self):
        orig = make_parsed(acc="a1")
        restated = make_parsed(acc="a2", fdate="2026-06-01", is_amendment=True,
                               amendment_no=1, amendment_type="RESTATEMENT")
        self.assertEqual(build.merge_quarter(1, "2026Q1", [orig, restated]),
                         [restated])

    def test_new_holdings_appended_after_base(self):
        orig = make_parsed(acc="a1")
        add = make_parsed(acc="a2", fdate="2026-06-01", is_amendment=True,
                          amendment_no=1, amendment_type="NEW HOLDINGS")
        self.assertEqual(build.merge_quarter(1, "2026Q1", [orig, add]),
                         [orig, add])

    def test_new_holdings_before_restatement_dropped(self):
        orig = make_parsed(acc="a1")
        add1 = make_parsed(acc="a2", fdate="2026-05-10", is_amendment=True,
                           amendment_no=1, amendment_type="NEW HOLDINGS")
        restated = make_parsed(acc="a3", fdate="2026-06-01", is_amendment=True,
                               amendment_no=2, amendment_type="RESTATEMENT")
        add2 = make_parsed(acc="a4", fdate="2026-06-10", is_amendment=True,
                           amendment_no=3, amendment_type="NEW HOLDINGS")
        self.assertEqual(build.merge_quarter(1, "2026Q1",
                                             [orig, add1, restated, add2]),
                         [restated, add2])

    def test_unknown_amendment_type_flagged_and_excluded(self):
        orig = make_parsed(acc="a1")
        odd = make_parsed(acc="a2", fdate="2026-06-01", is_amendment=True,
                          amendment_no=1, amendment_type=None)
        self.assertEqual(build.merge_quarter(1, "2026Q1", [orig, odd]), [orig])
        self.assertEqual(len(self.flags), 1)
        self.assertIn("unknown amendmentType", self.flags[0]["problem"])

    def test_multiple_originals_flagged_latest_used(self):
        first = make_parsed(acc="a1", fdate="2026-05-01")
        second = make_parsed(acc="a2", fdate="2026-05-02")
        self.assertEqual(build.merge_quarter(1, "2026Q1", [first, second]),
                         [second])
        self.assertEqual(len(self.flags), 1)

    def test_no_base_filing_flagged_empty(self):
        add = make_parsed(acc="a1", is_amendment=True, amendment_no=1,
                          amendment_type="NEW HOLDINGS")
        self.assertEqual(build.merge_quarter(1, "2026Q1", [add]), [])
        self.assertEqual(len(self.flags), 1)


class TestDedupeFilers(FlagCapture):
    def test_identical_books_keep_first_listed_filer(self):
        rows = [make_row(), make_row(cusip="594918104", shares="50", value="900")]
        lp = make_parsed(cik=2045724, acc="a1", rows=[dict(r) for r in rows])
        partners = make_parsed(cik=2038540, acc="a2",
                               rows=[dict(r) for r in reversed(rows)])
        kept, dropped = build.dedupe_filers("Situational Awareness", "2026Q1",
                                            {2045724: [lp], 2038540: [partners]})
        self.assertEqual(list(kept), [2045724])
        self.assertEqual(list(dropped), [2038540])
        self.assertIn("identical to filer 2045724 acc a1", dropped[2038540])
        self.assertEqual(len(self.flags), 1)
        self.assertEqual(self.flags[0]["filer_cik"], 2038540)
        self.assertIn("identical to filer 2045724", self.flags[0]["problem"])

    def test_administrative_columns_ignored_by_signature(self):
        # Situational Awareness 2026Q1: economically identical books differing
        # only in voting-authority columns are still duplicates.
        r_a, r_b = make_row(), make_row()
        r_b["vote_sole"], r_b["vote_none"] = "0", r_a["shares"]
        a = make_parsed(cik=1, acc="a1", rows=[r_a])
        b = make_parsed(cik=2, acc="a2", rows=[r_b])
        kept, dropped = build.dedupe_filers("m", "2026Q1", {1: [a], 2: [b]})
        self.assertEqual(list(kept), [1])
        self.assertEqual(list(dropped), [2])
        self.assertEqual(len(self.flags), 1)

    def test_differing_books_both_kept(self):
        a = make_parsed(cik=1, acc="a1", rows=[make_row(shares="100")])
        b = make_parsed(cik=2, acc="a2", rows=[make_row(shares="101")])
        kept, dropped = build.dedupe_filers("m", "2026Q1", {1: [a], 2: [b]})
        self.assertEqual(list(kept), [1, 2])
        self.assertEqual(dropped, {})
        self.assertEqual(self.flags, [])

    def test_identical_rows_across_multiple_filings_of_one_filer(self):
        # base + NEW HOLDINGS on one filer vs the same combined rows on another
        r1, r2 = make_row(), make_row(cusip="594918104")
        a = [make_parsed(cik=1, acc="a1", rows=[dict(r1)]),
             make_parsed(cik=1, acc="a2", rows=[dict(r2)])]
        b = [make_parsed(cik=2, acc="b1", rows=[dict(r1), dict(r2)])]
        kept, dropped = build.dedupe_filers("m", "2026Q1", {1: a, 2: b})
        self.assertEqual(list(kept), [1])
        self.assertIn("acc a1+a2", dropped[2])

    def test_empty_books_never_treated_as_duplicates(self):
        a = make_parsed(cik=1, acc="a1", rows=[])
        b = make_parsed(cik=2, acc="a2", rows=[])
        kept, dropped = build.dedupe_filers("m", "2026Q1", {1: [a], 2: [b]})
        self.assertEqual(list(kept), [1, 2])
        self.assertEqual(dropped, {})
        self.assertEqual(self.flags, [])


if __name__ == "__main__":
    unittest.main()
