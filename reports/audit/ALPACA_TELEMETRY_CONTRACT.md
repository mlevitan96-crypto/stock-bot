# Alpaca Required Telemetry Contract (Phase 0)

**MEMORY_BANK.md SHA256:** `605E72546DA23BE424898C0B8BDB43AC6571064795D281E8D9C929A598F2E271`  
**Loaded:** 2026-03-18 (governing contract)

## 1. Canonical streams

| Stream | Path | Purpose |
|--------|------|---------|
| **Exit (primary PnL / lifecycle)** | `logs/exit_attribution.jsonl` | One row per closed trade; v2 exit intel, PnL, `trade_id`, `entry_timestamp` |
| **Entry (UW / legacy)** | `logs/attribution.jsonl` | Entry events; `trade_id` `open_*`; context for effectiveness |
| **Entry (Alpaca lever truth)** | `logs/alpaca_entry_attribution.jsonl` | Composite, contributions, `trade_key`, `trade_id` |
| **Unified** | `logs/alpaca_unified_events.jsonl` | `event_type` = `alpaca_entry_attribution` \| `alpaca_exit_attribution` |
| **Exit (emitter mirror)** | `logs/alpaca_exit_attribution.jsonl` | Canonical exit rows from `emit_exit_attribution` (schema 1.2.0) |
| **Master trade** | `logs/master_trade_log.jsonl` | Optional join / replay |

## 2. Join keys (MB + `telemetry/snapshot_join_keys.py`)

| Key | Rule |
|-----|------|
| **trade_id** | Primary. Entry: `open_{SYMBOL}_{entry_ts_iso}` aligned with `position_metadata.json` `entry_ts`. Exit: same `open_*` on `exit_attribution` when joined. |
| **trade_key** | `symbol\|SIDE\|entry_time_iso` (UTC second) via `build_trade_key()`. |

## 3. REQUIRED fields — entry causality

| Field | Required |
|-------|----------|
| `trade_id` | YES |
| `trade_key` | YES |
| `symbol`, `side`, `timestamp` | YES |
| `composite_score` | YES (nullable only if raw empty) |
| `contributions` (or derivable from raw×weights) | YES |
| `schema_version` | YES |
| `decision` (OPEN_LONG / OPEN_SHORT) | YES |

## 4. REQUIRED fields — exit causality

| Field | Required |
|-------|----------|
| `trade_id` | YES |
| `entry_timestamp` | YES |
| `symbol`, `timestamp`, `pnl` / `realized_pnl_usd` | YES |
| `exit_reason` | YES |
| `v2_exit_components` (or equivalent) | YES for v2 exits |
| `attribution_schema_version` | YES (`exit_attribution.jsonl`) |

## 5. REQUIRED for analysis gate (forward window)

- **100%** of closed trades in proof window have matching **entry** row in `alpaca_entry_attribution.jsonl` **or** unified stream with same `trade_id`.
- **100%** have exit row in `exit_attribution.jsonl`.
- Streams **append-only** for protected paths (MB § retention).

## 6. Checklist (fail-closed)

- [ ] `alpaca_entry_attribution.jsonl` exists and growing after repair deploy  
- [ ] `alpaca_unified_events.jsonl` exists and growing  
- [ ] `exit_attribution.jsonl` present  
- [ ] Entry `trade_id` == exit `trade_id` (open_* family) for same trade  
- [ ] `trade_key` parseable on both sides  
- [ ] Forward proof script **PASS** (≥50 trades, 100% join)  

Until all checked: **analysis forbidden** on forward causal claims.
