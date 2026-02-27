# 07 Logs and attribution flow

## attribution.jsonl
- Line count: 2253 logs/attribution.jsonl
- Last record ts: 2026-02-18T17:25:49
Last 3 lines (sample):
```
{"ts": "2026-02-18T17:24:39.668120+00:00", "type": "attribution", "trade_id": "open_F_2026-02-18T17:24:39.667377+00:00", "symbol": "F", "pnl_usd": 0.0, "context": {"direction": "bullish", "gamma_regime": "neutral", "market_regime": "mixed", "score": 8.3, "order_type": "market", "intel_snapshot": {"v2_inputs": {"realized_vol_20d": 0.189167, "beta_vs_spy": 0.841633, "uw_conviction": 1.0, "trade_count": 100, "volatility_regime": "mid", "market_trend": "", "futures_direction": "flat", "spy_overnight_ret": 0.0, "qqq_overnight_ret": 0.0, "posture": "neutral", "direction": "bullish", "posture_confidence": 0.0, "weights_version": "2026-01-20_wt1"}, "v2_uw_inputs": {}, "v2_uw_sector_profile": {}, "v2_uw_regime_profile": {}, "uw_intel_version": ""}, "entry_ts": "2026-02-18T17:24:39.665991+00:00", "entry_status": "filled", "entry_price": 14.09, "entry_qty": 5, "qty": 5, "pending_fill": false, "entry_price_source": "alpaca.order.filled_avg_price", "entry_score": 8.3, "components": {"flow": 2.4, "dark_pool": 0.181, "insider": 0.087, "iv_skew": 0.082, "smile": 0.005, "whale": 0.0, "event": 0.237, "motif_bonus": 0.0, "toxicity_penalty": -0.188, "regime": 0.008, "congress": 0.0, "shorts_squeeze": 0.0, "institutional": 0.0, "market_tide": 8.249, "calendar": 0.0, "greeks_gamma": 0.14, "ftd_pressure": 0.042, "iv_rank": 0.07, "oi_change": 0.049, "etf_flow": 0.042, "squeeze_score": 0.07, "freshness_factor": 0.976}, "regime": "mixed", "position_side": "long", "first_signal_ts_utc": null, "metadata
```

## exit_attribution.jsonl
- Line count: 2000 logs/exit_attribution.jsonl
- Last record ts: 2026-02-18T17:25:49
Last 3 lines (sample):
```
{"symbol": "XLE", "timestamp": "2026-02-18T17:24:15.459641+00:00", "entry_timestamp": "2026-02-18T17:24:06.546799+00:00", "exit_reason": "signal_decay(0.96)", "pnl": -0.0999999999999801, "pnl_pct": -0.018331805682856115, "entry_price": 54.55, "exit_price": 54.54, "qty": 10.0, "time_in_trade_minutes": 0.14854736666666665, "entry_uw": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sentiment": "BULLISH", "earnings_proximity": 3, "sector_alignment": 0.1, "regime_alignment": -1.0, "uw_intel_version": "2026-01-20_uw_v1"}, "exit_uw": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sentiment": "BULLISH", "earnings_proximity": 3, "sector_alignment": 0.1, "regime_alignment": -1.0, "uw_intel_version": "2026-01-20_uw_v1"}, "entry_regime": "BEAR", "exit_regime": "BEAR", "entry_sector_profile": {"sector": "ENERGY", "version": "2026-01-20_sector_profiles_v1", "multipliers": {"flow_weight": 1.0, "darkpool_weight": 1.0, "earnings_weight": 0.9, "short_interest_weight": 1.0}}, "exit_sector_profile": {"sector": "ENERGY", "version": "2026-01-20_sector_profiles_v1", "multipliers": {"flow_weight": 1.0, "darkpool_weight": 1.0, "earnings_weight": 0.9, "short_interest_weight": 1.0}}, "score_deterioration": 0.3000000000000007, "relative_strength_deterioration": 0.0, "v2_exit_score": 0.10937500000000003, "v2_exit_components": {"flow_deterioration": 0.0, "darkpool_deterioration": 0.0, "sentiment_deterioration": 0.0, "score_deterioration": 0.0375, "regime_shift": 0.0, "sector_shift": 0.0, "vol_expansion": 1.
```

## Join keys
Expect trade_id (or equivalent) on both sides for join.