# UW Score Contribution (Features → Score)

**Generated:** 2026-01-28T16:44:56.247012+00:00
**Window:** last 30 min
**trade_intent count:** 405

**Component names with non-zero in samples:**
dark_pool, etf_flow, event, flow, freshness_factor, ftd_pressure, greeks_gamma, insider, iv_rank, iv_skew, market_tide, oi_change, regime, smile, squeeze_score, toxicity_penalty

**UW-sourced (inferred):** flow, dark_pool, oi_change, iv_rank, market_tide, insider, greeks_gamma, etf_flow

## Sample score_components (last trade_intent)
```json
{
  "flow": 2.4,
  "dark_pool": 0.164,
  "insider": 0.079,
  "iv_skew": 0.04,
  "smile": 0.004,
  "whale": 0.0,
  "event": 0.214,
  "motif_bonus": 0.0,
  "toxicity_penalty": -0.17,
  "regime": 0.008,
  "congress": 0.0,
  "shorts_squeeze": 0.0,
  "institutional": 0.0,
  "market_tide": -0.056,
  "calendar": 0.0,
  "greeks_gamma": 0.126,
  "ftd_pressure": 0.038,
  "iv_rank": 0.126,
  "oi_change": 0.044,
  "etf_flow": 0.038,
  "squeeze_score": 0.025,
  "freshness_factor": 0.885
}
```