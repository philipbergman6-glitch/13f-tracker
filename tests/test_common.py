"""Offline tests for fetch_cached (src/common.py) mutable-index refresh.

Immutable artifacts cache forever; mutable indexes (SEC submissions JSON)
re-fetch unless retrieved today, archiving the superseded snapshot. No
network: http_get is stubbed.

Run:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import common  # noqa: E402

YESTERDAY = time.time() - 86400


class TestFetchCached(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.raw = Path(self._tmp.name)
        self._raw_patch = mock.patch.object(common, "RAW", self.raw)
        self._raw_patch.start()

    def tearDown(self):
        self._raw_patch.stop()
        self._tmp.cleanup()

    def write_cached(self, body: bytes, mtime: float | None = None) -> Path:
        dest = self.raw / "123" / "submissions.json"
        dest.parent.mkdir(parents=True)
        dest.write_bytes(body)
        if mtime is not None:
            os.utime(dest, (mtime, mtime))
        return dest

    def test_immutable_never_refetched(self):
        dest = self.write_cached(b"old", mtime=YESTERDAY)
        with mock.patch.object(common, "http_get") as get:
            self.assertEqual(common.fetch_cached("u", dest), dest)
        get.assert_not_called()
        self.assertEqual(dest.read_bytes(), b"old")

    def test_mutable_same_day_cache_reused(self):
        dest = self.write_cached(b"today")
        with mock.patch.object(common, "http_get") as get:
            common.fetch_cached("u", dest, mutable=True)
        get.assert_not_called()

    def test_mutable_stale_refetched_and_superseded_archived(self):
        dest = self.write_cached(b"old", mtime=YESTERDAY)
        with mock.patch.object(common, "http_get", return_value=b"new"):
            common.fetch_cached("u", dest, mutable=True)
        self.assertEqual(dest.read_bytes(), b"new")
        archived = list((self.raw / "_archive" / "superseded").rglob("submissions.json"))
        self.assertEqual(len(archived), 1)
        self.assertEqual(archived[0].read_bytes(), b"old")

    def test_mutable_stale_but_unchanged_restamped_not_archived(self):
        dest = self.write_cached(b"same", mtime=YESTERDAY)
        with mock.patch.object(common, "http_get", return_value=b"same"):
            common.fetch_cached("u", dest, mutable=True)
        self.assertEqual(dest.read_bytes(), b"same")
        self.assertFalse((self.raw / "_archive").exists())
        self.assertGreater(dest.stat().st_mtime, YESTERDAY + 1)

    def test_missing_file_downloaded(self):
        dest = self.raw / "123" / "submissions.json"
        with mock.patch.object(common, "http_get", return_value=b"body"):
            common.fetch_cached("u", dest, mutable=True)
        self.assertEqual(dest.read_bytes(), b"body")


if __name__ == "__main__":
    unittest.main()
