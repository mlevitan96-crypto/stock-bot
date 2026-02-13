#!/usr/bin/env python3
"""
Tests for tightened profitability levers: exit regimes, survivorship, UW boosts,
constraint overrides, missed-money enforcement.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(REPO_ROOT))


class TestExitRegimesTightened(unittest.TestCase):
    """Exit regimes: FIRE SALE -0.25/-3, LET-IT-BREATHE 2.5, relax_decay 1.5."""

    def test_exit_regimes_tightened(self):
        from board.eod.exit_regimes import get_exit_regime, load_config

        cfg = load_config()
        fire = cfg.get("fire_sale") or {}
        breathe = cfg.get("let_it_breathe") or {}

        self.assertEqual(fire.get("signal_delta_threshold"), -0.25)
        self.assertEqual(fire.get("price_delta_pct_threshold"), -3)
        self.assertIn("catastrophic_decay_delta", fire)
        self.assertEqual(breathe.get("entry_signal_strength_threshold"), 2.5)
        self.assertIn("relax_decay_multiplier", breathe)

        regime, reason, ctx = get_exit_regime(signal_delta=-0.3)
        self.assertEqual(regime, "fire_sale")
        regime2, _, _ = get_exit_regime(entry_signal_strength=3.0, pnl_delta_15m=0.1)
        self.assertEqual(regime2, "let_it_breathe")


class TestSurvivorshipPenaltiesStronger(unittest.TestCase):
    """Survivorship: penalize_strong (-0.5), boost_strong (+0.5). NO symbol bans."""

    def test_survivorship_penalties_stronger(self):
        from board.eod.root_cause import build_survivorship_adjustments

        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "state").mkdir()
            (base / "state" / "signal_survivorship_2026-02-12.json").write_text(
                json.dumps({
                    "signals": {
                        "A": {"pnl_contribution_usd": -15, "trade_count": 4, "win_rate": 0.3},
                        "B": {"pnl_contribution_usd": 25, "trade_count": 5, "win_rate": 0.5},
                    }
                }),
                encoding="utf-8",
            )
            with patch("board.eod.rolling_windows.build_signal_survivorship") as m:
                m.return_value = json.loads((base / "state" / "signal_survivorship_2026-02-12.json").read_text())
                out = build_survivorship_adjustments(base, "2026-02-12", window_days=1)

        adj = {a["symbol"]: a for a in out.get("adjustments") or []}
        self.assertIn("A", adj)
        self.assertEqual(adj["A"]["action"], "penalize_strong")
        self.assertEqual(adj["A"].get("score_penalty"), -0.5)
        self.assertNotIn("block_for_days", adj["A"])  # NO bans: survivorship only adjusts scores
        self.assertIn("B", adj)
        self.assertEqual(adj["B"]["action"], "boost_strong")
        self.assertEqual(adj["B"].get("score_boost"), 0.5)


class TestUwBoostsStronger(unittest.TestCase):
    """UW: quality>=0.6 -> +0.75, edge_suppression>0.5 -> allow let-it-breathe."""

    def test_uw_boosts_stronger(self):
        from board.eod.live_entry_adjustments import apply_uw_to_score

        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "board" / "eod" / "out" / "2026-02-12").mkdir(parents=True)
            (base / "board" / "eod" / "out" / "2026-02-12" / "uw_root_cause.json").write_text(
                json.dumps({
                    "uw_signal_quality_score": 0.65,
                    "uw_edge_realization_rate": 0.5,
                    "uw_edge_suppression_rate": 0.55,
                }),
                encoding="utf-8",
            )
            score, details = apply_uw_to_score("AAPL", 3.0, base=base)
        self.assertGreater(score, 3.0)
        self.assertTrue(details.get("uw_quality_boost_strong"))
        self.assertTrue(details.get("allow_displacement_override"))


class TestConstraintOverridesEnabled(unittest.TestCase):
    """Constraint overrides: uw_quality>=0.6 OR survivorship boost OR live_canary."""

    def test_constraint_overrides_enabled(self):
        from board.eod.live_entry_adjustments import check_constraint_override_eligible

        eligible, reasons = check_constraint_override_eligible(
            "AAPL",
            {"allow_displacement_override": True},
            "",
            None,
        )
        self.assertTrue(eligible)
        self.assertIn("uw_quality_boost", reasons)

        eligible2, reasons2 = check_constraint_override_eligible(
            "MSFT",
            None,
            "boost_strong",
            None,
        )
        self.assertTrue(eligible2)
        self.assertIn("survivorship_boost", reasons2)

        eligible3, reasons3 = check_constraint_override_eligible(
            "GOOG",
            None,
            "",
            "live_canary",
        )
        self.assertTrue(eligible3)
        self.assertEqual(reasons3.get("variant_id"), "live_canary")


class TestForceEodAfterCronFailure(unittest.TestCase):
    """cron_diagnose_and_fix --date forces EOD and push."""

    def test_force_eod_after_cron_failure(self):
        from board.eod.cron_diagnose_and_fix import force_run_eod, push_to_github

        client = MagicMock()
        client._execute.return_value = ("", "", 0)
        with patch("board.eod.cron_diagnose_and_fix._detect_stockbot_root", return_value="/root/stock-bot"):
            rc, _, _ = force_run_eod("2026-02-12", client=client)
        self.assertEqual(rc, 0)
        call_cmd = client._execute.call_args[0][0]
        self.assertIn("eod_confirmation.py", call_cmd)
        self.assertIn("--date 2026-02-12", call_cmd)

        push_rc, _, _ = push_to_github("2026-02-12", client=client)
        self.assertEqual(push_rc, 0)
        push_cmd = client._execute.call_args[0][0]
        self.assertIn("board/eod/out/2026-02-12", push_cmd)


if __name__ == "__main__":
    unittest.main()
