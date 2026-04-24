# ALPACA METADATA TRUTH AUDIT

Required field checklist (per open symbol): ['entry_score', 'entry_reason', 'market_regime', 'variant_id', 'v2']

## AAPL

- entry_score: `4.697`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:14:18.762536+00:00",
  "entry_price": 246.12,
  "qty": 1,
  "side": "sell",
  "entry_score": 4.697,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.626,
    "insider": 0.301,
    "iv_skew": 0.152,
    "smile": 0.017,
    "whale": 0.0,
    "event": 0.818,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.65,
    "regime": 0.029,
    "congress": 0.173,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.267,
    "calendar": 0.0,
    "greeks_gamma": 0.193,
    "ftd_pressure": 0.144,
    "iv_rank": 0.241,
    "oi_change": 0.168,
    "etf_flow": 0.144,
    "squeeze_score": 0.096,
    "freshness_factor": 0.998
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.252422,
      "beta_vs_spy": 1.29645,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 17.912,
    "timestamp": 1774898058.8142498
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:14:18.847627",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "c8683e9f-a894-4552-bd7a-284bd4f6fb95",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## AMD

- entry_score: `5.306`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:12:42.473460+00:00",
  "entry_price": 193.68,
  "qty": 1,
  "side": "sell",
  "entry_score": 5.306,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.59,
    "insider": 0.284,
    "iv_skew": 0.143,
    "smile": 0.016,
    "whale": 0.0,
    "event": 0.772,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.613,
    "regime": 0.027,
    "congress": 0.041,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.195,
    "calendar": 0.0,
    "greeks_gamma": 0.454,
    "ftd_pressure": 0.136,
    "iv_rank": 0.227,
    "oi_change": 0.159,
    "etf_flow": 0.136,
    "squeeze_score": 0.091,
    "freshness_factor": 1.0
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.813192,
      "beta_vs_spy": 2.477311,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 20.33,
    "timestamp": 1774897962.547518
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:12:42.573046",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "1008203b-c164-4b6a-8ed6-56a595e06e8b",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## BAC

- entry_score: `4.547`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:16:39.299606+00:00",
  "entry_price": 47.05,
  "qty": 4,
  "side": "sell",
  "entry_score": 4.547,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.626,
    "insider": 0.301,
    "iv_skew": 0.152,
    "smile": 0.017,
    "whale": 0.0,
    "event": 0.818,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.65,
    "regime": 0.029,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.267,
    "calendar": 0.0,
    "greeks_gamma": 0.481,
    "ftd_pressure": 0.144,
    "iv_rank": 0.072,
    "oi_change": 0.168,
    "etf_flow": 0.144,
    "squeeze_score": 0.096,
    "freshness_factor": 0.998
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.242708,
      "beta_vs_spy": 0.602173,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 27.892,
    "timestamp": 1774898199.3546164
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:16:39.408226",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:16:05.564486+00:00",
    "spy_prev_close": 630.15,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.010918035388399581,
    "qqq_prev_close": 556.36,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.015008268027895648,
    "vxx_close_1d": 39.7388,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6408450249959684,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:16:06.231790+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.010918035388399581,
      "qqq_overnight_ret": 0.015008268027895648,
      "vxx_vxz_ratio": 0.6408450249959684,
      "stale_1m": true
    }
  },
  "entry_order_id": "a6aa0653-d32e-4a2a-bd2e-ae948cc02acb",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## C

- entry_score: `4.746`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:14:10.334302+00:00",
  "entry_price": 106.59,
  "qty": 2,
  "side": "sell",
  "entry_score": 4.746,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.59,
    "insider": 0.284,
    "iv_skew": 0.143,
    "smile": 0.016,
    "whale": 0.0,
    "event": 0.772,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.613,
    "regime": 0.027,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.195,
    "calendar": 0.0,
    "greeks_gamma": 0.454,
    "ftd_pressure": 0.136,
    "iv_rank": 0.068,
    "oi_change": 0.159,
    "etf_flow": 0.136,
    "squeeze_score": 0.091,
    "freshness_factor": 0.993
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.31195,
      "beta_vs_spy": 1.612222,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 11.747,
    "timestamp": 1774898050.383919
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:14:10.412936",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "9473ee67-474c-49b0-854e-7d1bc74ae4b3",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## COIN

