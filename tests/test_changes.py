"""Tests for corporate-action-aware quarter-over-quarter changes."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import changes  # noqa: E402


def position(shares: int, value: int) -> dict:
    return {"shares": shares, "value": value, "issuer": "Booking Holdings",
            "ticker": "BKNG", "cls": "COM"}


class TestCorporateActionAdjustedClassification(unittest.TestCase):
    def test_split_does_not_create_a_false_add(self):
        prev = {"09857L108": position(21_117, 88_909_327)}
        cur = {"09857L108": position(522_664, 93_159_631)}

        rows = changes.classify(
            prev, cur, share_multipliers={"09857L108": 25})

        self.assertEqual(rows, [])

    def test_real_add_after_split_uses_comparable_prior_shares(self):
        prev = {"C1": position(100, 1_000)}
        cur = {"C1": position(1_500, 15_000)}

        rows = changes.classify(prev, cur, share_multipliers={"C1": 10})

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["action"], "add")
        self.assertEqual(rows[0]["shares_prev"], 1_000)
        self.assertEqual(rows[0]["shares_prev_reported"], 100)
        self.assertEqual(rows[0]["delta_shares"], 500)
        self.assertEqual(rows[0]["pct_change_shares"], "50.0")
        self.assertEqual(rows[0]["share_multiplier"], 10)

    def test_loads_only_actions_effective_for_comparison_quarter(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "corporate_actions.csv"
            path.write_text(
                "cusip,effective_quarter,share_multiplier,description,source_url,retrieved_date\n"
                "NFLX,2025Q4,10,10-for-1 forward split,https://example/nflx,2026-08-17\n"
                "BKNG,2026Q2,25,25-for-1 forward split,https://example/bkng,2026-08-17\n",
                encoding="utf-8")

            self.assertEqual(
                changes.load_share_multipliers("2025Q4", path), {"NFLX": 10})

    def test_multiplier_is_not_claimed_when_no_comparison_was_possible(self):
        prev = {"C1": position(100, 1_000)}

        [row] = changes.classify(
            prev, {}, share_multipliers={"C1": 10})

        self.assertEqual(row["action"], "exit")
        self.assertEqual(row["shares_prev"], 100)
        self.assertEqual(row["share_multiplier"], 1)


class TestIdentifierAliasClassification(unittest.TestCase):
    def test_filer_cusip_typo_does_not_create_false_exit_and_new(self):
        prev = {"H2927K103": position(880_000, 42_706_400)}
        cur = {"H2627K103": position(880_000, 49_297_600)}

        rows = changes.classify(
            prev, cur, security_aliases={"H2627K103": "H2927K103"})

        self.assertEqual(rows, [])

    def test_loads_committed_security_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "security_aliases.csv"
            path.write_text(
                "reported_cusip,canonical_cusip,description,source_url,retrieved_date\n"
                "H2627K103,H2927K103,Filer typo,https://example/amrize,2026-08-17\n",
                encoding="utf-8")

            self.assertEqual(changes.load_security_aliases(path),
                             {"H2627K103": "H2927K103"})


if __name__ == "__main__":
    unittest.main()
