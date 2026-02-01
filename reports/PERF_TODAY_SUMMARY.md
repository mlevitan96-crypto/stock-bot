# Performance Review — Today

**Generated:** 2026-01-28T22:55:40.895229+00:00
**Date:** 2026-01-28

## 1) Executive Summary

- **Net PnL (USD):** -23.64
- **Win rate (%):** 41.36
- **Max drawdown (USD):** -49.95
- **Trade count:** 162

**One-sentence verdict:** Today was flat/negative with 162 trades and 41.36% win rate; main drivers: trade mix and gate/signal behavior.

## 2) Trade Quality

- **R-multiples / win quality:** Avg win USD = 1.19; avg loss USD = -1.12.

**Best 5 trades (by PnL):**
- TSLA PnL=13.72 USD — —
- CAT PnL=13.24 USD — —
- INTC PnL=9.85 USD — —
- UNH PnL=5.78 USD — —
- PLTR PnL=3.17 USD — —

**Worst 5 trades:**
- MRNA PnL=-8.64 USD — —
- AMZN PnL=-7.73 USD — —
- META PnL=-6.77 USD — —
- LCID PnL=-5.61 USD — —
- AMD PnL=-5.11 USD — —

## 3) Signal & Gate Attribution

- **Trade intents:** 1552 total; entered: 53, blocked: 1499.
- **Blocked reasons:** {'displacement_blocked': 1499}

**Per-signal family (from intelligence_trace):**

- **alpha_signals:** count=1552, entered=53, blocked=1499, PnL sum≈-3.37
- **flow_signals:** count=1552, entered=53, blocked=1499, PnL sum≈-3.37
- **regime_signals:** count=1552, entered=53, blocked=1499, PnL sum≈-3.37
- **volatility_signals:** count=1552, entered=53, blocked=1499, PnL sum≈-3.37
- **dark_pool_signals:** count=1552, entered=53, blocked=1499, PnL sum≈-3.37

**Gates:**
- Displacement: evaluated=0, allowed=0, blocked=0
- Directional gate: events=0, blocked≈0

## 4) Regime Fit

- **Source:** telemetry
- **Dominant regime:** NEUTRAL
- **Trend bucket:** unknown; **Volatility bucket:** mid

Whether the strategy is aligned or fighting the tape depends on today's regime vs. system comfort zone (e.g. trend vs chop). Use regime_timeline and state/regime_detector_state for full context.

## 5) Operational Friction

- **Self-heal events today:** 0

- **Telemetry computed keys:** ['entry_parity_details.json', 'exit_intel_completeness.json', 'blocked_counterfactuals_summary.json', 'signal_weight_recommendations.json', 'pnl_windows.json', 'shadow_vs_live_parity.json', 'score_distribution_curves.json', 'exit_quality_summary.json', 'long_short_analysis.json', 'regime_timeline.json', 'live_vs_shadow_pnl.json', 'feature_value_curves.json', 'gate_profitability.json', 'intelligence_recommendations.json', 'signal_performance.json', 'feature_family_summary.json', 'feature_equalizer_builder.json', 'regime_sector_feature_matrix.json', 'signal_profitability.json', 'replacement_telemetry_expanded.json']

Any WARNs or telemetry gaps that coincided with performance swings should be reviewed in logs.

## 6) Tuning Brief (Cursor's Implementation-Aware Recommendations)

Evidence-backed recommendations; **not applied** in this pass.

- **[PARAM_TUNING]**
  - **Observation:** Block rate 97% (1499/1552 trade_intent blocked).
  - **Hypothesis:** Over-blocking may reduce opportunity; gates or score thresholds may be too strict.
  - **Proposed change:** Add diagnostic: log blocked_reason distribution by hour; consider relaxing displacement or directional_gate thresholds in config if regime supports it.

- **[PARAM_TUNING]**
  - **Observation:** Net PnL negative (-23.64 USD) with 162 trades.
  - **Hypothesis:** Exits or position sizing may be suboptimal; or entries are poor quality.
  - **Proposed change:** Review exit_intent reasons and trailing-stop/time-exit settings; consider tightening entry score threshold (MIN_EXEC_SCORE) or reducing size.

- **[SAFE_DIAGNOSTIC]**
  - **Observation:** Signal-family PnL attribution is best-effort from intelligence_trace.
  - **Hypothesis:** Better attribution improves tuning.
  - **Proposed change:** Add per-trade signal_family snapshot to attribution or exit_attribution for robust signal performance tables.

## 7) Model-Level Recommendations (High-Level Strategy Perspective)

Summary for Mark (no code):

- **Regime alignment:** Ensure strategy comfort zone (e.g. trend-following vs mean-reversion) matches today's regime; consider regime filter or reduced size in hostile regimes.
- **Entry quality:** If losses are concentrated in a few symbols or themes, tighten universe or signal weights for those; improve entry timing (e.g. pullback vs breakout).
- **Exit quality:** If winners are cut early or losers run, review trailing-stop, time-exit, and thesis-break logic.
- **Over- vs under-blocking:** If many blocked intents would have been winners, consider relaxing gates; if losses come from bad entries that passed, consider tightening.
- **Position sizing / capital at risk:** Align exposure with volatility and regime; avoid over-concentration in single names.

**Structural note:** Negative PnL with realized trades suggests the issue is strategy (entry/exit/sizing) or regime mismatch, not merely data completeness.

## 8) Dual Perspective: Cursor vs Model

### 8.1 Cursor (Implementation-Aware)

Concrete, code/config-adjacent recommendations (tagged):

- **SAFE_DIAGNOSTIC:** Add telemetry when displacement blocks (symbol, score_delta) for blocked-trade analysis.
- **SAFE_DIAGNOSTIC:** Add per-trade signal_family snapshot to attribution for robust signal performance tables.
- **PARAM_TUNING:** If block rate is high, log blocked_reason by hour and consider relaxing displacement/gate thresholds in config.
- **PARAM_TUNING:** If PnL is negative with many trades, review MIN_EXEC_SCORE and trailing-stop/time-exit params.
- **STRUCTURAL:** If zero trades despite intents, trace execution path (trade_intent → orders.jsonl → attribution) and check safe mode / audit flags.

### 8.2 Model (Strategy-Level)

If we assume the data is correct and complete, losses are likely due to **entry quality**, **exit timing**, or **regime mismatch**. Structural changes that would most likely improve expectancy: (1) align timeframes with regime (e.g. shorter in chop); (2) tighten entry filter or reduce size in high-vol regimes; (3) improve exit logic (trailing vs thesis-break); (4) add regime filter to reduce trading in hostile regimes; (5) diversify symbols/themes to reduce single-name risk.