- entry_score: `4.656`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:14:43.308709+00:00",
  "entry_price": 158.98,
  "qty": 2,
  "side": "sell",
  "entry_score": 4.656,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.59,
    "insider": 0.284,
    "iv_skew": 0.143,
    "smile": 0.016,
    "whale": 0.0,
    "event": 0.772,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.613,
    "regime": 0.027,
    "congress": 0.082,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.195,
    "calendar": 0.0,
    "greeks_gamma": 0.227,
    "ftd_pressure": 0.136,
    "iv_rank": 0.068,
    "oi_change": 0.159,
    "etf_flow": 0.136,
    "squeeze_score": 0.091,
    "freshness_factor": 0.985
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.428492,
      "beta_vs_spy": 1.180758,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 15.125,
    "timestamp": 1774898083.3605568
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:14:43.393070",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "8f6d38a0-06e5-457d-83f0-6d845e9d80fb",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## COP

- entry_score: `4.873`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:13:30.923344+00:00",
  "entry_price": 132.21,
  "qty": 2,
  "side": "sell",
  "entry_score": 4.873,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.626,
    "insider": 0.301,
    "iv_skew": 0.152,
    "smile": 0.017,
    "whale": 0.0,
    "event": 0.818,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.65,
    "regime": 0.029,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.267,
    "calendar": 0.0,
    "greeks_gamma": 0.481,
    "ftd_pressure": 0.144,
    "iv_rank": 0.241,
    "oi_change": 0.168,
    "etf_flow": 0.144,
    "squeeze_score": 0.096,
    "freshness_factor": 0.987
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.361613,
      "beta_vs_spy": 0.01507,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 17.888,
    "timestamp": 1774898010.9739985
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:13:30.998044",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "2cec7382-1581-483c-8188-7d23652f4f37",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## CVX

- entry_score: `4.688`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:14:35.577177+00:00",
  "entry_price": 210.77,
  "qty": 1,
  "side": "sell",
  "entry_score": 4.688,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.626,
    "insider": 0.301,
    "iv_skew": 0.152,
    "smile": 0.017,
    "whale": 0.0,
    "event": 0.818,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.65,
    "regime": 0.029,
    "congress": 0.087,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.267,
    "calendar": 0.0,
    "greeks_gamma": 0.481,
    "ftd_pressure": 0.144,
    "iv_rank": 0.241,
    "oi_change": 0.168,
    "etf_flow": 0.144,
    "squeeze_score": 0.096,
    "freshness_factor": 0.987
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.201316,
      "beta_vs_spy": -0.16172,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 12.91,
    "timestamp": 1774898075.630988
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:14:35.658291",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "1d44b34a-93b1-4055-9690-106c523713be",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## F

- entry_score: `4.759`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:13:50.901480+00:00",
  "entry_price": 11.12,
  "qty": 35,
  "side": "sell",
  "entry_score": 4.759,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.59,
    "insider": 0.284,
    "iv_skew": 0.143,
    "smile": 0.016,
    "whale": 0.0,
    "event": 0.772,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.613,
    "regime": 0.027,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.195,
    "calendar": 0.0,
    "greeks_gamma": 0.454,
    "ftd_pressure": 0.136,
    "iv_rank": 0.227,
    "oi_change": 0.159,
    "etf_flow": 0.136,
    "squeeze_score": 0.091,
    "freshness_factor": 0.995
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.302054,
      "beta_vs_spy": 1.11387,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 15.366,
    "timestamp": 1774898030.9698553
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:13:50.993962",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "dc36eeda-b786-4b8f-bbb9-19c80f48480b",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## GM

- entry_score: `5.127`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:12:53.342837+00:00",
  "entry_price": 72.52,
  "qty": 2,
  "side": "sell",
  "entry_score": 5.127,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.59,
    "insider": 0.284,
    "iv_skew": 0.143,
    "smile": 0.016,
    "whale": 0.0,
    "event": 0.772,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.613,
    "regime": 0.027,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.195,
    "calendar": 0.0,
    "greeks_gamma": 0.454,
    "ftd_pressure": 0.136,
    "iv_rank": 0.227,
    "oi_change": 0.159,
    "etf_flow": 0.136,
    "squeeze_score": 0.091,
    "freshness_factor": 0.986
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.450401,
      "beta_vs_spy": 1.670275,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 18.97,
    "timestamp": 1774897973.4007208
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:12:53.425815",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "87366f15-ad42-4664-a2a1-f680e16c4880",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## GOOGL

