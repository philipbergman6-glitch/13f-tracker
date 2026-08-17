"""Unit tests for the dashboard's pure data-shaping functions (src/dashboard.py).

Run:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import dashboard as db  # noqa: E402


def book(*positions):
    """positions: (cusip, ticker, issuer, shares, value)."""
    return {c: {"cusip": c, "ticker": t, "issuer": i, "shares": s, "value": v}
            for c, t, i, s, v in positions}


class TestFormatting(unittest.TestCase):
    def test_fmt_usd_scales(self):
        self.assertEqual(db.fmt_usd(323_779_000_000), "$323.8bn")
        self.assertEqual(db.fmt_usd(2_646_532_635), "$2.65bn")
        self.assertEqual(db.fmt_usd(498_992_850), "$499.0m")
        self.assertEqual(db.fmt_usd(1_500_000), "$1.5m")
        self.assertEqual(db.fmt_usd(12_340), "$12,340")
        self.assertEqual(db.fmt_usd(0), "$0")

    def test_fmt_usd_negative(self):
        self.assertEqual(db.fmt_usd(-2_646_532_635), "-$2.65bn")

    def test_fmt_pct(self):
        self.assertEqual(db.fmt_pct(3.456), "3.5%")
        self.assertEqual(db.fmt_pct(-12.04), "-12.0%")
        self.assertEqual(db.fmt_pct(0.04), "0.0%")

    def test_fmt_signed_pct(self):
        self.assertEqual(db.fmt_signed_pct(3.456), "+3.5%")
        self.assertEqual(db.fmt_signed_pct(-3.456), "-3.5%")


class TestManagerStats(unittest.TestCase):
    def setUp(self):
        self.cur = book(("C1", "AAA", "Alpha Inc", 100, 600),
                        ("C2", "BBB", "Beta Corp", 50, 300),
                        ("C3", "CCC", "Gamma Ltd", 10, 100))
        self.prev = book(("C1", "AAA", "Alpha Inc", 100, 500),
                         ("C2", "BBB", "Beta Corp", 60, 300))

    def test_totals_and_counts(self):
        s = db.build_manager_stats(self.cur, self.prev)
        self.assertEqual(s["value"], 1000)
        self.assertEqual(s["value_prev"], 800)
        self.assertEqual(s["n_positions"], 3)
        self.assertAlmostEqual(s["qoq_pct"], 25.0)

    def test_top10_concentration(self):
        s = db.build_manager_stats(self.cur, self.prev)
        self.assertAlmostEqual(s["top10_pct"], 100.0)  # only 3 positions
        big = book(*[(f"C{i}", f"T{i}", f"Issuer {i}", 1, 10) for i in range(20)])
        s2 = db.build_manager_stats(big, {})
        self.assertAlmostEqual(s2["top10_pct"], 50.0)

    def test_no_prev_quarter(self):
        s = db.build_manager_stats(self.cur, {})
        self.assertIsNone(s["qoq_pct"])


class TestTopPositions(unittest.TestCase):
    def test_sorted_with_weights(self):
        b = book(("C1", "AAA", "Alpha", 1, 250), ("C2", "BBB", "Beta", 1, 750))
        top = db.top_positions(b, n=15)
        self.assertEqual([p["ticker"] for p in top], ["BBB", "AAA"])
        self.assertAlmostEqual(top[0]["weight_pct"], 75.0)

    def test_truncates_to_n(self):
        b = book(*[(f"C{i}", f"T{i}", f"I{i}", 1, 100 - i) for i in range(30)])
        self.assertEqual(len(db.top_positions(b, n=15)), 15)


class TestSectorMix(unittest.TestCase):
    def test_rollup_and_other_fold(self):
        b = book(*[(f"C{i}", f"T{i}", f"I{i}", 1, v) for i, v in
                   enumerate([400, 300, 100, 80, 60, 30, 20, 10])])
        sectors = {f"C{i}": s for i, s in enumerate(
            ["Tech", "Tech", "Health", "Energy", "Financials",
             "Utilities", "Materials", "Staples"])}
        mix = db.sector_mix(b, sectors, top_n=3)
        self.assertEqual(mix[0]["sector"], "Tech")
        self.assertEqual(mix[0]["value"], 700)
        self.assertAlmostEqual(mix[0]["weight_pct"], 70.0)
        self.assertEqual(mix[-1]["sector"], "Other")
        self.assertEqual(mix[-1]["value"], 60 + 30 + 20 + 10)
        self.assertEqual(len(mix), 4)  # top 3 + Other

    def test_missing_cusip_is_unclassified(self):
        b = book(("C1", "AAA", "Alpha", 1, 100))
        mix = db.sector_mix(b, {}, top_n=6)
        self.assertEqual(mix[0]["sector"], "Unclassified")

    def test_weights_sum_to_100(self):
        b = book(*[(f"C{i}", f"T{i}", f"I{i}", 1, v) for i, v in
                   enumerate([1, 2, 3, 4, 5, 6, 7, 8, 9])])
        mix = db.sector_mix(b, {f"C{i}": f"S{i}" for i in range(9)}, top_n=6)
        self.assertAlmostEqual(sum(m["weight_pct"] for m in mix), 100.0, places=6)


def chg(ticker, action, value=0, issuer=None, delta_weight=1.0):
    return {"cusip": ticker, "ticker": ticker, "issuer": issuer or ticker,
            "action": action, "value_cur_usd": str(value),
            "delta_weight_pp": f"{delta_weight:.2f}",
            "pct_change_shares": "", "shares_prev": "0", "shares_cur": "1"}


class TestConsensus(unittest.TestCase):
    def test_groups_buys_and_sells_by_ticker(self):
        by_mgr = {
            "M1": [chg("NVDA", "new", 100)],
            "M2": [chg("NVDA", "add", 200)],
            "M3": [chg("NVDA", "add", 300), chg("XOM", "exit")],
            "M4": [chg("XOM", "trim"), chg("NVDA", "exit")],
            "M5": [chg("XOM", "exit")],
        }
        c = db.consensus(by_mgr, min_count=3)
        self.assertEqual(len(c["buys"]), 1)
        self.assertEqual(c["buys"][0]["ticker"], "NVDA")
        self.assertEqual(c["buys"][0]["n_managers"], 3)
        self.assertEqual(len(c["sells"]), 1)
        self.assertEqual(c["sells"][0]["ticker"], "XOM")
        self.assertEqual(c["sells"][0]["n_managers"], 3)

    def test_below_threshold_excluded(self):
        by_mgr = {"M1": [chg("AAPL", "new")], "M2": [chg("AAPL", "add")]}
        c = db.consensus(by_mgr, min_count=3)
        self.assertEqual(c["buys"], [])

    def test_same_manager_counted_once(self):
        by_mgr = {"M1": [chg("AAPL", "new"), chg("AAPL", "add")],
                  "M2": [chg("AAPL", "add")], "M3": [chg("AAPL", "add")]}
        c = db.consensus(by_mgr, min_count=3)
        self.assertEqual(c["buys"][0]["n_managers"], 3)

    def test_sorted_by_manager_count_desc(self):
        by_mgr = {f"M{i}": [chg("AAPL", "add"), chg("MSFT", "add")]
                  for i in range(4)}
        by_mgr["M9"] = [chg("MSFT", "add")]
        c = db.consensus(by_mgr, min_count=3)
        self.assertEqual(c["buys"][0]["ticker"], "MSFT")  # 5 > 4

    def test_no_ticker_falls_back_to_cusip_grouping(self):
        rows = [dict(chg("", "new"), cusip="912828XX", issuer="T-Bond")
                for _ in range(3)]
        by_mgr = {f"M{i}": [dict(r) for r in rows] for i in range(3)}
        c = db.consensus(by_mgr, min_count=3)
        self.assertEqual(c["buys"][0]["n_managers"], 3)


class TestTakeaways(unittest.TestCase):
    def setUp(self):
        self.stats = {"value": 34_100_000_000, "value_prev": 30_300_000_000,
                      "qoq_pct": 12.5, "n_positions": 199, "top10_pct": 61.2}
        self.mix = [{"sector": "Information Technology", "value": 20_000_000_000,
                     "weight_pct": 58.7}]

    def test_two_to_three_sentences_with_traced_numbers(self):
        changes = [chg("NVDA", "new", 1_200_000_000, "NVIDIA CORP", 3.4),
                   chg("ABC", "exit", 0, "AmerisourceBergen")]
        out = db.takeaways("Coatue", "2026Q1", "2025Q4", self.stats,
                           changes, self.mix)
        self.assertTrue(2 <= len(out) <= 3, out)
        text = " ".join(out)
        self.assertIn("$34.1bn", text)
        self.assertIn("199", text)
        self.assertIn("+12.5%", text)
        self.assertIn("NVDA", text)
        self.assertIn("$1.2bn", text)
        self.assertIn("Information Technology", text)

    def test_no_changes_quarter(self):
        out = db.takeaways("Fairholme", "2026Q1", "2025Q4", self.stats, [],
                           self.mix)
        text = " ".join(out)
        self.assertIn("No significant changes", text)

    def test_first_tracked_quarter(self):
        stats = dict(self.stats, qoq_pct=None, value_prev=None)
        out = db.takeaways("SA", "2024Q4", None, stats, [], self.mix)
        self.assertTrue(2 <= len(out) <= 3)
        self.assertNotIn("None", " ".join(out))


class TestQuarterSelection(unittest.TestCase):
    def test_as_of_quarter_is_latest_majority(self):
        latest = {"a": "2026Q1", "b": "2026Q1", "c": "2026Q2"}
        self.assertEqual(db.as_of_quarter(latest), "2026Q1")

    def test_unanimous(self):
        latest = {"a": "2026Q2", "b": "2026Q2"}
        self.assertEqual(db.as_of_quarter(latest), "2026Q2")


class TestPinnedQuarter(unittest.TestCase):
    """--quarter pins the as-of date: no card may show a book from after it.

    Uses the committed holdings CSVs. situational-awareness is first tracked in
    2024Q4, so a 2024Q3 pin leaves it with no book as of that date.
    """
    PIN = "2024Q3"

    @classmethod
    def setUpClass(cls):
        cls.payload = db.build_payload(cls.PIN)

    def test_no_manager_shown_later_than_the_pin(self):
        later = {m["manager"]: m["quarter"] for m in self.payload["managers"]
                 if m["quarter"] > self.PIN}
        self.assertEqual(later, {})

    def test_manager_with_no_book_as_of_the_pin_is_omitted(self):
        shown = {m["manager"] for m in self.payload["managers"]}
        self.assertNotIn("Situational Awareness", shown)

    def test_consensus_pools_only_changes_from_at_or_before_the_pin(self):
        """A consensus row must not count a change filed after the as-of date."""
        quarter_of = {m["manager"]: m["quarter"] for m in self.payload["managers"]}
        credited = {a["manager"]
                    for side in self.payload["consensus"].values()
                    for row in side for a in row["managers"]}
        from_after_pin = {m: quarter_of.get(m) for m in credited
                          if quarter_of.get(m, self.PIN) > self.PIN}
        self.assertEqual(from_after_pin, {})
        self.assertEqual(credited - set(quarter_of), set())


class TestRunStatusGate(unittest.TestCase):
    """A failed pipeline run must never overwrite the approved dashboard."""

    def check(self, content: str | None):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run_status.json"
            if content is not None:
                path.write_text(content, encoding="utf-8")
            db.check_run_status(path)

    def test_missing_run_status_refuses(self):
        with self.assertRaisesRegex(SystemExit, "run src/pipeline.py first"):
            self.check(None)

    def test_failed_run_refuses(self):
        with self.assertRaisesRegex(SystemExit, "FAILED"):
            self.check('{"ok": false, "blocked": ["Mgr 2026Q2"], '
                       '"validation_errors": 1}')

    def test_ok_run_passes(self):
        self.check('{"ok": true, "blocked": [], "validation_errors": 0}')


if __name__ == "__main__":
    unittest.main()
