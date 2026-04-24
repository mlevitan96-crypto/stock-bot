"""Tests for SPI visibility gate (Alpaca entry hard lock)."""
from __future__ import annotations

import csv
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


class TestIntelligenceGate(unittest.TestCase):
    def test_fresh_row_allows(self):
        from src import intelligence_gate as ig

        ig._SPI_CACHE.clear()
        now = datetime.now(timezone.utc)
        fresh = (now - timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "spi.csv"
            with p.open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["symbol", "timestamp_utc"])
                w.writeheader()
                w.writerow({"symbol": "TEST", "timestamp_utc": fresh})
            os.environ["ALPACA_SPI_CSV"] = str(p)
            os.environ["ALPACA_SPI_VISIBILITY_GATE"] = "1"
            ok, detail = ig.spi_visibility_ok("TEST", max_age_minutes=15.0)
            self.assertTrue(ok, detail)

    def test_stale_row_denies(self):
        from src import intelligence_gate as ig

        ig._SPI_CACHE.clear()
        old = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat().replace("+00:00", "Z")
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "spi.csv"
            with p.open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["symbol", "timestamp_utc"])
                w.writeheader()
                w.writerow({"symbol": "STALE", "timestamp_utc": old})
            os.environ["ALPACA_SPI_CSV"] = str(p)
            ok, _ = ig.spi_visibility_ok("STALE", max_age_minutes=15.0)
            self.assertFalse(ok)

    def tearDown(self):
        os.environ.pop("ALPACA_SPI_CSV", None)


if __name__ == "__main__":
    unittest.main()
