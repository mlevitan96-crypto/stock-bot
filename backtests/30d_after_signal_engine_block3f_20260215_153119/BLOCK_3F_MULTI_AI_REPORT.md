# Block 3F — Multi-AI Review Report

**Backtest dir:** `backtests/30d_after_signal_engine_block3f_20260215_153119`  
**Purpose:** First true signal edge backtest; multi-role read of results and recommendations.

---

## 1. What each “AI role” observed

### Proposer (initial read: promising / harmful signals)

- **Data limitation:** Raw signals (trend, momentum, volatility, sector, reversal, breakout, mean_reversion) are **missing** in this run because the backtest replayed from attribution/blocked_trades written **before** Block 3E.
- **Available:** Only **regime_signal** (near_zero / MIXED) and **entry_score** (positive / near_zero) have non-missing buckets. Both show negative expectancy (~−$0.15 per trade) and low win rate (15%); no bucket stands out as clearly “promising” or “harmful” with the current single-bucket coverage.
- **Conclusion:** No actionable signal-level weight-up/weight-down recommendation is possible from this run until we have real per-signal buckets.

### Adversarial (caveats)

- **Sample size:** 2,243 trades is reasonable for aggregate stats but regime split is skewed (MIXED 2,233, UNKNOWN 10). Any future per-regime conclusion (e.g. “trend works in BULL”) needs more balanced regime counts.
- **Regime imbalance:** We do not yet have BULL / BEAR / RANGE in the data; only MIXED and UNKNOWN. Regime-specific edge statements are not possible yet.
- **Noise:** Single 30d window; one run. No cross-validation or out-of-sample check. Any future weight change based on signal edge should be validated across multiple windows.

### Systems (data quality)

- **Missing fields:** Backtest loader and Signal Edge Analysis correctly treat missing signal fields (no crash); buckets show "missing" as expected.
- **Backward compatibility:** Confirmed; old attribution without signal fields still loads and is analyzed.
- **Verification:** To get real signal fields in a future run, either (a) ensure the bot has run with Block 3E for the full 30d window and re-run the backtest, or (b) add replay-time signal injection in the backtest script so that at each entry/block timestamp we compute market_context and write signal fields into the backtest output.

### Safety (overfitting / overreacting)

- **Do not change weights based on this run.** We do not have per-signal bucket data yet; changing weights would be unjustified.
- **Avoid overfitting to one run.** When real per-signal data exists, any weight-up/weight-down or gating decision should be validated on another window or held-out period.
- **Recommendation:** Treat Block 3F as pipeline validation. Use the next run that has full signal data for the first true weight-tuning input.

---

## 2. Clear answers (with current data)

### Which 1–3 signals look most promising to weight UP in the next block?

**None.** Raw signals are missing in this run. We cannot identify promising signals until attribution and blocked_trades (or backtest replay) include trend_signal, momentum_signal, volatility_signal, sector_signal, reversal_signal, breakout_signal, mean_reversion_signal.

### Which 1–3 signals look harmful enough to weight DOWN or gate harder?

**None.** Same reason: no per-signal bucket data. Do not reduce or gate signals based on this run.

### Any obvious regime-specific behaviors (e.g. trend only in BULL)?

**No.** Regimes in this run are MIXED (majority) and UNKNOWN (small). We do not have BULL / BEAR / RANGE. Regime-specific behavior will be answerable only after (1) real signal fields are present and (2) regime labels include BULL/BEAR/RANGE where applicable.

---

## 3. Next steps

1. **Option A — Wait for live data:** Run the bot with Block 3E for a full 30 days in the backtest window, then re-run the 30d backtest and Signal Edge Analysis.  
2. **Option B — Replay-time signals:** Extend the backtest script to compute market_context (and thus raw signals) at each entry/block timestamp during replay and merge them into the written backtest_trades.jsonl and backtest_blocks.jsonl so that the first “true” signal edge backtest does not depend on live log history.  
3. After a run **with** full signal data, re-run this multi-AI review to answer: weight up (1–3 signals), weight down (1–3 signals), and regime-specific behavior.
