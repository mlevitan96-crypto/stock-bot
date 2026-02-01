# Ingestion & Data Presence Audit

**Generated:** 2026-01-28T17:19:42.708040+00:00 (UTC)
**Window:** N/A (file existence and non-empty payloads).

---

- **UW flow cache** (`data/uw_flow_cache.json`): exists=True, size=6784989, status=OK — non-empty dict with flow/cluster data
- **UW flow cache log** (`data/uw_flow_cache.log.jsonl`): exists=True, size=2907431, status=OK — lines with _ts
- **Composite cache** (`data/composite_cache.json`): exists=False, size=0, status=MISSING — composite clusters
- **Run log** (`logs/run.jsonl`): exists=True, size=11422338, status=OK — event_type trade_intent/exit_intent/complete
- **System events** (`logs/system_events.jsonl`): exists=True, size=7245008, status=OK — event_type, timestamp
- **Regime state** (`state/regime_detector_state.json`): exists=True, size=107, status=OK — regime_label or equivalent
- **Market context v2** (`state/market_context_v2.json`): exists=True, size=584, status=OK — optional
- **Signal weights** (`state/signal_weights.json`): exists=True, size=1149659, status=OK — optional

## Evidence (timestamps)
- **Run log (last 3 _dt):** ['2026-01-28T17:19:35.93', '2026-01-28T17:19:38.29', '2026-01-28T17:19:41.04']
- **System events (last 3 timestamp):** ['2026-01-28T17:19:41.40', '2026-01-28T17:19:41.40', '2026-01-28T17:19:41.44']