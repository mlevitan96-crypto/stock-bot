#!/usr/bin/env python3
"""
Unit tests for raw signal engine (Block 3B).
Ensures raw_signal_engine imports cleanly, each signal returns float,
and sanity checks: increasing series -> trend/momentum > 0, flat -> near 0.
"""
from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(REPO_ROOT))


class TestRawSignalEngineImport(unittest.TestCase):
    def test_import_cleanly(self):
        from src.signals.raw_signal_engine import (
            build_raw_signals,
            compute_trend_signal,
            compute_momentum_signal,
            compute_volatility_signal,
            compute_regime_signal,
            compute_sector_signal,
            compute_reversal_signal,
            compute_breakout_signal,
            compute_mean_reversion_signal,
        )
        self.assertIsNotNone(build_raw_signals)
        self.assertIsNotNone(compute_trend_signal)


class TestRawSignalEngineReturnsFloat(unittest.TestCase):
    def test_each_signal_returns_float(self):
        from src.signals.raw_signal_engine import build_raw_signals
        out = build_raw_signals([100.0, 101.0, 102.0] * 20, "BULL", 0.1)
        for k, v in out.items():
            self.assertIsInstance(v, float, f"{k} should be float, got {type(v)}")


class TestRawSignalEngineSanity(unittest.TestCase):
    def test_increasing_series_trend_and_momentum_positive(self):
        from src.signals.raw_signal_engine import compute_trend_signal, compute_momentum_signal
        inc = [100.0 + i for i in range(50)]
        trend = compute_trend_signal(inc)
        momentum = compute_momentum_signal(inc)
        self.assertGreater(trend, 0, "increasing series -> trend_signal > 0")
        self.assertGreater(momentum, 0, "increasing series -> momentum_signal > 0")

    def test_flat_series_near_zero(self):
        from src.signals.raw_signal_engine import compute_trend_signal, compute_momentum_signal
        flat = [100.0] * 30
        trend = compute_trend_signal(flat)
        momentum = compute_momentum_signal(flat)
        self.assertAlmostEqual(trend, 0.0, places=2, msg="flat series -> trend near 0")
        self.assertAlmostEqual(momentum, 0.0, places=2, msg="flat series -> momentum near 0")

    def test_regime_signal_bull_bear(self):
        from src.signals.raw_signal_engine import compute_regime_signal
        self.assertEqual(compute_regime_signal("BULL"), 1.0)
        self.assertEqual(compute_regime_signal("BEAR"), -1.0)
        self.assertAlmostEqual(compute_regime_signal("RANGE"), 0.0, places=2)


class TestBlock3CWeightingAndGating(unittest.TestCase):
    """Block 3C: gate multiplier and weighted signal delta return floats and behave as specified."""

    def test_gate_multiplier_returns_float(self):
        from src.signals.raw_signal_engine import compute_signal_gate_multiplier
        g = compute_signal_gate_multiplier({"volatility_signal": 0.5, "regime_signal": 1.0})
        self.assertIsInstance(g, float)
        self.assertGreaterEqual(g, 0.0)
        self.assertLessEqual(g, 1.0)

    def test_gate_full_when_healthy_vol_and_bull_regime(self):
        from src.signals.raw_signal_engine import compute_signal_gate_multiplier
        g = compute_signal_gate_multiplier({"volatility_signal": 0.5, "regime_signal": 1.0})
        self.assertEqual(g, 1.0)

    def test_gate_damp_when_regime_range(self):
        from src.signals.raw_signal_engine import compute_signal_gate_multiplier
        g = compute_signal_gate_multiplier({"volatility_signal": 0.5, "regime_signal": 0.0})
        self.assertEqual(g, 0.5)

    def test_gate_damp_when_vol_negative(self):
        from src.signals.raw_signal_engine import compute_signal_gate_multiplier
        g = compute_signal_gate_multiplier({"volatility_signal": -0.5, "regime_signal": 1.0})
        self.assertEqual(g, 0.25)

    def test_weighted_signal_delta_returns_float(self):
        from src.signals.raw_signal_engine import get_weighted_signal_delta, DEFAULT_SIGNAL_WEIGHTS
        d = get_weighted_signal_delta({"trend_signal": 0.5, "momentum_signal": 0.3}, DEFAULT_SIGNAL_WEIGHTS)
        self.assertIsInstance(d, float)

    def test_weighted_signal_delta_bounded(self):
        from src.signals.raw_signal_engine import get_weighted_signal_delta, DEFAULT_SIGNAL_WEIGHTS
        all_ones = {k: 1.0 for k in DEFAULT_SIGNAL_WEIGHTS}
        d = get_weighted_signal_delta(all_ones, DEFAULT_SIGNAL_WEIGHTS)
        self.assertIsInstance(d, float)
        self.assertLessEqual(abs(d), 0.2)


