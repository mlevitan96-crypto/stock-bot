# Alpaca learning gate separation

**Evidence host:** local_workspace  
**ET report date:** 2026-03-27  
**Generated (UTC):** 20260328_032555Z

## Learning gate definition source

**telemetry/alpaca_strict_completeness_gate.py — evaluate_completeness()**

## Gating inputs (enumerated)

- trade_intent entered joinable via canonical_trade_id / trade_key aliases
- alpaca_unified_events alpaca_entry_attribution present for aliases
- orders.jsonl rows keyed by canonical_trade_id
- exit_intent for canonical keys
- alpaca_exit_attribution with terminal_close
- exit_attribution.jsonl economic closure (exit_price, pnl, timestamps, trade_id schema)

## Explicitly non-gating (analytics)

- MFE/MAE appear in exit attribution snapshot (src/telemetry/alpaca_attribution_schema.py) but are not checked in strict completeness reasons[] in evaluate_completeness.
- No price-path or post-hoc volatility metric appears in reason_histogram keys produced by the strict gate.

## Review-only analytics

Path analytics / volatility may appear in dashboards, board packets, or CSA reviews; they do not appear in LEARNING_STATUS / learning_fail_closed_reason computation.