- entry_score: `4.486`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:16:50.180554+00:00",
  "entry_price": 272.52,
  "qty": 1,
  "side": "sell",
  "entry_score": 4.486,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.626,
    "insider": 0.301,
    "iv_skew": 0.152,
    "smile": 0.017,
    "whale": 0.0,
    "event": 0.818,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.65,
    "regime": 0.029,
    "congress": 0.043,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.267,
    "calendar": 0.0,
    "greeks_gamma": 0.193,
    "ftd_pressure": 0.144,
    "iv_rank": 0.241,
    "oi_change": 0.168,
    "etf_flow": 0.144,
    "squeeze_score": 0.096,
    "freshness_factor": 0.995
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.207949,
      "beta_vs_spy": 1.309889,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 27.107,
    "timestamp": 1774898210.2337687
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:16:50.266391",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:16:05.564486+00:00",
    "spy_prev_close": 630.15,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.010918035388399581,
    "qqq_prev_close": 556.36,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.015008268027895648,
    "vxx_close_1d": 39.7388,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6408450249959684,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:16:06.231790+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.010918035388399581,
      "qqq_overnight_ret": 0.015008268027895648,
      "vxx_vxz_ratio": 0.6408450249959684,
      "stale_1m": true
    }
  },
  "entry_order_id": "d4c80690-8248-4303-9b9f-089723ff2f8a",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## HOOD

- entry_score: `5.016`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:12:57.271272+00:00",
  "entry_price": 63.65,
  "qty": 6,
  "side": "sell",
  "entry_score": 5.016,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.59,
    "insider": 0.284,
    "iv_skew": 0.143,
    "smile": 0.016,
    "whale": 0.0,
    "event": 0.772,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.613,
    "regime": 0.027,
    "congress": 0.041,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.195,
    "calendar": 0.0,
    "greeks_gamma": 0.454,
    "ftd_pressure": 0.136,
    "iv_rank": 0.227,
    "oi_change": 0.159,
    "etf_flow": 0.136,
    "squeeze_score": 0.091,
    "freshness_factor": 0.994
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.500099,
      "beta_vs_spy": 0.643167,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 18.659,
    "timestamp": 1774897977.3244207
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:12:57.359033",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "1c517e96-a202-4f4d-99ed-eccde73d9ead",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## INTC

- entry_score: `4.85`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:13:33.024647+00:00",
  "entry_price": 40.8,
  "qty": 4,
  "side": "sell",
  "entry_score": 4.85,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.59,
    "insider": 0.284,
    "iv_skew": 0.143,
    "smile": 0.016,
    "whale": 0.0,
    "event": 0.772,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.613,
    "regime": 0.027,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.195,
    "calendar": 0.0,
    "greeks_gamma": 0.454,
    "ftd_pressure": 0.136,
    "iv_rank": 0.068,
    "oi_change": 0.159,
    "etf_flow": 0.136,
    "squeeze_score": 0.091,
    "freshness_factor": 0.982
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 1.079104,
      "beta_vs_spy": 1.276029,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 19.11,
    "timestamp": 1774898013.0762963
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:13:33.107121",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "20462f2e-8ac8-4ba4-b9a2-31156b1154e2",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## JPM

- entry_score: `4.556`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:15:25.201078+00:00",
  "entry_price": 282.93,
  "qty": 1,
  "side": "sell",
  "entry_score": 4.556,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.626,
    "insider": 0.301,
    "iv_skew": 0.152,
    "smile": 0.017,
    "whale": 0.0,
    "event": 0.818,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.65,
    "regime": 0.029,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.267,
    "calendar": 0.0,
    "greeks_gamma": 0.481,
    "ftd_pressure": 0.144,
    "iv_rank": 0.072,
    "oi_change": 0.168,
    "etf_flow": 0.144,
    "squeeze_score": 0.096,
    "freshness_factor": 0.992
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.260228,
      "beta_vs_spy": 0.728566,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 11.731,
    "timestamp": 1774898125.2521822
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:15:25.281903",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "d5872e0b-c458-49b7-b012-8110650568b9",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## MRNA

- entry_score: `4.886`
- entry_reason: `None`
- regime: `None`
- variant: `None`
- v2 keys: `None`
- **Flags:** entry_reason missing; regime missing; variant missing; v2 snapshot missing or empty

```json
{
  "entry_ts": "2026-03-30T19:16:01.031197Z",
  "entry_price": 47.29,
  "qty": -8,
  "side": "short",
  "entry_score": 4.886,
  "recovered_from": "continuous_health_check",
  "unrealized_pl": 0.12,
  "reconciled_at": "2026-03-30T19:16:01.031230Z"
}
```

## MS

- entry_score: `4.781`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:13:48.538156+00:00",
  "entry_price": 157.48,
  "qty": 2,
  "side": "sell",
  "entry_score": 4.781,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.59,
    "insider": 0.284,
    "iv_skew": 0.143,
    "smile": 0.016,
    "whale": 0.0,
    "event": 0.772,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.613,
    "regime": 0.027,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.195,
    "calendar": 0.0,
    "greeks_gamma": 0.454,
    "ftd_pressure": 0.136,
    "iv_rank": 0.068,
    "oi_change": 0.159,
    "etf_flow": 0.136,
    "squeeze_score": 0.091,
    "freshness_factor": 0.993
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.304343,
      "beta_vs_spy": 1.789161,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 11.747,
    "timestamp": 1774898028.6287673
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:13:48.682423",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "c460942e-d645-4291-beed-3329d9262f01",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## MSFT

