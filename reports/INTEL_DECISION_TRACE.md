# Decision Trace & Sentinel Audit

**Generated:** 2026-01-28T17:19:45.013220+00:00 (UTC)
**Window:** last 30 minutes.

---

## trade_intent with intelligence_trace
- Total trade_intent: 399
- With intelligence_trace: 399 (100.0%)
- Missing intelligence_trace: 0

## missing_intelligence_trace sentinel events (system_events.jsonl)
- Count in window: 0

## Partial traces (have trace but missing final_decision or gates)
- Count: 0

## Evidence (raw excerpt)
- **Sample trade_intent WITH intelligence_trace:**
  - _dt: None, event_type: trade_intent, symbol: COST
  - trace keys: ['intent_id', 'symbol', 'side_intended', 'ts', 'cycle_id', 'signal_layers', 'opposing_signals', 'aggregation', 'gates', 'final_decision']