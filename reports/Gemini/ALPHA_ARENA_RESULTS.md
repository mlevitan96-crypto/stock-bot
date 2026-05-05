# Alpha Arena — Local Research Run

- **CSV:** `reports/Gemini/alpaca_ml_cohort_flat.csv`
- **Regression target (exported RF):** `realized_pnl_usd` — _column_present_in_csv_
- **Rows / features (after filters):** 549 / 42

## Classification head (win vs loss on realized PnL, 5-fold OOF)

Separate **RandomForestClassifier** on the same `X`, label = (`realized_pnl_usd` > 0) on fit rows. Metrics from out-of-fold `predict_proba` vs labels (not the exported regressor).

- **ROC AUC (mean OOF):** 0.6715296597410418
- **Precision @0.5:** 0.48095238095238096
- **Recall @0.5:** 0.5611111111111111
- **Note:** ok

## Top 10 features by mean |SHAP| (regressor on export target)

| Rank | Feature | mean \|SHAP\| | mean signed SHAP |
| ---: | --- | ---: | ---: |
| 1 | `mlf_direction_intel_embed_intel_deltas_futures_direction_delta` | 0.137485 | -0.000538266 |
| 2 | `mlf_scoreflow_total_score` | 0.128635 | -0.0133165 |
| 3 | `mlf_scoreflow_snapshot_age_sec` | 0.0892067 | 0.00954629 |
| 4 | `mlf_scoreflow_components_oi_change` | 0.0615798 | -0.00289058 |
| 5 | `mlf_direction_intel_embed_intel_snapshot_entry_futures_intel_futures_trend_strength` | 0.0446314 | 0.00445837 |
| 6 | `mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_vxx_vxz_ratio` | 0.0410775 | 0.0096561 |
| 7 | `mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_qqq_overnight_ret` | 0.0337019 | -0.00651085 |
| 8 | `mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_spy_overnight_ret` | 0.0331928 | 0.00423309 |
| 9 | `mlf_scoreflow_components_freshness_factor` | 0.0327373 | -0.000561107 |
| 10 | `uw_gamma_skew` | 0.030063 | -0.00060754 |

## Commander: loss tilt (regressor SHAP sign)

- **#1 most penalizing feature (lowest mean signed SHAP on target `realized_pnl_usd`):** `mlf_scoreflow_total_score` (mean signed SHAP = **-0.0133165** — pushes predicted target **down** on average across this cohort).
