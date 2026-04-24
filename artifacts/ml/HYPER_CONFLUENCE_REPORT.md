# Hyper-Confluence Manifold Report

**Generated:** `scripts/ml/hyper_confluence_engine.py`

## 1. Data inventory
- **Cohort:** `C:\Dev\stock-bot\reports\Gemini\alpaca_ml_cohort_flat.csv`
- **Rows (clean):** 629
- **Base theory columns:** 11
- **Cross features (3/4/5-way products):** 360 (capped per order)
- **Blocked intents sampled:** 23 (from `logs/run.jsonl` tail)

## 2. Gradient boosted manifold (XGBoost regressor → realized PnL USD)
- **Test MAE (USD):** 2.3592
- **Test Spearman(pred, y):** 0.2043

### Top 12 gain features
- `hc__mlf_scoreflow_components_dark_pool__mlf_scoreflow_components_iv_skew__mlf_entry_uw_sentiment_score__mlf_scoreflow_components_toxicity_penalty__mlf_direction_intel_embed_intel_snapshot_entry_volati` — gain 71.0
- `hc__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score__mlf_direction_intel_embed_intel_snapshot_entry_volatility_intel_realized_vol_20d` — gain 35.2
- `hc__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score__mlf_direction_intel_embed_intel_snapshot_entry_volatility_intel_realized_v` — gain 31.9
- `hc__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score` — gain 20.3
- `mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_spy_overnight_ret` — gain 19.2
- `hc__mlf_scoreflow_components_dark_pool__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score` — gain 18.0
- `hc__mlf_scoreflow_components_iv_skew__mlf_entry_uw_sentiment_score__mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_spy_overnight_ret` — gain 11.4
- `hc__mlf_entry_uw_flow_strength__mlf_scoreflow_components_flow__mlf_direction_intel_embed_intel_snapshot_entry_volatility_intel_realized_vol_20d` — gain 11.3
- `hc__mlf_entry_uw_flow_strength__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew` — gain 11.0
- `hc__mlf_scoreflow_components_dark_pool__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_spy_overnight_ret` — gain 10.2
- `hc__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score` — gain 9.5
- `hc__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_scoreflow_components_toxicity_penalty__mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_spy_overnight_r` — gain 9.0

## 3. High-order sensitivity (triads & quartets)
_Method:_ `mean_abs_shap_top_gain_columns` — product of per-feature masses over the top-8 gain columns (SHAP mean-|value| when available; else sklearn `permutation_importance`). This ranks **which simultaneous feature bundle** the booster leans on; it is **not** the full SHAP interaction tensor (omitted here for XGBoost+SHAP stability on wide models).
### Top triads (3-way geometric mass)
- **0.0019** — `hc__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score :: mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_spy_overnight_ret :: hc__mlf_scoreflow_components_dark_pool__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score`
- **0.0013** — `hc__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score :: mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_spy_overnight_ret :: hc__mlf_scoreflow_components_iv_skew__mlf_entry_uw_sentiment_score__mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_spy_overnight_ret`
- **0.0012** — `hc__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score :: mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_spy_overnight_ret :: hc__mlf_entry_uw_flow_strength__mlf_scoreflow_components_flow__mlf_direction_intel_embed_intel_snapshot_entry_volatility_intel_realized_vol_20d`
- **9.5715e-04** — `hc__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score__mlf_direction_intel_embed_intel_snapshot_entry_volatility_intel_realized_v :: hc__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score :: mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_spy_overnight_ret`
- **6.6887e-04** — `hc__mlf_scoreflow_components_dark_pool__mlf_scoreflow_components_iv_skew__mlf_entry_uw_sentiment_score__mlf_scoreflow_components_toxicity_penalty__mlf_direction_intel_embed_intel_snapshot_entry_volati :: hc__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score :: mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_spy_overnight_ret`

### Top quartets
- **2.2256e-05** — `hc__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score::mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_spy_overnight_ret::hc__mlf_scoreflow_components_dark_pool__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score::hc__mlf_scoreflow_components_iv_skew__mlf_entry_uw_sentiment_score__mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_spy_overnight_ret`
- **2.1498e-05** — `hc__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score::mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_spy_overnight_ret::hc__mlf_scoreflow_components_dark_pool__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score::hc__mlf_entry_uw_flow_strength__mlf_scoreflow_components_flow__mlf_direction_intel_embed_intel_snapshot_entry_volatility_intel_realized_vol_20d`
- **1.6824e-05** — `hc__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score__mlf_direction_intel_embed_intel_snapshot_entry_volatility_intel_realized_v::hc__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score::mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_spy_overnight_ret::hc__mlf_scoreflow_components_dark_pool__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score`
- **1.4208e-05** — `hc__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score::mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_spy_overnight_ret::hc__mlf_scoreflow_components_iv_skew__mlf_entry_uw_sentiment_score__mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_spy_overnight_ret::hc__mlf_entry_uw_flow_strength__mlf_scoreflow_components_flow__mlf_direction_intel_embed_intel_snapshot_entry_volatility_intel_realized_vol_20d`
- **1.1757e-05** — `hc__mlf_scoreflow_components_dark_pool__mlf_scoreflow_components_iv_skew__mlf_entry_uw_sentiment_score__mlf_scoreflow_components_toxicity_penalty__mlf_direction_intel_embed_intel_snapshot_entry_volati::hc__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score::mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_spy_overnight_ret::hc__mlf_scoreflow_components_dark_pool__mlf_scoreflow_components_flow__mlf_scoreflow_components_iv_skew__mlf_scoreflow_total_score__mlf_entry_uw_sentiment_score`

## 4. Manifold projection (t-SNE 3D)
t-SNE 3D on top-50 gain features, n=500, perplexity=30. Top-decile PnL mean=3.5463 vs bottom-decile mean=-5.7446.

## 5. Lost World — blocked intents vs hyper-volumes
Counterfactual PnL for blocked rows requires joining each intent timestamp to post-trade outcomes (replay or forward marks). **Heuristic audit:** compare `blocked_reason` histogram to top gain crosses; if `score_below_min` dominates while crosses show edge, floor may be mis-calibrated vs confluence.

| blocked_reason (top) | count |
|---|---:|
| score_below_min | 19 |
| displacement_blocked | 4 |

## 6. Grand Unified Theory (single 4-ingredient recipe)
_Operational definition:_ the four base signals named in the **top quartet** above (or, if absent, the first four theories inside the **#1 gain cross** `hc__…`). Validate OOS; descriptive only.

1. **scoreflow components flow * scoreflow components iv skew * scoreflow total score * entr...**
2. **direction intel embed intel snapshot entry regime posture market context spy overnight ret**
3. **scoreflow components dark pool * scoreflow components flow * scoreflow components iv sk...**
4. **scoreflow components iv skew * entry uw sentiment score * direction intel embed intel s...**

---
*This report is descriptive, not prescriptive for live routing. Validate on hold-out eras.*