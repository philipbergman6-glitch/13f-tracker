"""Offline tests for the shared OpenFIGI batching seam (src/figi.py).

figi.map_batch is the single place that talks to the mapping endpoint — both
figi.resolve and sectors.us_ticker_lookup go through it — so the batching,
job shape and 429 back-off are worth pinning down. No network: urlopen and
sleep are stubbed.

Run:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
import urllib.error
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import figi  # noqa: E402


class FakeResponse:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@contextmanager
def fake_openfigi(responder):
    """Stub urlopen with `responder(jobs) -> results`; record the jobs sent."""
    sent = []

    def urlopen(req, timeout=None):
        jobs = json.loads(req.data)
        sent.append(jobs)
        return FakeResponse(responder(jobs))

    with mock.patch.object(figi.urllib.request, "urlopen", urlopen), \
            mock.patch.object(figi.time, "sleep", lambda _s: None):
        yield sent


class FakeHTTPError(urllib.error.HTTPError):
    """An HTTPError carrying only what map_batch reads (.code).

    Skips HTTPError.__init__ on purpose: it buffers a response body in a temp
    file, and a raised-then-swallowed 429 would leave that file to be reaped
    by the collector, spraying ResourceWarnings through the test output.
    """

    def __init__(self, code: int, msg: str):
        Exception.__init__(self, code, msg)
        self.code, self.msg = code, msg
        self.hdrs, self.filename, self.fp = {}, figi.MAPPING_URL, None


def matched(jobs):
    """One match per job, ticker = last 3 chars of the CUSIP."""
    return [{"data": [{"ticker": j["idValue"][-3:], "name": "N",
                       "exchCode": "US", "securityType": "Common Stock"}]}
            for j in jobs]


class TestBestMatch(unittest.TestCase):
    def test_first_match_wins(self):
        result = {"data": [{"ticker": "AAA"}, {"ticker": "BBB"}]}
        self.assertEqual(figi.best_match(result)["ticker"], "AAA")

    def test_no_data_is_empty_dict(self):
        self.assertEqual(figi.best_match({"error": "No identifier found."}), {})
        self.assertEqual(figi.best_match({"data": []}), {})


class TestMapBatch(unittest.TestCase):
    def test_chunks_to_jobs_per_request(self):
        cusips = [f"C{i:07d}" for i in range(23)]
        with fake_openfigi(matched) as sent:
            batches = list(figi.map_batch(cusips))
        self.assertEqual([len(j) for j in sent], [10, 10, 3])
        self.assertEqual([len(b) for b in batches], [10, 10, 3])

    def test_pairs_each_cusip_with_its_result(self):
        cusips = ["C00000AAA", "C00000BBB"]
        with fake_openfigi(matched):
            pairs = [p for batch in figi.map_batch(cusips) for p in batch]
        self.assertEqual([c for c, _ in pairs], cusips)
        self.assertEqual([figi.best_match(r)["ticker"] for _, r in pairs],
                         ["AAA", "BBB"])

    def test_job_shape_and_optional_exch_code(self):
        with fake_openfigi(matched) as sent:
            list(figi.map_batch(["C00000AAA"]))
        self.assertEqual(sent[0], [{"idType": "ID_CUSIP",
                                    "idValue": "C00000AAA"}])
        with fake_openfigi(matched) as sent:
            list(figi.map_batch(["C00000AAA"], exch_code="US"))
        self.assertEqual(sent[0], [{"idType": "ID_CUSIP",
                                    "idValue": "C00000AAA", "exchCode": "US"}])

    def test_empty_input_makes_no_request(self):
        with fake_openfigi(matched) as sent:
            self.assertEqual(list(figi.map_batch([])), [])
        self.assertEqual(sent, [])

    def test_retries_on_429_then_succeeds(self):
        calls = {"n": 0}

        def flaky(req, timeout=None):
            calls["n"] += 1
            if calls["n"] < 3:
                raise FakeHTTPError(429, "Too Many")
            return FakeResponse(matched(json.loads(req.data)))

        with mock.patch.object(figi.urllib.request, "urlopen", flaky), \
                mock.patch.object(figi.time, "sleep", lambda _s: None):
            batches = list(figi.map_batch(["C00000AAA"]))
        self.assertEqual(calls["n"], 3)
        self.assertEqual(figi.best_match(batches[0][0][1])["ticker"], "AAA")

    def test_non_429_error_propagates(self):
        def boom(req, timeout=None):
            raise FakeHTTPError(500, "Server Error")

        with mock.patch.object(figi.urllib.request, "urlopen", boom), \
                mock.patch.object(figi.time, "sleep", lambda _s: None):
            with self.assertRaises(urllib.error.HTTPError):
                list(figi.map_batch(["C00000AAA"]))


class TestResolve(unittest.TestCase):
    """resolve() on top of map_batch: cache misses queried, hits and manual
    overrides left alone."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patch = mock.patch.object(figi, "CACHE_PATH",
                                  Path(self.tmp.name) / "cusip_ticker.csv")
        patch.start()
        self.addCleanup(patch.stop)

    def test_queries_only_misses_and_caches_them(self):
        figi.save_cache({"C00000HIT": {"cusip": "C00000HIT", "ticker": "HIT",
                                       "override": ""}})
        with fake_openfigi(matched) as sent, redirect_stdout(io.StringIO()):
            out = figi.resolve({"C00000HIT", "C00000AAA"}, today="2026-08-12")
        self.assertEqual([j["idValue"] for j in sent[0]], ["C00000AAA"])
        self.assertEqual(out, {"C00000HIT": "HIT", "C00000AAA": "AAA"})
        self.assertEqual(figi.load_cache()["C00000AAA"]["retrieved"],
                         "2026-08-12")

    def test_no_match_is_cached_with_its_error(self):
        def unmatched(jobs):
            return [{"error": "No identifier found."} for _ in jobs]

        with fake_openfigi(unmatched), redirect_stdout(io.StringIO()):
            out = figi.resolve({"C00000ZZZ"}, today="2026-08-12")
        self.assertEqual(out, {"C00000ZZZ": ""})
        self.assertEqual(figi.load_cache()["C00000ZZZ"]["status"],
                         "No identifier found.")

    def test_override_beats_figi_ticker(self):
        figi.save_cache({"C00000OLD": {"cusip": "C00000OLD", "ticker": "CHV",
                                       "override": "CVX"}})
        with fake_openfigi(matched) as sent:
            out = figi.resolve({"C00000OLD"}, today="2026-08-12")
        self.assertEqual(sent, [])
        self.assertEqual(out, {"C00000OLD": "CVX"})


if __name__ == "__main__":
    unittest.main()
