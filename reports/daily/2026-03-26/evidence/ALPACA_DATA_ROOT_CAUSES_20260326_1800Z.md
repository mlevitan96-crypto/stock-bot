# PHASE 1 — Root Cause Isolation (SRE + Quant)

**Timestamp:** 2026-03-26  
**Inputs:** `reports/audit/ALPACA_DATA_COLLECTION_CLOSEOUT_20260326_1622Z.md`, droplet log analysis, code trace.

---

## Ranked defects (concrete)

| Rank | Defect | Evidence | Impact |
|------|--------|----------|--------|
| 1 | **`trade_intent(decision_outcome=entered)` emitted before `mark_open`, using `datetime.now()` as canonical anchor** while **`mark_open` / metadata / orders use actual fill `now`** (often different UTC second). | `main.py` `_emit_trade_intent` + `mark_open` `build_trade_key(symbol, side, now)`. | Strict gate: `entry_decision_not_joinable` (116 rows); sparse `canonical_trade_id_resolved` cannot cover all pairs. |
| 2 | **Historical `run.jsonl` lacks `trade_key` on `trade_intent`**; gate only matched `canonical_trade_id` to alias set. | Pre-repair gate code. | Legacy rows never join without exact canonical match + resolution edges. |
| 3 | **`exit_intent` indexed only when `canonical_trade_id` present**; many rows missing key. | `telemetry/alpaca_strict_completeness_gate.py` (pre-repair). | `missing_exit_intent_for_canonical_trade_id` (92). |
| 4 | **Unified terminal vs economic close gap (682 vs 252 in 72h audit)** mix of **pre-unified-emit era**, **validation-blocked emits** (now logged to `logs/alpaca_emit_failures.jsonl`), and **timestamp-window counting**. | Prior certification JSON. | Parity SLA miss until backfill + forward fix. |
| 5 | **`append_exit_attribution` preferred in-memory `get_symbol_attribution_keys` over row `canonical_trade_id`/`trade_key`**, allowing **stale or mismatched** unified canonical vs `exit_attribution` row. | `src/exit/exit_attribution.py` (pre-repair). | HOOD-class `trade_key` ≠ `canonical_trade_id` in unified tail. |
| 6 | **Per-symbol attribution keys never cleared on exit** | `clear_symbol_attribution_keys` unused outside definition. | Cross-trade contamination risk on hot symbols. |
| 7 | **UW cache writer**: single shared `.json.tmp` + `Path.replace` without fsync / PID suffix | `cache_enrichment_service.py` (pre-repair); droplet log `No such file ... .tmp`. | Intermittent cache write failures (SRE noise, stale UW). |
| 8 | **Dashboard `float(submitted_at)` on pandas `Timestamp`** | `dashboard.py` health_status. | Parse warnings; no telemetry loss but ops noise. |

---

## Not root causes (clarifications)

- **Separate execution sidecar:** orders are logged in-process; not a missing systemd unit for joins.
- **Trading/strategy logic:** out of scope; no changes applied there.
