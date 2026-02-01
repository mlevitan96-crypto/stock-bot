# V2 Tuning Suggestions — 2026-01-23

## Scope
- Suggestions only (no auto-tuning). Apply manually by adjusting `COMPOSITE_WEIGHTS_V2['uw']` weight multipliers.

## Suggested UW weight nudges (multipliers)
- No P&L summary available yet (or no matches).

## Rationale (best-effort)
- Uses `state/uw_intel_pnl_summary.json` aggregates and a tail of `logs/uw_attribution.jsonl` to contextualize what the model is using.

## Attribution tail (sample)
- **XLI** dir=bullish uw_score_delta=0.0
- **XLF** dir=bullish uw_score_delta=0.0
- **META** dir=bullish uw_score_delta=0.08951999999999999
- **AAPL** dir=bullish uw_score_delta=0.0
- **AAPL** dir=bullish uw_score_delta=0.0
- **AAPL** dir=bullish uw_score_delta=0.0
- **AAPL** dir=bullish uw_score_delta=0.0
- **AAPL** dir=bullish uw_score_delta=0.0
- **AAPL** dir=bullish uw_score_delta=0.0
- **AAPL** dir=bullish uw_score_delta=0.0