- entry_score: `4.747`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:14:00.852619+00:00",
  "entry_price": 356.7,
  "qty": 1,
  "side": "sell",
  "entry_score": 4.747,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.626,
    "insider": 0.301,
    "iv_skew": 0.152,
    "smile": 0.017,
    "whale": 0.0,
    "event": 0.818,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.65,
    "regime": 0.029,
    "congress": 0.173,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.267,
    "calendar": 0.0,
    "greeks_gamma": 0.193,
    "ftd_pressure": 0.144,
    "iv_rank": 0.072,
    "oi_change": 0.168,
    "etf_flow": 0.144,
    "squeeze_score": 0.096,
    "freshness_factor": 0.999
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.429436,
      "beta_vs_spy": 0.710867,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 17.912,
    "timestamp": 1774898040.927169
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:14:00.979274",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "6cd29ea7-22c5-4d13-8f5c-cce71ffa2357",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## NIO

- entry_score: `4.903`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:13:11.691621+00:00",
  "entry_price": 5.48,
  "qty": 72,
  "side": "sell",
  "entry_score": 4.903,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.59,
    "insider": 0.284,
    "iv_skew": 0.143,
    "smile": 0.016,
    "whale": 0.0,
    "event": 0.772,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.613,
    "regime": 0.027,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.195,
    "calendar": 0.0,
    "greeks_gamma": 0.454,
    "ftd_pressure": 0.136,
    "iv_rank": 0.227,
    "oi_change": 0.159,
    "etf_flow": 0.136,
    "squeeze_score": 0.091,
    "freshness_factor": 0.986
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.392394,
      "beta_vs_spy": 1.196758,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 18.97,
    "timestamp": 1774897991.7417293
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:13:11.768491",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "f46048a1-3643-4602-8e86-2665ec100efe",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## NVDA

- entry_score: `4.973`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:13:03.649895+00:00",
  "entry_price": 164.55,
  "qty": 2,
  "side": "sell",
  "entry_score": 4.973,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.59,
    "insider": 0.284,
    "iv_skew": 0.143,
    "smile": 0.016,
    "whale": 0.0,
    "event": 0.772,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.613,
    "regime": 0.027,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.195,
    "calendar": 0.0,
    "greeks_gamma": 0.182,
    "ftd_pressure": 0.136,
    "iv_rank": 0.454,
    "oi_change": 0.159,
    "etf_flow": 0.136,
    "squeeze_score": 0.091,
    "freshness_factor": 0.999
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.313763,
      "beta_vs_spy": 1.936026,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 16.929,
    "timestamp": 1774897983.7022896
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:13:03.729520",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "d1a6ea70-bb82-4d06-9ee8-a3b7884b3e92",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## PFE

- entry_score: `3.8291`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T18:36:23.142301+00:00",
  "entry_price": 27.62,
  "qty": 12,
  "side": "sell",
  "entry_score": 3.8291,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.26,
    "insider": 0.125,
    "iv_skew": 0.063,
    "smile": 0.007,
    "whale": 0.0,
    "event": 0.34,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.27,
    "regime": 0.012,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -0.527,
    "calendar": 0.0,
    "greeks_gamma": 0.2,
    "ftd_pressure": 0.06,
    "iv_rank": 0.1,
    "oi_change": 0.07,
    "etf_flow": 0.06,
    "squeeze_score": 0.04,
    "freshness_factor": 0.993
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.266895,
      "beta_vs_spy": 0.678787,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "bypassed_high_score",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 12.895,
    "timestamp": 1774895783.1971672
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T18:36:23.243072",
  "entry_market_context": {
    "timestamp": "2026-03-30T18:32:57.429920+00:00",
    "spy_prev_close": 632.53,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.007114287069388014,
    "qqq_prev_close": 558.9599,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.010287142244014443,
    "vxx_close_1d": 39.165,
    "vxz_close_1d": 61.68,
    "vxx_vxz_ratio": 0.6349708171206225,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T18:32:57.646744+00:00",
    "regime_label": "crash",
    "regime_confidence": 1.0,
    "regime_source": "structural_regime:RISK_OFF+high_vol",
    "structural_regime": "RISK_OFF",
    "structural_confidence": 1.0,
    "posture": "short",
    "posture_flags": {
      "allow_new_longs": false,
      "tighten_long_exits": true,
      "prefer_shorts": true
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.007114287069388014,
      "qqq_overnight_ret": 0.010287142244014443,
      "vxx_vxz_ratio": 0.6349708171206225,
      "stale_1m": true
    }
  },
  "entry_order_id": "64030883-3d6c-4e7a-9ce9-3a2ba3521d03",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## PLTR

