# Alpaca live entry intent contract (learning truth)

Canonical reference for `entry_decision_made` rows on `logs/run.jsonl`. Telemetry-only; does not change execution decisions.

## Event

- `event_type`: `entry_decision_made`
- Emitted on the filled-entry path immediately after `trade_intent` (`decision_outcome=entered`) once `canonical_trade_id` and `open_<SYM>_<entry_ts>` are known.

## LIVE, non-synthetic (required for learning audits post epoch)

- `entry_intent_synthetic`: `false` for runtime emissions
- `entry_intent_source`: `live_runtime`
- `entry_intent_status`: `OK` when economics are present; `MISSING_INTENT_BLOCKER` when the bot stayed live but intent could not be completed (audits **fail**; no fabricated scores).

### Required when `entry_intent_status=OK`

- `signal_trace`: non-empty object with `policy_anchor` (string). May embed `intelligence_trace` and/or `source` describing equalizer-only fallback.
- `entry_score_total`: numeric (float/int).
- `entry_score_components`: non-empty object. May use `{"_no_breakdown": true, "entry_score_total_echo": <total>}` when only a total exists.

### Blocker payload (`MISSING_INTENT_BLOCKER`)

- `entry_intent_error`: reason string
- `entry_score_components` includes `"_blocked": true`
- Audits treat this as **FAIL** (stay-live semantics; no synthetic scores).

## Non-gating (unchanged)

- MFE/MAE, path analytics, post-hoc volatility: review-only; not used in strict completeness reasons except as documented elsewhere.

## Epoch

- Trades with position open time ≥ `LIVE_ENTRY_INTENT_REQUIRED_SINCE_EPOCH` in `telemetry/alpaca_strict_completeness_gate.py` must have a contract-satisfying LIVE `entry_decision_made` row or strict completeness reports `live_entry_decision_made_missing_or_blocked`.

## Isolation

- Alpaca-only paths; no Kraken imports or shared execution.
