"""Smoke test: decision-path truth harness exits 0 and writes test sink only."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


class TestDecisionPathHarness(unittest.TestCase):
    def test_harness_exits_zero(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        sink = repo / "logs" / "test_run.jsonl"
        if sink.exists():
            sink.unlink()
        r = subprocess.run(
            [sys.executable, str(repo / "scripts" / "audit" / "alpaca_decision_path_truth_test.py"), "--root", str(repo)],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr + r.stdout)
        data = None
        for line in r.stdout.splitlines():
            if line.startswith("SUMMARY_JSON:"):
                data = json.loads(line[len("SUMMARY_JSON:") :])
                break
        self.assertIsNotNone(data, msg=r.stdout)
        self.assertEqual(data["csa_verdict"], "CSA_DECISION_PATH_TRUTH_CONFIRMED")
        self.assertEqual(data["sre_verdict"], "SRE_DECISION_PATH_SAFE")
        self.assertTrue(data["production_run_jsonl_unchanged"])


if __name__ == "__main__":
    unittest.main()
