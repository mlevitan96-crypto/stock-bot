# Alpaca Quant Lab — Feature & Signal Inventory (QSA)

**Mission:** Phase 1 — Enumerate all available features; quantify coverage, redundancy, correlation clusters.  
**Authority:** QSA (quant/stat).  
**Date:** 2026-03-18.

---

## 1. Price / Volume Indicators

| Feature | Source | Grain | Coverage | Notes |
|---------|--------|--------|----------|--------|
| **Bar OHLCV** | data/bars_cache, Alpaca API | symbol, date, resolution (1Min, 5Min, 15Min) | Per symbol/date when cached | Used for path-real counterfactuals, MFE/MAE. |
| **realized_vol_5d, realized_vol_20d** | state/symbol_risk_features.json, structural_intelligence | Per symbol | Best-effort; may be stale when market closed. | Feature snapshot, vol expansion in exit. |
| **beta_vs_spy** | state/symbol_risk_features.json | Per symbol | Best-effort. | Feature snapshot. |
| **premarket_gap, premarket_relvol** | state/market_context_v2.json | Time snapshot | When market context updated. | feature_snapshot. |

**Coverage:** Bars = per-trade when step2 runs and cache exists. Vol/beta = symbol-level state; not per-trade unless attached to snapshot.

---

## 2. Entry Composite (V2) — Components

All from `uw_composite_v2.py` (WEIGHTS_V3). One composite score per decision; components logged in attribution / master_trade_log when captured.

| Component (signal_id / name) | Base weight | Description |
|-------------------------------|-------------|-------------|
| options_flow | 2.4 | Flow conviction (flow_conv); protected floor. |
| dark_pool | 1.3 | Dark pool strength. |
| insider | 0.5 | Insider band (0.25–0.75). |
| iv_term_skew | 0.6 | IV term structure skew. |
| smile_slope | 0.35 | Smile slope. |
| whale_persistence | 0.7 | Whale detection boost. |
| event_alignment | 0.4 | Event alignment. |
| toxicity_penalty | -0.9 | Toxicity penalty. |
| temporal_motif | 0.6 | Staircase/motif. |
| regime_modifier | 0.3 | Regime factor. |
| congress | 0.9 | Congress/politician trading. |
| shorts_squeeze | 0.7 | Short interest / squeeze. |
| institutional | 0.5 | 13F / institutional. |
| market_tide | 0.4 | Options market sentiment. |
| calendar_catalyst | 0.45 | Earnings/FDA/economic. |
| greeks_gamma | 0.4 | Gamma exposure. |
| ftd_pressure | 0.3 | Fails-to-deliver. |
| iv_rank | 0.2 | IV rank. |
| oi_change | 0.35 | Open interest change. |
| etf_flow | 0.3 | ETF flow. |
| squeeze_score | 0.2 | Combined squeeze. |

**Coverage:** Per trade when entry/exit attribution or master_trade_log carries component breakdown; otherwise aggregate score only (see Phase 0 join coverage).

---

## 3. Regime Labels

| Feature | Source | Values | Coverage |
|---------|--------|--------|----------|
| regime_label (posture) | state/regime_posture_state.json | bull, bear, chop, crash | Time snapshot. |
| regime (intel) | state/regime_state.json | RISK_ON, RISK_OFF, NEUTRAL, BEAR, MIXED | Time snapshot. |
| structural_regime | state/regime_detector_state.json | RISK_ON, NEUTRAL, RISK_OFF, PANIC | Time snapshot. |
| entry_regime, exit_regime | exit_attribution, TRADES_FROZEN | As at entry/exit time | Per trade when logged. |

---

## 4. Volatility Measures

| Feature | Source | Grain |
|---------|--------|--------|
| realized_vol_5d, realized_vol_20d | symbol_risk_features | Symbol. |
| vol_expansion (exit) | exit_score_v2 (derived from realized_vol_20d) | Per exit. |
| volatility_regime | market_context_v2 | Time (low/mid/high). |

---

## 5. Market Breadth Proxies

- **market_trend**, **risk_on_off**, **spy_overnight_ret**, **qqq_overnight_ret**, **vxx_vxz_ratio** in market_context_v2.
- **Market tide** in composite = options market sentiment (UW-derived).

No separate breadth index (e.g. advance/decline); proxies only.

---

## 6. Time-of-Day / Session State

| Feature | Source | Notes |
|---------|--------|--------|
| entry_time, exit_time | TRADES_FROZEN, exit_attribution | UTC; second precision. |
| time_in_trade_minutes | exit_attribution | Hold duration. |
| Session (RTH/ETH) | Derived from timestamps + market hours | Not a stored field. |
| premarket / postmarket | market_context, premarket_intel, postmarket_intel | State files. |

---

## 7. Symbol Metadata

| Feature | Source | Notes |
|---------|--------|--------|
| symbol | All trade/attribution records | Identity. |
| side (LONG/SHORT) | TRADES_FROZEN, exit_attribution | Direction. |
| sector | sector_profiles.json, sector_intel | Best-effort. |
| in_v2_universe | daily_universe_v2 | Universe membership. |

---

## 8. Exit-Side Features (Attribution)

Exit score components (exit_score_v2); all use **exit_** prefix in attribution_components:

- exit_flow_deterioration, exit_darkpool_deterioration, exit_sentiment_deterioration  
- exit_score_deterioration, exit_regime_shift, exit_sector_shift  
- exit_vol_expansion, exit_thesis_invalidated, exit_earnings_risk, exit_overnight_flow_risk  

**Coverage:** Per closed trade when exit attribution is written (exit_attribution.jsonl).

---

## 9. Redundancy & Correlation (Summary)

- **Regime:** Multiple regime sources (posture, intel, structural); often aligned; use single canonical per analysis (e.g. entry_regime/exit_regime from exit_attribution).
- **Flow vs dark pool:** Both UW-derived; can be correlated; separate weights in composite.
- **IV family:** iv_term_skew, smile_slope, iv_rank — related; separate components.
- **Squeeze family:** shorts_squeeze, ftd_pressure, squeeze_score, greeks_gamma — overlap in squeeze/positioning; consider correlation cluster in feature selection.
- **Entry vs exit:** Entry composite and exit score are different models; no redundancy, but both should be used for full attribution.

**Recommendation:** For profit discovery (Phase 4), treat entry components as a feature set and exit_* as another; optionally cluster (e.g. flow/dp, iv family, squeeze family) to reduce multicollinearity in models.