class TestBlock3DWeightingAndGating(unittest.TestCase):
    """Block 3D: regime-adjusted weights, sector alignment, composite gate, bounded delta."""

    def test_compute_regime_adjusted_weights_returns_dict_of_floats(self):
        from src.signals.raw_signal_engine import compute_regime_adjusted_weights, SIGNAL_KEYS
        w = compute_regime_adjusted_weights("BULL")
        self.assertIsInstance(w, dict)
        for k in SIGNAL_KEYS:
            self.assertIn(k, w)
            self.assertIsInstance(w[k], float)

    def test_regime_adjusted_weights_bull_boosts_trend_momentum(self):
        from src.signals.raw_signal_engine import compute_regime_adjusted_weights, DEFAULT_SIGNAL_WEIGHTS_3D
        w_bull = compute_regime_adjusted_weights("BULL")
        self.assertGreater(w_bull["trend_signal"], DEFAULT_SIGNAL_WEIGHTS_3D["trend_signal"])
        self.assertGreater(w_bull["momentum_signal"], DEFAULT_SIGNAL_WEIGHTS_3D["momentum_signal"])
        self.assertLess(w_bull["reversal_signal"], DEFAULT_SIGNAL_WEIGHTS_3D["reversal_signal"])

    def test_regime_adjusted_weights_range_boosts_reversal_mean_reversion(self):
        from src.signals.raw_signal_engine import compute_regime_adjusted_weights, DEFAULT_SIGNAL_WEIGHTS_3D
        w_range = compute_regime_adjusted_weights("RANGE")
        self.assertGreater(w_range["reversal_signal"], DEFAULT_SIGNAL_WEIGHTS_3D["reversal_signal"])
        self.assertGreater(w_range["mean_reversion_signal"], DEFAULT_SIGNAL_WEIGHTS_3D["mean_reversion_signal"])
        self.assertLess(w_range["trend_signal"], DEFAULT_SIGNAL_WEIGHTS_3D["trend_signal"])

    def test_compute_sector_alignment_multiplier_agree_returns_boost(self):
        from src.signals.raw_signal_engine import compute_sector_alignment_multiplier, SECTOR_ALIGNMENT_BOOST
        m = compute_sector_alignment_multiplier({"sector_signal": 0.5, "trend_signal": 0.3})
        self.assertEqual(m, SECTOR_ALIGNMENT_BOOST)

    def test_compute_sector_alignment_multiplier_disagree_returns_damp(self):
        from src.signals.raw_signal_engine import compute_sector_alignment_multiplier, SECTOR_ALIGNMENT_DAMP
        m = compute_sector_alignment_multiplier({"sector_signal": -0.5, "trend_signal": 0.3})
        self.assertEqual(m, SECTOR_ALIGNMENT_DAMP)

    def test_compute_sector_alignment_multiplier_missing_keys_default_safe(self):
        from src.signals.raw_signal_engine import compute_sector_alignment_multiplier
        self.assertEqual(compute_sector_alignment_multiplier({}), 1.0)
        self.assertEqual(compute_sector_alignment_multiplier(None), 1.0)

    def test_compute_volatility_gate_returns_float_in_bounds(self):
        from src.signals.raw_signal_engine import compute_volatility_gate
        g = compute_volatility_gate({"volatility_signal": 0.5})
        self.assertIsInstance(g, float)
        self.assertIn(g, (0.25, 0.5, 1.0))

    def test_compute_volatility_gate_low_vol_returns_025(self):
        from src.signals.raw_signal_engine import compute_volatility_gate
        self.assertEqual(compute_volatility_gate({"volatility_signal": -0.5}), 0.25)

    def test_compute_volatility_gate_high_vol_returns_05(self):
        from src.signals.raw_signal_engine import compute_volatility_gate
        self.assertEqual(compute_volatility_gate({"volatility_signal": 0.9}), 0.5)

    def test_compute_composite_gate_returns_float_bounded(self):
        from src.signals.raw_signal_engine import compute_composite_gate, COMPOSITE_GATE_MIN
        g = compute_composite_gate(
            {"volatility_signal": 0.5, "trend_signal": 0.3, "regime_signal": 1.0},
            "BULL",
            0.1,
        )
        self.assertIsInstance(g, float)
        self.assertGreaterEqual(g, COMPOSITE_GATE_MIN)
        self.assertLessEqual(g, 1.0)

    def test_compute_composite_gate_missing_keys_safe(self):
        from src.signals.raw_signal_engine import compute_composite_gate, COMPOSITE_GATE_MIN
        g = compute_composite_gate({}, "", 0.0)
        self.assertIsInstance(g, float)
        self.assertGreaterEqual(g, COMPOSITE_GATE_MIN)

    def test_get_weighted_signal_delta_3d_returns_float_bounded(self):
        from src.signals.raw_signal_engine import (
            get_weighted_signal_delta_3D,
            compute_regime_adjusted_weights,
            WEIGHTED_DELTA_MAX_ABS,
        )
        raw = {k: 1.0 for k in ("trend_signal", "momentum_signal", "volatility_signal", "regime_signal",
                                "sector_signal", "reversal_signal", "breakout_signal", "mean_reversion_signal")}
        w = compute_regime_adjusted_weights("BULL")
        d = get_weighted_signal_delta_3D(raw, w, 1.0)
        self.assertIsInstance(d, float)
        self.assertLessEqual(abs(d), WEIGHTED_DELTA_MAX_ABS)

    def test_get_weighted_signal_delta_3d_missing_keys_default_zero(self):
        from src.signals.raw_signal_engine import get_weighted_signal_delta_3D, DEFAULT_SIGNAL_WEIGHTS_3D
        d = get_weighted_signal_delta_3D({}, DEFAULT_SIGNAL_WEIGHTS_3D, 1.0)
        self.assertIsInstance(d, float)
        self.assertEqual(d, 0.0)
