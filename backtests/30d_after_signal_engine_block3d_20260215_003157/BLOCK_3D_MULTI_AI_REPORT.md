# Block 3D — Multi-AI Implementation Report

**Date:** 2026-02-15  
**Block:** 3D — Signal Weight Tuning, Gating Tuning, Predictive Influence Integration

---

## 1. Simulated AI roles and proposals

### Model A — Proposer
- **Proposal:** Add DEFAULT_SIGNAL_WEIGHTS_3D (trend/momentum higher; reversal/mean_reversion lower). Add compute_regime_adjusted_weights(regime_label) with BULL/BEAR/RANGE multipliers. Add compute_sector_alignment_multiplier (agree 1.2, disagree 0.5). Add compute_volatility_gate (low 0.25, high 0.5, else 1.0), regime_gate (contradict 0.5), compute_composite_gate (vol × regime × sector, ≥ 0.1). Add get_weighted_signal_delta_3D with clamp to ±0.25. Wire in live_entry_adjustments.

### Model B — Adversarial Reviewer
- **Challenges:** Sector boost 1.2 could push composite gate above 1.0 — cap composite at 1.0. Regime gate should not over-damp in RANGE (we want reversal/mean_reversion there). Ensure all dicts use .get() so missing keys don’t KeyError. **Resolution:** Composite gate min(1.0, composite); regime_gate only 0.5 when BULL/BEAR and trend/momentum contradict; RANGE no regime damp. All code paths use .get(..., 0.0) or safe defaults.

### Model C — Systems Integrator
- **Checks:** live_entry_adjustments already has regime_label and sector_momentum in ctx; use ctx.get("regime_label") or regime_label, ctx.get("sector_momentum") or 0.0. raw_signal_engine has no import of live_entry_adjustments. SIGNAL_KEYS unchanged so market_ctx keys match. **Resolution:** Use regime_label_ctx = ctx.get("regime_label") or regime_label; sector_momentum_ctx from ctx; pass to compute_composite_gate and compute_regime_adjusted_weights.

### Model D — Safety Auditor
- **Checks:** All new functions return float; get_weighted_signal_delta_3D clamps to ±0.25; compute_composite_gate ≥ 0.1. Unit tests for regime-adjusted weights, sector alignment, volatility gate, composite gate, delta 3D. **Resolution:** 24 tests pass (existing + Block 3D); no new failures.

---

## 2. Disagreements and resolution

- **Composite gate above 1.0:** Proposer had sector boost 1.2; composite could be 1.2. **Resolution:** composite = min(1.0, vol_gate * regime_gate * sector_mult); max 1.0.
- **Regime gate in RANGE:** Adversarial wanted no regime damp in RANGE so reversal/mean_reversion can influence. **Resolution:** _compute_regime_gate returns 0.5 only when BULL and (trend < 0 or momentum < 0), or BEAR and (trend > 0 or momentum > 0); RANGE/unknown → 1.0.

---

## 3. Code implemented

| File | Changes |
|------|--------|
| **raw_signal_engine.py** | DEFAULT_SIGNAL_WEIGHTS_3D; WEIGHTED_DELTA_MAX_ABS, COMPOSITE_GATE_MIN, VOL_GATE_THRESHOLD_LOW/HIGH, SECTOR_ALIGNMENT_DAMP/BOOST; compute_regime_adjusted_weights(regime_label); compute_sector_alignment_multiplier(raw_signals); compute_volatility_gate(raw_signals); _compute_regime_gate(raw_signals, regime_label); compute_composite_gate(raw_signals, regime_label, sector_momentum); get_weighted_signal_delta_3D(raw_signals, weights, gate). |
| **live_entry_adjustments.py** | Replaced Block 3C block with Block 3D: build raw_signals from SIGNAL_KEYS; regime_label_ctx, sector_momentum_ctx from ctx; gate = compute_composite_gate(...); weights_3d = compute_regime_adjusted_weights(...); delta += get_weighted_signal_delta_3D(raw_signals, weights_3d, gate). |
| **validation/scenarios/test_raw_signal_engine.py** | TestBlock3DWeightingAndGating: regime_adjusted_weights (dict of floats, BULL boosts trend/momentum, RANGE boosts reversal/mean_reversion); sector alignment (agree 1.2, disagree 0.5, missing keys 1.0); volatility gate (0.25/0.5/1.0); composite gate (float, bounded ≥ 0.1); get_weighted_signal_delta_3D (float, bounded ±0.25, missing keys 0). |
| **scripts/run_backtest_on_droplet_and_push.py** | OUT_DIR_PREFIX=30d_after_signal_engine_block3d. |

---

## 4. Backtest results

- **Run:** 2026-02-15 00:31:57 UTC on droplet.  
- **Window:** 2026-01-15 → 2026-02-14 (30 days).  
- **Metrics:** Trades 2,243; Exits 2,815; Blocks 2,000; **P&L -$162.15**; **Win rate 15.16%**.  
- **Interpretation:** Aggregate P&L and win rate unchanged vs baseline. Block 3D is the first iteration intended to meaningfully influence P&L; bounded delta and composite gate keep impact conservative. Next: inspect exit/block distributions and symbol-level/regime-specific behavior, then tune weights or thresholds and re-backtest.

---

## 5. Next iteration recommendations

- **Inspect:** Exit reason distribution (signal_decay mix), block reasons (score_floor vs displacement), symbol-level P&L, regime-specific (BULL/BEAR/RANGE) trade counts and P&L.
- **Tune:** Increase trend/momentum weight in BULL or sector alignment boost when sector and trend agree; tighten regime gate or volatility thresholds if needed.
- **Re-run:** 30-day backtest after tuning and compare P&L and win rate to Block 3D baseline.
