"""
Unit tests for Canonical Truth Root (CTR) truth_router.
Tests: truth_path, append_jsonl, write_json (atomic), heartbeat/freshness, disabled no-op.

Run: python -m unittest tests.test_truth_router (from repo root)
Or: pytest tests/test_truth_router.py -v
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path


class TestTruthRouter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))
        self._prev_root = os.environ.get("STOCKBOT_TRUTH_ROOT")
        self._prev_enabled = os.environ.get("TRUTH_ROUTER_ENABLED")
        os.environ["STOCKBOT_TRUTH_ROOT"] = self.tmp
        os.environ["TRUTH_ROUTER_ENABLED"] = "1"

    def tearDown(self):
        if self._prev_root is not None:
            os.environ["STOCKBOT_TRUTH_ROOT"] = self._prev_root
        elif "STOCKBOT_TRUTH_ROOT" in os.environ:
            del os.environ["STOCKBOT_TRUTH_ROOT"]
        if self._prev_enabled is not None:
            os.environ["TRUTH_ROUTER_ENABLED"] = self._prev_enabled
        else:
            os.environ["TRUTH_ROUTER_ENABLED"] = "0"

    def test_truth_path(self):
        from src.infra.truth_router import truth_path
        p = truth_path("gates/expectancy.jsonl")
        self.assertIn(self.tmp, p)
        self.assertTrue("gates" in p and "expectancy.jsonl" in p)

    def test_append_jsonl_creates_file_and_heartbeat(self):
        from src.infra.truth_router import append_jsonl
        rec = {"ts": 0, "symbol": "TEST", "gate_outcome": "pass"}
        append_jsonl("gates/expectancy.jsonl", rec, expected_max_age_sec=300)
        gate_file = Path(self.tmp) / "gates" / "expectancy.jsonl"
        self.assertTrue(gate_file.exists())
        lines = gate_file.read_text().strip().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["symbol"], "TEST")
        heartbeat = Path(self.tmp) / "meta" / "last_write_heartbeat.json"
        self.assertTrue(heartbeat.exists())
        h = json.loads(heartbeat.read_text())
        self.assertIn("ts_epoch", h)
        self.assertEqual(h.get("stream"), "gates/expectancy.jsonl")

    def test_write_json_atomic(self):
        from src.infra.truth_router import write_json
        obj = {"a": 1, "b": "x"}
        write_json("telemetry/score_telemetry.json", obj, expected_max_age_sec=600)
        p = Path(self.tmp) / "telemetry" / "score_telemetry.json"
        self.assertTrue(p.exists())
        data = json.loads(p.read_text())
        self.assertEqual(data["a"], 1)
        self.assertEqual(data["b"], "x")

    def test_freshness_updated(self):
        from src.infra.truth_router import append_jsonl
        append_jsonl("health/signal_health.jsonl", {"ts": 0, "symbol": "S"}, expected_max_age_sec=600)
        freshness_file = Path(self.tmp) / "health" / "freshness.json"
        self.assertTrue(freshness_file.exists())
        data = json.loads(freshness_file.read_text())
        self.assertIn("streams", data)
        self.assertIn("health/signal_health.jsonl", data["streams"])


class TestTruthRouterDisabled(unittest.TestCase):
    def test_disabled_no_op(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))
        os.environ["STOCKBOT_TRUTH_ROOT"] = tmp
        os.environ["TRUTH_ROUTER_ENABLED"] = "0"
        try:
            from src.infra.truth_router import append_jsonl, write_json
            append_jsonl("gates/expectancy.jsonl", {"x": 1})
            write_json("telemetry/x.json", {"y": 2})
            self.assertFalse((Path(tmp) / "gates" / "expectancy.jsonl").exists())
            self.assertFalse((Path(tmp) / "telemetry" / "x.json").exists())
        finally:
            os.environ["TRUTH_ROUTER_ENABLED"] = "0"


if __name__ == "__main__":
    unittest.main()
