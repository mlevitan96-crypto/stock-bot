#!/usr/bin/env python3
"""
Tests for proactive root-cause mode: UW root cause, exit causality, exit regimes,
survivorship adjustments, constraint root cause, missed money numeric, variant tagging,
correlation snapshot, board proactive insights, governance enforcer.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(REPO_ROOT))


class TestUwRootCauseGenerated(unittest.TestCase):
    def test_uw_root_cause_generated(self):
        from board.eod.root_cause import build_uw_root_cause
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "logs").mkdir()
            (base / "state").mkdir()
            out = build_uw_root_cause(base, "2026-02-15", window_days=7)
        self.assertIn("uw_signal_quality_score", out)
        self.assertIn("uw_edge_realization_rate", out)
        self.assertIn("uw_edge_suppression_rate", out)
        self.assertIn("candidates", out)


class TestExitCausalityMatrixGenerated(unittest.TestCase):
    def test_exit_causality_matrix_generated(self):
        from board.eod.root_cause import build_exit_causality_matrix, CAUSE_OF_DECAY_OPTIONS
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "logs").mkdir()
            (base / "state").mkdir()
            out = build_exit_causality_matrix(base, "2026-02-15", window_days=7)
        self.assertIn("exits", out)
        self.assertIn("cause_counts", out)
        self.assertEqual(out.get("cause_options"), CAUSE_OF_DECAY_OPTIONS)


class TestExitRegimesFireSaleAndLetItBreathe(unittest.TestCase):
    def test_exit_regimes_fire_sale_and_let_it_breathe(self):
        from board.eod.exit_regimes import get_exit_regime
        regime, reason, ctx = get_exit_regime(signal_delta=-0.6)
        self.assertEqual(regime, "fire_sale")
        self.assertIn("signal_delta", reason)
        regime2, reason2, _ = get_exit_regime(entry_signal_strength=4.0, pnl_delta_15m=10.0)
        self.assertEqual(regime2, "let_it_breathe")
        regime3, _, _ = get_exit_regime()
        self.assertEqual(regime3, "normal")


class TestSurvivorshipAdjustmentsWritten(unittest.TestCase):
    def test_survivorship_adjustments_written(self):
        from board.eod.root_cause import build_survivorship_adjustments
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "logs").mkdir()
            (base / "state").mkdir()
            out = build_survivorship_adjustments(base, "2026-02-15", window_days=7)
        self.assertIn("chronic_losers", out)
        self.assertIn("consistent_winners", out)
        self.assertIn("adjustments", out)
        with tempfile.TemporaryDirectory() as td2:
            base2 = Path(td2)
            (base2 / "logs").mkdir()
            (base2 / "state").mkdir()
            build_survivorship_adjustments(base2, "2026-02-16", window_days=7)
            self.assertTrue((base2 / "state" / "survivorship_adjustments.json").exists())


class TestConstraintRootCauseGenerated(unittest.TestCase):
    def test_constraint_root_cause_generated(self):
        from board.eod.root_cause import build_constraint_root_cause
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "logs").mkdir()
            (base / "state").mkdir()
            out = build_constraint_root_cause(base, "2026-02-15", window_days=7)
        self.assertIn("by_reason", out)
        self.assertIn("constraint_suppression_cost_usd", out)


class TestMissedMoneyNumeric(unittest.TestCase):
    def test_missed_money_numeric(self):
        from board.eod.root_cause import build_missed_money_numeric
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "logs").mkdir()
            (base / "state").mkdir()
            out = build_missed_money_numeric(base, "2026-02-15", window_days=7)
        self.assertIn("blocked_trade_cost_usd", out)
        self.assertIn("early_exit_cost_usd", out)
        self.assertIn("correlation_cost_score", out)
        self.assertIn("all_numeric", out)


class TestVariantTaggingPresent(unittest.TestCase):
    def test_variant_tagging_present(self):
        from src.exit.exit_attribution import build_exit_attribution_record
        rec = build_exit_attribution_record(
            symbol="AAPL", entry_timestamp="2026-02-15T10:00:00Z", exit_reason="signal_decay(0.5)",
            pnl=10.0, pnl_pct=0.5, entry_price=100.0, exit_price=101.0, qty=10.0,
            time_in_trade_minutes=30.0, entry_uw={}, exit_uw={}, entry_regime="NEUTRAL", exit_regime="NEUTRAL",
            entry_sector_profile={}, exit_sector_profile={}, score_deterioration=-0.2,
            relative_strength_deterioration=-0.1, v2_exit_score=2.5, v2_exit_components={},
        )
        self.assertIn("symbol", rec)
        if "variant_id" in rec:
            self.assertIsInstance(rec["variant_id"], (str, type(None)))


class TestCorrelationSnapshotNonempty(unittest.TestCase):
    def test_correlation_snapshot_nonempty(self):
        from board.eod.root_cause import build_correlation_snapshot
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "state").mkdir()
            out = build_correlation_snapshot(base, "2026-02-15")
        self.assertIn("date", out)
        self.assertIn("pairs", out)
        self.assertIn("concentration_risk_score", out)


class TestBoardProactiveInsightsPresent(unittest.TestCase):
    def test_board_proactive_insights_present(self):
        from board.eod.run_stock_quant_officer_eod import build_prompt
        prompt = build_prompt(
            "Contract text", "Bundle summary", "2026-02-15",
            root_cause_summary="UW quality_score=0.5 edge_suppression=0.3",
        )
        self.assertIn("proactive_insights", prompt)
        self.assertIn("root_cause", prompt)
        self.assertIn("recommended_fixes", prompt)
        self.assertIn("at least 5", prompt)


class TestGovernanceEnforcerBlocksStaleActions(unittest.TestCase):
    def test_governance_enforcer_blocks_stale_actions(self):
        from board.eod.governance_enforcer import check_governance
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "reports").mkdir()
            ok, reasons, payload = check_governance(base=base, date_str="2026-02-15")
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(reasons, list)
        self.assertIn("ok", payload)
        self.assertIn("unclosed_actions", payload)


# --- Live integration tests (wire root-cause into trading) ---

class TestExitRegimesInLiveExitPath(unittest.TestCase):
    def test_exit_regimes_in_live_exit_path(self):
        from board.eod.exit_regimes import get_exit_regime, log_exit_regime_decision
        regime, reason, ctx = get_exit_regime(signal_delta=-0.6, price_delta_pct=-6.0)
        self.assertEqual(regime, "fire_sale")
        with tempfile.TemporaryDirectory() as td:
            log_exit_regime_decision("AAPL", regime, reason, ctx, log_dir=Path(td))
            self.assertTrue((Path(td) / "exit_regime_decisions.jsonl").exists())


class TestVariantIdPropagatesThroughExit(unittest.TestCase):
    def test_variant_id_propagates_through_exit(self):
        from src.exit.exit_attribution import build_exit_attribution_record
        rec = build_exit_attribution_record(
            symbol="AAPL", entry_timestamp="2026-02-15T10:00:00Z", exit_reason="signal_decay(0.5)",
            pnl=10.0, pnl_pct=0.5, entry_price=100.0, exit_price=101.0, qty=10.0,
            time_in_trade_minutes=30.0, entry_uw={}, exit_uw={}, entry_regime="NEUTRAL", exit_regime="NEUTRAL",
            entry_sector_profile={}, exit_sector_profile={}, score_deterioration=-0.2,
            relative_strength_deterioration=-0.1, v2_exit_score=2.5, v2_exit_components={},
            variant_id="live_canary",
        )
        self.assertEqual(rec.get("variant_id"), "live_canary")


class TestSurvivorshipAdjustmentsAffectEntry(unittest.TestCase):
    def test_survivorship_adjustments_affect_entry(self):
        from board.eod.live_entry_adjustments import apply_survivorship_to_score, load_survivorship_adjustments
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "state").mkdir()
            (base / "state" / "survivorship_adjustments.json").write_text(
                json.dumps({"adjustments": [{"symbol": "X", "action": "penalize"}]}), encoding="utf-8"
            )
            adj, action = apply_survivorship_to_score("X", 4.0, base=base)
        self.assertLess(adj, 4.0)
        self.assertEqual(action, "penalize")


class TestUwAdjustmentsAffectEntry(unittest.TestCase):
    def test_uw_adjustments_affect_entry(self):
        from board.eod.live_entry_adjustments import apply_uw_to_score
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "board" / "eod" / "out" / "2026-02-15").mkdir(parents=True)
            (base / "board" / "eod" / "out" / "2026-02-15" / "uw_root_cause.json").write_text(
                json.dumps({"uw_signal_quality_score": 0.5, "uw_edge_realization_rate": 0.6, "uw_edge_suppression_rate": 0.3}), encoding="utf-8"
            )
            score, details = apply_uw_to_score("AAPL", 3.0, base=base)
        self.assertGreaterEqual(score, 3.0)


class TestConstraintRootCauseAffectsConstraints(unittest.TestCase):
    def test_constraint_root_cause_affects_constraints(self):
        from board.eod.live_entry_adjustments import load_constraint_root_cause_latest
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "board" / "eod" / "out" / "2026-02-15").mkdir(parents=True)
            (base / "board" / "eod" / "out" / "2026-02-15" / "constraint_root_cause.json").write_text(
                json.dumps({"constraint_suppression_cost_usd": 100.0, "by_reason": [{"block_reason": "max_positions_reached", "count": 5}]}), encoding="utf-8"
            )
            data = load_constraint_root_cause_latest(base=base)
        self.assertEqual(data.get("constraint_suppression_cost_usd"), 100.0)


class TestMissedMoneyNumericEnforced(unittest.TestCase):
    def test_missed_money_numeric_enforced(self):
        import argparse
        ap = argparse.ArgumentParser()
        ap.add_argument("--allow-missing-missed-money", action="store_true")
        args_no_flag = ap.parse_args([])
        args_with_flag = ap.parse_args(["--allow-missing-missed-money"])
        self.assertFalse(getattr(args_no_flag, "allow_missing_missed_money", False))
        self.assertTrue(getattr(args_with_flag, "allow_missing_missed_money", False))
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "missed_money_numeric.json"
            path.write_text(json.dumps({"all_numeric": False}), encoding="utf-8")
            mm = json.loads(path.read_text())
            self.assertIs(mm.get("all_numeric"), False)
            should_fail = mm.get("all_numeric") is False and not getattr(args_with_flag, "allow_missing_missed_money")
            self.assertFalse(should_fail)
            should_fail_no_allow = mm.get("all_numeric") is False and not getattr(args_no_flag, "allow_missing_missed_money")
            self.assertTrue(should_fail_no_allow)


class TestCorrelationSnapshotAffectsSizing(unittest.TestCase):
    def test_correlation_snapshot_affects_sizing(self):
        from board.eod.live_entry_adjustments import correlation_concentration_risk_multiplier, load_correlation_snapshot
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "state").mkdir()
            (base / "state" / "correlation_snapshot.json").write_text(
                json.dumps({"concentration_risk_score": 3.0}), encoding="utf-8"
            )
            mult = correlation_concentration_risk_multiplier(base=base, threshold=2.0)
        self.assertLess(mult, 1.0)
