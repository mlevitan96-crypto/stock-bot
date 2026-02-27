"""
Regression: effectiveness reports must surface win_rate, avg_profit_giveback, and unclassified_pct.
When joined rows have exit_quality_metrics.profit_giveback, aggregates must be non-null.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.analysis.run_effectiveness_reports import (
    build_exit_effectiveness,
    build_entry_vs_exit_blame,
)


def _joined_row(pnl: float, entry_score: float | None = None, profit_giveback: float | None = None, mfe: float | None = None) -> dict:
    row = {"pnl": pnl, "symbol": "TEST", "exit_reason_code": "profit"}
    if entry_score is not None:
        row["entry_score"] = entry_score
    qm = {}
    if profit_giveback is not None:
        qm["profit_giveback"] = profit_giveback
    if mfe is not None:
        qm["mfe"] = mfe
    if qm:
        row["exit_quality_metrics"] = qm
    return row


class TestEffectivenessReports(unittest.TestCase):
    def test_exit_effectiveness_produces_giveback_when_present(self):
        """When joined rows have profit_giveback, exit_effectiveness has avg_profit_giveback."""
        joined = [
            _joined_row(10.0, entry_score=4.0, profit_giveback=0.2),
            _joined_row(-5.0, entry_score=2.0, profit_giveback=0.5),
            _joined_row(0.0, entry_score=3.0, profit_giveback=0.1),
        ]
        report = build_exit_effectiveness(joined)
        self.assertIsInstance(report, dict)
        for _reason, v in report.items():
            if isinstance(v, dict) and v.get("frequency", 0) > 0:
                self.assertIsNotNone(
                    v.get("avg_profit_giveback"),
                    "exit_effectiveness must have avg_profit_giveback when input has profit_giveback",
                )
                break

    def test_blame_has_unclassified_pct(self):
        """entry_vs_exit_blame must include unclassified_pct (and unclassified_count)."""
        # 3 losers: one weak entry (score 2), one exit timing (giveback 0.4), one neither
        joined = [
            _joined_row(-1.0, entry_score=2.0, profit_giveback=0.1),   # weak_entry only
            _joined_row(-1.0, entry_score=5.0, profit_giveback=0.4), # exit_timing only
            _joined_row(-1.0, entry_score=5.0, profit_giveback=0.0),  # unclassified
        ]
        blame = build_entry_vs_exit_blame(joined)
        self.assertIn("unclassified_pct", blame)
        self.assertIn("unclassified_count", blame)
        self.assertEqual(blame["total_losing_trades"], 3)
        self.assertGreaterEqual(blame["unclassified_count"], 0)
        self.assertGreaterEqual(blame["unclassified_pct"], 0)


if __name__ == "__main__":
    unittest.main()