- entry_score: `5.207`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:12:50.507733+00:00",
  "entry_price": 137.1,
  "qty": 1,
  "side": "sell",
  "entry_score": 5.207,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.59,
    "insider": 0.284,
    "iv_skew": 0.143,
    "smile": 0.016,
    "whale": 0.0,
    "event": 0.772,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.613,
    "regime": 0.027,
    "congress": 0.041,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.195,
    "calendar": 0.0,
    "greeks_gamma": 0.454,
    "ftd_pressure": 0.136,
    "iv_rank": 0.454,
    "oi_change": 0.159,
    "etf_flow": 0.136,
    "squeeze_score": 0.091,
    "freshness_factor": 0.985
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.563134,
      "beta_vs_spy": 0.162046,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 18.024,
    "timestamp": 1774897970.587884
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:12:50.623538",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "bbb5c8c7-7d95-4331-bfaa-a91dd834ea9a",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## RIVN

- entry_score: `4.616`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:15:15.301774+00:00",
  "entry_price": 14.27,
  "qty": 18,
  "side": "sell",
  "entry_score": 4.616,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.59,
    "insider": 0.284,
    "iv_skew": 0.143,
    "smile": 0.016,
    "whale": 0.0,
    "event": 0.772,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.613,
    "regime": 0.027,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.195,
    "calendar": 0.0,
    "greeks_gamma": 0.454,
    "ftd_pressure": 0.136,
    "iv_rank": 0.068,
    "oi_change": 0.159,
    "etf_flow": 0.136,
    "squeeze_score": 0.091,
    "freshness_factor": 0.994
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.329977,
      "beta_vs_spy": 0.619234,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 15.029,
    "timestamp": 1774898115.3582382
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:15:15.392716",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "7ff11bbb-d55a-4180-b862-7282e4b75d56",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## SLB

- entry_score: `4.631`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:14:49.976227+00:00",
  "entry_price": 51.45,
  "qty": 4,
  "side": "sell",
  "entry_score": 4.631,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.59,
    "insider": 0.284,
    "iv_skew": 0.143,
    "smile": 0.016,
    "whale": 0.0,
    "event": 0.772,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.613,
    "regime": 0.027,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.195,
    "calendar": 0.0,
    "greeks_gamma": 0.454,
    "ftd_pressure": 0.136,
    "iv_rank": 0.068,
    "oi_change": 0.159,
    "etf_flow": 0.136,
    "squeeze_score": 0.091,
    "freshness_factor": 0.987
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.354023,
      "beta_vs_spy": 0.575038,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 12.707,
    "timestamp": 1774898090.036075
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:14:50.103632",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "a99c7898-7f49-4303-8ae1-8a73c681a20b",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## SOFI

- entry_score: `4.878`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:13:29.369454+00:00",
  "entry_price": 14.97,
  "qty": 26,
  "side": "sell",
  "entry_score": 4.878,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.626,
    "insider": 0.301,
    "iv_skew": 0.152,
    "smile": 0.017,
    "whale": 0.0,
    "event": 0.818,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.65,
    "regime": 0.029,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.267,
    "calendar": 0.0,
    "greeks_gamma": 0.481,
    "ftd_pressure": 0.144,
    "iv_rank": 0.241,
    "oi_change": 0.168,
    "etf_flow": 0.144,
    "squeeze_score": 0.096,
    "freshness_factor": 0.994
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.349673,
      "beta_vs_spy": 0.950877,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 15.142,
    "timestamp": 1774898009.4212117
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:13:29.453792",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "879ed743-98bd-4b3a-864a-ffaeeee9ea41",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## TGT

- entry_score: `4.992`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:12:58.708007+00:00",
  "entry_price": 118.26,
  "qty": 3,
  "side": "sell",
  "entry_score": 4.992,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.59,
    "insider": 0.284,
    "iv_skew": 0.143,
    "smile": 0.016,
    "whale": 0.0,
    "event": 0.772,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.613,
    "regime": 0.027,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.195,
    "calendar": 0.0,
    "greeks_gamma": 0.454,
    "ftd_pressure": 0.136,
    "iv_rank": 0.454,
    "oi_change": 0.159,
    "etf_flow": 0.136,
    "squeeze_score": 0.091,
    "freshness_factor": 0.996
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.320831,
      "beta_vs_spy": -0.447634,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 26.568,
    "timestamp": 1774897978.7581449
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:12:58.783866",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "abef3bbd-f458-4708-ba37-1f33f28ce711",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## TSLA

