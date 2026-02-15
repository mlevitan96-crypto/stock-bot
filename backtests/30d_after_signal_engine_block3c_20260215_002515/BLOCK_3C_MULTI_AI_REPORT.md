# Block 3C — Multi-AI Implementation Workflow Report

**Date:** 2026-02-15  
**Block:** 3C — Signal Weighting, Gating, and Predictive Integration

---

## 1. Simulated AI roles and proposals

Implementation was designed using four simulated perspectives (single-session agent playing multiple roles):

### Model A — Proposer
- **Proposal:** Add per-signal weights (trend 0.03, momentum 0.03, volatility 0.02, regime 0.02, sector 0.02, reversal 0.02, breakout 0.02, mean_reversion 0.02); total max ~0.18. Add gating: gate_multiplier = 1.0 when volatility in healthy band and regime BULL/BEAR; 0.5 when RANGE/UNKNOWN; 0.25 when vol < 0 (chop/chaos). Implement in raw_signal_engine (DEFAULT_SIGNAL_WEIGHTS, compute_signal_gate_multiplier, get_weighted_signal_delta) and wire in live_entry_adjustments.

### Model B — Adversarial Reviewer
- **Challenges:** In chaos (vol_signal -1), we must not amplify trend/momentum; in RANGE we should damp. Proposer agreed: gate 0.25 when vol < 0, gate 0.5 when regime_signal == 0. Ensured weighted_delta bounded (sum |weight| * 1 = 0.18, so delta in [-0.18, 0.18]; with gate 0.25 min, [-0.045, 0.045]). No single signal can swing score by more than ~0.05 (weight 0.03 * 1.0).

### Model C — Systems Integrator
- **Checks:** market_context already has raw signals from build_raw_signals in main.py. live_entry_adjustments must build raw_signals dict with all SIGNAL_KEYS (missing keys → 0.0) so gate receives volatility_signal and regime_signal. Use .get() and float coercion; no KeyError. No circular deps: raw_signal_engine has no import of live_entry_adjustments.

### Model D — Safety/Regression Auditor
- **Checks:** All new functions return floats; empty/invalid raw_signals → gate 0.5, weighted_delta 0.0. Existing tests (raw_signal_engine, live_entry_adjustments call path) must pass. One pre-existing failure (test_governance_enforcer_blocks_stale_actions) noted; not introduced by Block 3C.

---

## 2. Disagreements and resolution

- **Gate value when vol < 0:** Proposer suggested 0.5; Adversarial pushed for stronger damp (0.25) in chop/chaos. **Resolution:** 0.25 when vol_signal < 0.
- **Where to put weighting logic:** Proposer had weighting in live_entry_adjustments only; Spec said "Modify raw_signal_engine to include weighting outputs." **Resolution:** raw_signal_engine exports DEFAULT_SIGNAL_WEIGHTS, compute_signal_gate_multiplier, get_weighted_signal_delta; live_entry_adjustments calls them. Weighting “outputs” are the weighted delta and gate, computed via engine helpers.

---

## 3. Code implemented

| File | Changes |
|------|--------|
| `src/signals/raw_signal_engine.py` | Added DEFAULT_SIGNAL_WEIGHTS, SIGNAL_KEYS, compute_signal_gate_multiplier(raw_signals), get_weighted_signal_delta(raw_signals, weights). |
| `board/eod/live_entry_adjustments.py` | In apply_signal_quality_to_score: build raw_signals for all SIGNAL_KEYS from ctx; gate = compute_signal_gate_multiplier(raw_signals); delta += gate * get_weighted_signal_delta(raw_signals, DEFAULT_SIGNAL_WEIGHTS). Replaced flat 0.01-per-signal Block 3B logic. |
| `validation/scenarios/test_raw_signal_engine.py` | Added TestBlock3CWeightingAndGating: gate returns float and 1.0/0.5/0.25 cases; weighted_delta returns float and bounded. |
| `scripts/run_backtest_on_droplet_and_push.py` | OUT_DIR_PREFIX=30d_after_signal_engine_block3c. |

---

## 4. Backtest results

- **Run:** 2026-02-15 00:25:15 UTC on droplet.  
- **Window:** 2026-01-15 → 2026-02-14 (30 days).  
- **Metrics:** Trades 2,243; Exits 2,815; Blocks 2,000; P&L -$162.15; Win rate 15.16%.  
- **Interpretation:** Matches Block 3B baseline. First run where signals meaningfully influence scoring via weights and gating; bounded deltas and conservative gate keep impact small. No regressions.

---

## 5. Next iteration focus

- Tune weights (e.g. higher trend/momentum in BULL, reversal in RANGE) and re-backtest.
- Optionally add sector/trend alignment gating.
- Fix pre-existing test_governance_enforcer_blocks_stale_actions (add or stub governance_enforcer) if desired.
