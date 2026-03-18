# Kraken telemetry contract (independent spec)

**Scope:** Hypothetical **Kraken venue** live system. **Not** Alpaca. **Not** implied by current `MEMORY_BANK.md` Alpaca sections.

## Required event streams (minimum)

| Stream | Purpose | Append-only |
|--------|---------|-------------|
| **Entry attribution** | One record per opened position / accepted entry intent | Yes |
| **Execution / submit** | Order submit, acks, partial fills (if applicable) | Yes |
| **Exit attribution** | One record per closed position with PnL and exit reason | Yes |
| **Unified events** (optional but recommended) | Normalized `event_type` timeline for joins and replay | Yes |
| **Blocked / counterfactual** | Gates that prevented entry (if strategy emits) | Yes |

## Canonical join key

- **`trade_id`:** Stable string, assigned **before** first persistence of entry, reused on every fill/update and on exit line.  
- **Alternates:** If broker uses multiple ids, contract must document `broker_order_id` / `position_id` → `trade_id` mapping table or embedded fields on every line.

## Required fields (by lifecycle)

| Stage | Minimum fields |
|-------|----------------|
| Entry | `trade_id`, `timestamp` (UTC), `symbol` (pair), `venue`, `side`, `intent` or `fill_price`/`qty` |
| Execution | `trade_id` (or mappable id), `timestamp`, status |
| Exit | `trade_id`, `exit_timestamp`, `pnl` or `pnl_quote`, `exit_reason`, `entry_timestamp` (or linkable) |

## Schema version

- Each stream line SHOULD include `schema_version` or contract version in first line / sidecar file under `state/`.

## Truth Gate thresholds (this mission)

- **DATA_READY (join):** **100%** entry↔exit join on a defined forward window, or MB-approved documented exception (none exists for Kraken in MB today).
- **Forensics-grade floor:** **≥95%** log join only if explicitly approved; below 95% = **NOT_DATA_READY** for causal forensics.

## Repository reality (non-performance)

This repo’s **live** path is **Alpaca equities** (`venue: "alpaca"`). **Kraken public OHLC** exists under `data/raw/kraken` for **research download only** — not a substitute for live trade telemetry.