- entry_score: `5.024`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:12:55.459950+00:00",
  "entry_price": 353.09,
  "qty": 1,
  "side": "sell",
  "entry_score": 5.024,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.59,
    "insider": 0.284,
    "iv_skew": 0.143,
    "smile": 0.016,
    "whale": 0.0,
    "event": 0.772,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.613,
    "regime": 0.027,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.195,
    "calendar": 0.0,
    "greeks_gamma": 0.182,
    "ftd_pressure": 0.136,
    "iv_rank": 0.454,
    "oi_change": 0.159,
    "etf_flow": 0.136,
    "squeeze_score": 0.091,
    "freshness_factor": 0.999
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.369615,
      "beta_vs_spy": 1.776519,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 16.929,
    "timestamp": 1774897975.5284927
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:12:55.552756",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "7d96db5b-bfda-430e-8cdd-8ac604ed402b",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## UNH

- entry_score: `4.546`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:15:45.641102+00:00",
  "entry_price": 260.53,
  "qty": 1,
  "side": "sell",
  "entry_score": 4.546,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.626,
    "insider": 0.301,
    "iv_skew": 0.152,
    "smile": 0.017,
    "whale": 0.0,
    "event": 0.818,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.65,
    "regime": 0.029,
    "congress": 0.043,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.267,
    "calendar": 0.0,
    "greeks_gamma": 0.096,
    "ftd_pressure": 0.144,
    "iv_rank": 0.072,
    "oi_change": 0.168,
    "etf_flow": 0.144,
    "squeeze_score": 0.096,
    "freshness_factor": 0.996
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.753798,
      "beta_vs_spy": -0.799338,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 12.97,
    "timestamp": 1774898145.698422
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:15:45.725544",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "e140cd42-53f8-482a-b2b9-acb768d7f0dc",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## WFC

- entry_score: `4.566`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:15:20.632220+00:00",
  "entry_price": 76.55,
  "qty": 2,
  "side": "sell",
  "entry_score": 4.566,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.59,
    "insider": 0.284,
    "iv_skew": 0.143,
    "smile": 0.016,
    "whale": 0.0,
    "event": 0.772,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.613,
    "regime": 0.027,
    "congress": 0.041,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.195,
    "calendar": 0.0,
    "greeks_gamma": 0.454,
    "ftd_pressure": 0.136,
    "iv_rank": 0.068,
    "oi_change": 0.159,
    "etf_flow": 0.136,
    "squeeze_score": 0.091,
    "freshness_factor": 0.993
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.277784,
      "beta_vs_spy": 1.006393,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 11.747,
    "timestamp": 1774898120.6928296
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:15:20.724758",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "5c9c1e0a-866b-4b52-908c-5292007b5beb",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## WMT

- entry_score: `4.624`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:14:58.717210+00:00",
  "entry_price": 123.55,
  "qty": 1,
  "side": "sell",
  "entry_score": 4.624,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.59,
    "insider": 0.284,
    "iv_skew": 0.143,
    "smile": 0.016,
    "whale": 0.0,
    "event": 0.772,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.613,
    "regime": 0.027,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.195,
    "calendar": 0.0,
    "greeks_gamma": 0.454,
    "ftd_pressure": 0.136,
    "iv_rank": 0.227,
    "oi_change": 0.159,
    "etf_flow": 0.136,
    "squeeze_score": 0.091,
    "freshness_factor": 0.996
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.237519,
      "beta_vs_spy": 0.234525,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 13.342,
    "timestamp": 1774898098.7895546
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:14:58.849326",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:12:29.833726+00:00",
    "spy_prev_close": 629.87,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.011367425024211295,
    "qqq_prev_close": 556.15,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.01539153106176402,
    "vxx_close_1d": 39.8281,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6422851153039832,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:12:30.122306+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.011367425024211295,
      "qqq_overnight_ret": 0.01539153106176402,
      "vxx_vxz_ratio": 0.6422851153039832,
      "stale_1m": true
    }
  },
  "entry_order_id": "e049daae-fe79-4643-b179-21f2746d4d9c",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## XLE

- entry_score: `4.511`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:16:44.392504+00:00",
  "entry_price": 61.94,
  "qty": 6,
  "side": "sell",
  "entry_score": 4.511,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.626,
    "insider": 0.301,
    "iv_skew": 0.152,
    "smile": 0.017,
    "whale": 0.0,
    "event": 0.818,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.65,
    "regime": 0.029,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.267,
    "calendar": 0.0,
    "greeks_gamma": 0.481,
    "ftd_pressure": 0.144,
    "iv_rank": 0.072,
    "oi_change": 0.168,
    "etf_flow": 0.144,
    "squeeze_score": 0.096,
    "freshness_factor": 0.997
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.22377,
      "beta_vs_spy": -0.267776,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 25.099,
    "timestamp": 1774898204.4459372
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:16:44.469659",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:16:05.564486+00:00",
    "spy_prev_close": 630.15,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.010918035388399581,
    "qqq_prev_close": 556.36,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.015008268027895648,
    "vxx_close_1d": 39.7388,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6408450249959684,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:16:06.231790+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.010918035388399581,
      "qqq_overnight_ret": 0.015008268027895648,
      "vxx_vxz_ratio": 0.6408450249959684,
      "stale_1m": true
    }
  },
  "entry_order_id": "7a4e770f-9de7-4134-bb7d-70865e99047c",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## XLF

