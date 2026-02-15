# Block 3G — Multi-AI Review Report

**Backtest dir:** `backtests/30d_after_signal_engine_block3g_20260215_155617`  
**Purpose:** Replay-time signal injection; multi-role read and recommendations for Block 3H.

---

## 1. What each “AI role” observed

### Proposer (observations on signals / edge)

- **This run:** Raw signals (trend, momentum, volatility, sector, reversal, breakout, mean_reversion) are **missing** in this report because this dir was produced **before** replay-time injection was merged. Only **regime_signal** (near_zero / MIXED) and **entry_score** (positive / near_zero) have non-missing buckets; both show negative expectancy (~−$0.15) and ~15% win rate.
- **Once injection runs:** The next 3g run (with merged code) will have all signal fields populated. Proposer should then read per-signal buckets (negative / near_zero / positive) and identify which signals correlate with higher win rate or expectancy and which with lower.

### Adversarial (warnings: noise, sample size, regime imbalance)

- **Sample size:** 2,243 trades is reasonable for aggregate stats; regime split is skewed (MIXED 2,233, UNKNOWN 10). Per-regime conclusions need more balanced regime counts.
- **Regime imbalance:** No BULL / BEAR / RANGE in this run; only MIXED and UNKNOWN. Regime-specific edge statements require regime diversity.
- **Noise:** Single 30d window; one run. Weight changes based on signal edge should be validated on another window or held-out period. Avoid overfitting to one backtest.

### Systems (data quality, missing fields, bucket distribution)

- **Data quality:** Backtest loader and Signal Edge Analysis handle missing signal fields without crash; buckets show "missing" as expected. Backward compatibility confirmed.
- **Replay-time injection:** Implemented in `scripts/replay_signal_injection.py` and wired into `run_30d_backtest_droplet.py`. Uses `data.bars_loader` and `raw_signal_engine.build_raw_signals`. Missing bars → safe defaults (0.0); no KeyErrors.
- **Bucket distribution:** Once injection runs, sanity-check that no single bucket has 0 trades and that positive/negative/near_zero are reasonably balanced; flag if any signal is 100% one bucket.

### Safety (overfitting, conservative next steps)

- **Do not change weights based on this run.** This run has no per-signal data; changing weights would be unjustified.
- **When full signal data exists:** Any weight-up/weight-down or gating decision for Block 3H should be conservative and validated (e.g. second window or out-of-sample). Prefer small adjustments.
- **Recommendation:** Treat this 3g run as pipeline validation. Use the **next** 3g run (with injection) for the first true per-signal, per-regime recommendations.

---

## 2. Final recommendations (for Block 3H)

### 1–3 signals to weight UP in Block 3H

**Deferred.** Raw signals are missing in this run. After the next 3g run with replay-time injection, re-run Signal Edge Analysis and identify 1–3 signals whose positive bucket (or higher bucket) shows meaningfully better win rate or expectancy than baseline.

### 1–3 signals to weight DOWN or gate harder

**Deferred.** Same reason. After full signal data is available, identify 1–3 signals whose negative bucket (or harmful bucket) shows meaningfully worse expectancy; consider reducing weight or gating.

### Regime-specific adjustments

**Deferred.** Regimes in this run are MIXED and UNKNOWN only. Once BULL/BEAR/RANGE appear and per-signal buckets are populated, recommend regime-specific adjustments (e.g. trend up in BULL, reversal up in RANGE).

---

## 3. Next steps

1. **Re-run 3g backtest** on the droplet (with merged Block 3G code) so that `backtest_trades.jsonl` and `backtest_blocks.jsonl` have all signal fields populated.
2. **Re-run Signal Edge Analysis** on that new 3g dir; confirm SIGNAL_EDGE_ANALYSIS_REPORT.md has per-signal edge tables with no "missing" buckets (except where data is truly absent).
3. **Update this multi-AI report** (or create one for the new dir) with concrete 1–3 weight-up, 1–3 weight-down, and regime-specific recommendations for Block 3H.
