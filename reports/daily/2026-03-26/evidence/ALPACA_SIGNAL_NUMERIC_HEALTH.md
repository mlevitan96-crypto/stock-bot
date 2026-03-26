# ALPACA SIGNAL NUMERIC HEALTH (QSA)
Generated: 2026-03-19T17:29:26.124922+00:00

## Summary
- **run.jsonl sampled:** last 2110 records (tail 3000)
- **State files checked:** regime_posture_state, market_context_v2, symbol_risk_features

## Numeric integrity
- **Null/NaN/inf/sentinel:** PASS — 0 issues
- **Out-of-range:** 0 issues
- **Constant-zero signals:** None detected
- **Saturated signals:** None detected

## State files
{
  "source": "regime_posture",
  "path": "/root/stock-bot/state/regime_posture_state.json",
  "keys_sample": [
    "ts",
    "regime_label",
    "regime_confidence",
    "regime_source",
    "structural_regime",
    "structural_confidence",
    "posture",
    "posture_flags",
    "market_context"
  ]
}
{
  "source": "market_context",
  "path": "/root/stock-bot/state/market_context_v2.json",
  "keys_sample": [
    "timestamp",
    "spy_prev_close",
    "spy_last_1m",
    "spy_overnight_ret",
    "qqq_prev_close",
    "qqq_last_1m",
    "qqq_overnight_ret",
    "vxx_close_1d",
    "vxz_close_1d",
    "vxx_vxz_ratio",
    "spy_last_1m_ts",
    "qqq_last_1m_ts",
    "stale_1m",
    "stale_reason",
    "market_trend"
  ]
}
{
  "source": "symbol_risk",
  "path": "/root/stock-bot/state/symbol_risk_features.json",
  "keys_sample": [
    "_meta",
    "symbols"
  ]
}

## Issues (sample)