- entry_score: `8.8`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:36:16.662910+00:00",
  "entry_price": 48.23,
  "qty": 12,
  "side": "buy",
  "entry_score": 8.8,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.626,
    "insider": 0.301,
    "iv_skew": 0.282,
    "smile": 0.017,
    "whale": 0.0,
    "event": 0.818,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.65,
    "regime": 0.029,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": 3.426,
    "calendar": 0.0,
    "greeks_gamma": 0.481,
    "ftd_pressure": 0.144,
    "iv_rank": 0.072,
    "oi_change": 0.168,
    "etf_flow": 0.144,
    "squeeze_score": 0.241,
    "freshness_factor": 0.993
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.156727,
      "beta_vs_spy": 0.81231,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bullish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bullish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 4.215,
    "timestamp": 1774899376.7268264
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:36:16.752147",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:35:51.432315+00:00",
    "spy_prev_close": 629.45,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.012042259115100368,
    "qqq_prev_close": 555.76,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.016104073700878158,
    "vxx_close_1d": 39.7096,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6403741332043219,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:35:51.675340+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.012042259115100368,
      "qqq_overnight_ret": 0.016104073700878158,
      "vxx_vxz_ratio": 0.6403741332043219,
      "stale_1m": true
    }
  },
  "entry_order_id": "6b3d6de9-0bed-41d7-9b04-7f18516b4ca9",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## XLI

- entry_score: `4.474`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:16:57.637245+00:00",
  "entry_price": 156.36,
  "qty": 1,
  "side": "sell",
  "entry_score": 4.474,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.626,
    "insider": 0.301,
    "iv_skew": 0.152,
    "smile": 0.017,
    "whale": 0.0,
    "event": 0.818,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.65,
    "regime": 0.029,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.267,
    "calendar": 0.0,
    "greeks_gamma": 0.481,
    "ftd_pressure": 0.144,
    "iv_rank": 0.072,
    "oi_change": 0.168,
    "etf_flow": 0.144,
    "squeeze_score": 0.096,
    "freshness_factor": 0.998
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.156353,
      "beta_vs_spy": 0.872288,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 26.027,
    "timestamp": 1774898217.7156594
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:16:57.772343",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:16:05.564486+00:00",
    "spy_prev_close": 630.15,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.010918035388399581,
    "qqq_prev_close": 556.36,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.015008268027895648,
    "vxx_close_1d": 39.7388,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6408450249959684,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:16:06.231790+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.010918035388399581,
      "qqq_overnight_ret": 0.015008268027895648,
      "vxx_vxz_ratio": 0.6408450249959684,
      "stale_1m": true
    }
  },
  "entry_order_id": "a69e0d76-f901-44fa-8114-ecf0403aa846",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## XLP

