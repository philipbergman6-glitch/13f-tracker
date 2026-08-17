"""Offline tests for holdings validation (src/validate.py).

ERROR blocks publication; WARN is recorded only. Thresholds must keep the
committed 2024Q2-2026Q2 history ERROR-free (calibrated 2026-08-17): accepted
filings contain bad check digits, issuer renames and BRK-A prices, so those
are warnings, while malformed CUSIPs and unparseable numbers hard-fail.

Run:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import validate  # noqa: E402
from edgar import Filing, ParsedFiling  # noqa: E402


def make_row(**over):
    row = {"issuer": "APPLE INC", "class": "COM", "cusip": "037833100",
           "value_usd": "1000000", "shares": "5000", "sh_prn_type": "SH",
           "put_call": "", "discretion": "SOLE", "other_manager": "",
           "vote_sole": "5000", "vote_shared": "0", "vote_none": "0"}
    row.update(over)
    return row


def make_parsed(rows, cik=1, acc="0000000001-26-000001"):
    return ParsedFiling(
        filing=Filing(cik, acc, "13F-HR", "2026-08-14", "2026-06-30"),
        report_type="13F HOLDINGS REPORT", is_amendment=False,
        amendment_no=None, amendment_type=None,
        table_entry_total=len(rows), table_value_total=None, rows=rows)


def run_rows(rows):
    return validate.validate_rows("Mgr", "2026Q2", {1: [make_parsed(rows)]})


def levels(findings, check):
    return [f.level for f in findings if f.check == check]


class TestCusip(unittest.TestCase):
    def test_check_digit_valid(self):
        for cusip in ("037833100", "02079K107", "N07059210"):
            self.assertEqual(validate.cusip_check_digit(cusip), cusip[8], cusip)

    def test_known_bad_check_digit_is_warn_not_error(self):
        # SPDR institutional series 78462F953 is in accepted SEC filings
        f = run_rows([make_row(cusip="78462F953", issuer="SPDR S&P 500 ETF TR")])
        self.assertEqual(levels(f, "cusip-check-digit"), ["WARN"])
        self.assertEqual(levels(f, "cusip-format"), [])

    def test_malformed_cusip_is_error(self):
        for bad in ("03783310", "0378331000", "03783310!"):
            f = run_rows([make_row(cusip=bad)])
            self.assertEqual(levels(f, "cusip-format"), ["ERROR"], bad)


class TestFields(unittest.TestCase):
    def test_clean_row_no_findings(self):
        self.assertEqual(run_rows([make_row()]), [])

    def test_unparseable_value_is_error(self):
        f = run_rows([make_row(value_usd="N/A")])
        self.assertEqual(levels(f, "field"), ["ERROR"])

    def test_negative_shares_is_error(self):
        f = run_rows([make_row(shares="-5")])
        self.assertEqual(levels(f, "field"), ["ERROR"])

    def test_empty_issuer_is_error(self):
        f = run_rows([make_row(issuer=" ")])
        self.assertEqual(levels(f, "field"), ["ERROR"])

    def test_unknown_share_type_is_error(self):
        f = run_rows([make_row(sh_prn_type="XX")])
        self.assertEqual(levels(f, "share-type"), ["ERROR"])

    def test_put_call_variants_accepted(self):
        for pc in ("", "Put", "Call", "PUT", "call"):
            self.assertEqual(run_rows([make_row(put_call=pc)]), [], pc)

    def test_brk_a_price_within_bounds(self):
        f = run_rows([make_row(cusip="084670108", issuer="BERKSHIRE HATH",
                               value_usd="8302800", shares="11")])
        self.assertEqual(f, [])

    def test_absurd_price_is_warn(self):
        f = run_rows([make_row(value_usd="5000000000000", shares="1")])
        self.assertEqual(levels(f, "price-bounds"), ["WARN"])


class TestIdentity(unittest.TestCase):
    def test_cross_label_warns(self):
        # the observed Amazon CUSIP labelled Astera Labs (2026-08-17 calibration)
        merged = {(1, "2026Q2"): [make_parsed([make_row(cusip="023135106",
                                                        issuer="AMAZON COM INC")])],
                  (2, "2026Q2"): [make_parsed([make_row(cusip="023135106",
                                                        issuer="ASTERA LABS INC")],
                                              cik=2, acc="a2")]}
        f = validate.validate_identity(merged)
        self.assertEqual(levels(f, "identity"), ["WARN"])

    def test_spelling_drift_ignored(self):
        merged = {(1, "2026Q2"): [make_parsed([
            make_row(issuer="NVIDIA CORP", cusip="67066G104"),
            make_row(issuer="NVIDIA CORPORATION", cusip="67066G104")])]}
        self.assertEqual(validate.validate_identity(merged), [])


class TestTickers(unittest.TestCase):
    def test_normal_tickers_pass(self):
        self.assertEqual(validate.validate_tickers(
            {"a": "AAPL", "b": "BRK/A", "c": "", "d": "RDS.A",
             "e": "MASI*", "f": "GOOGL 6.25 05/15/29 A"}), [])

    def test_garbage_ticker_warns(self):
        f = validate.validate_tickers({"a": "<script>"})
        self.assertEqual(levels(f, "ticker-format"), ["WARN"])


class TestQoq(unittest.TestCase):
    def write_quarter(self, root, qkey, shares, value):
        d = root / "mgr"
        d.mkdir(exist_ok=True)
        cols = ("filer_cik,accession,cusip,ticker,issuer,class,put_call,"
                "value_usd,shares,sh_prn_type,discretion,other_manager,"
                "vote_sole,vote_shared,vote_none\n")
        (d / f"{qkey}.csv").write_text(
            cols + f"1,a,037833100,AAPL,APPLE INC,COM,,{value},{shares},SH,"
                   f"SOLE,,0,0,0\n", encoding="utf-8")

    def test_hundredfold_share_jump_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_quarter(root, "2026Q1", 100, 20000)
            self.write_quarter(root, "2026Q2", 200000, 40000000)
            f = validate.validate_qoq(root)
            self.assertEqual(levels(f, "qoq-shares"), ["WARN"])
            self.assertEqual(levels(f, "qoq-price"), [])

    def test_price_collapse_warns_units_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_quarter(root, "2026Q1", 1000, 200000)   # $200/sh
            self.write_quarter(root, "2026Q2", 1100, 11000)    # $10/sh
            f = validate.validate_qoq(root)
            self.assertEqual(levels(f, "qoq-price"), ["WARN"])

    def test_ordinary_movement_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_quarter(root, "2026Q1", 1000, 200000)
            self.write_quarter(root, "2026Q2", 3000, 630000)
            self.assertEqual(validate.validate_qoq(root), [])


class TestWriteCsv(unittest.TestCase):
    def test_errors_sort_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(validate, "OUT", Path(tmp)), \
                 mock.patch.object(validate, "VALIDATION_PATH",
                                   Path(tmp) / "validation.csv"):
                path = validate.write_validation_csv([
                    validate.Finding("WARN", "identity", "", "", "", "", "c1", "w"),
                    validate.Finding("ERROR", "field", "2026Q2", "Mgr", "1", "a",
                                     "c2", "e"),
                ])
                lines = Path(path).read_text(encoding="utf-8").splitlines()
                self.assertTrue(lines[1].startswith("ERROR"))


if __name__ == "__main__":
    unittest.main()