- entry_score: `4.474`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:17:06.959325+00:00",
  "entry_price": 81.82,
  "qty": 2,
  "side": "sell",
  "entry_score": 4.474,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.626,
    "insider": 0.301,
    "iv_skew": 0.152,
    "smile": 0.017,
    "whale": 0.0,
    "event": 0.818,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.65,
    "regime": 0.029,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.267,
    "calendar": 0.0,
    "greeks_gamma": 0.481,
    "ftd_pressure": 0.144,
    "iv_rank": 0.072,
    "oi_change": 0.168,
    "etf_flow": 0.144,
    "squeeze_score": 0.096,
    "freshness_factor": 0.998
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.147648,
      "beta_vs_spy": -0.182443,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 27.892,
    "timestamp": 1774898227.0398583
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:17:07.072924",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:16:05.564486+00:00",
    "spy_prev_close": 630.15,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.010918035388399581,
    "qqq_prev_close": 556.36,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.015008268027895648,
    "vxx_close_1d": 39.7388,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6408450249959684,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:16:06.231790+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.010918035388399581,
      "qqq_overnight_ret": 0.015008268027895648,
      "vxx_vxz_ratio": 0.6408450249959684,
      "stale_1m": true
    }
  },
  "entry_order_id": "ae94cfc8-31e2-4e50-a7f3-c1e7cb6f21b7",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```

## XOM

- entry_score: `4.566`
- entry_reason: `None`
- regime: `mixed`
- variant: `paper_aggressive`
- v2 keys: `['v2_inputs', 'v2_uw_inputs', 'v2_uw_sector_profile', 'v2_uw_regime_profile', 'uw_intel_version']`
- **Flags:** entry_reason missing

```json
{
  "strategy_id": "equity",
  "entry_ts": "2026-03-30T19:16:35.390332+00:00",
  "entry_price": 171.82,
  "qty": 1,
  "side": "sell",
  "entry_score": 4.566,
  "components": {
    "flow": 2.4,
    "dark_pool": 0.626,
    "insider": 0.301,
    "iv_skew": 0.152,
    "smile": 0.017,
    "whale": 0.0,
    "event": 0.818,
    "motif_bonus": 0.0,
    "toxicity_penalty": -0.65,
    "regime": 0.029,
    "congress": 0.0,
    "shorts_squeeze": 0.0,
    "institutional": 0.0,
    "market_tide": -1.267,
    "calendar": 0.0,
    "greeks_gamma": 0.481,
    "ftd_pressure": 0.144,
    "iv_rank": 0.072,
    "oi_change": 0.168,
    "etf_flow": 0.144,
    "squeeze_score": 0.096,
    "freshness_factor": 0.991
  },
  "v2": {
    "v2_inputs": {
      "realized_vol_20d": 0.269093,
      "beta_vs_spy": -0.426886,
      "uw_conviction": 1.0,
      "trade_count": 100,
      "volatility_regime": "mid",
      "market_trend": "",
      "futures_direction": "flat",
      "spy_overnight_ret": 0.0,
      "qqq_overnight_ret": 0.0,
      "posture": "neutral",
      "direction": "bearish",
      "posture_confidence": 0.0,
      "weights_version": "2026-01-20_wt1"
    },
    "v2_uw_inputs": {},
    "v2_uw_sector_profile": {},
    "v2_uw_regime_profile": {},
    "uw_intel_version": ""
  },
  "composite_version": "v2",
  "market_regime": "mixed",
  "direction": "bearish",
  "regime_modifier": 0.0,
  "ignition_status": "passed",
  "correlation_id": null,
  "alpha_signature": {
    "status": "computed",
    "rvol": null,
    "rsi": null,
    "put_call_ratio": 43.315,
    "timestamp": 1774898195.440471
  },
  "variant_id": "paper_aggressive",
  "updated_at": "2026-03-30T19:16:35.466906",
  "entry_market_context": {
    "timestamp": "2026-03-30T19:16:05.564486+00:00",
    "spy_prev_close": 630.15,
    "spy_last_1m": 637.03,
    "spy_overnight_ret": 0.010918035388399581,
    "qqq_prev_close": 556.36,
    "qqq_last_1m": 564.71,
    "qqq_overnight_ret": 0.015008268027895648,
    "vxx_close_1d": 39.7388,
    "vxz_close_1d": 62.01,
    "vxx_vxz_ratio": 0.6408450249959684,
    "spy_last_1m_ts": "2026-03-30T10:00:00+00:00",
    "qqq_last_1m_ts": "2026-03-30T10:01:00+00:00",
    "stale_1m": true,
    "stale_reason": "missing_or_old_1m_bars",
    "market_trend": "up",
    "volatility_regime": "high",
    "risk_on_off": "neutral"
  },
  "entry_regime_posture": {
    "ts": "2026-03-30T19:16:06.231790+00:00",
    "regime_label": "chop",
    "regime_confidence": 0.45,
    "regime_source": "default_chop",
    "structural_regime": "NEUTRAL",
    "structural_confidence": 0.5,
    "posture": "neutral",
    "posture_flags": {
      "allow_new_longs": true,
      "tighten_long_exits": false,
      "prefer_shorts": false
    },
    "market_context": {
      "market_trend": "up",
      "volatility_regime": "high",
      "risk_on_off": "neutral",
      "spy_overnight_ret": 0.010918035388399581,
      "qqq_overnight_ret": 0.015008268027895648,
      "vxx_vxz_ratio": 0.6408450249959684,
      "stale_1m": true
    }
  },
  "entry_order_id": "40f6771f-b56d-405f-86ce-ec28e1b40a2c",
  "targets": [
    {
      "pct": 0.02,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.05,
      "hit": false,
      "fraction": 0.3
    },
    {
      "pct": 0.1,
      "hit": false,
      "fraction": 0.4
    }
  ]
}
```


## Decay / learning hollow data?

If `entry_score` is zero or missing, decay ratio path is inactive (see exit audit). That is **hollow for decay-driven exits** until recovery/backfill.
