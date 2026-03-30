# ALPACA_TELEGRAM_NEW_DESIGN_20260330_190500Z

## Principles

- Alpaca-only; env secrets only; no strategy changes.
- One orchestrator: `run_alpaca_telegram_integrity_cycle.py`.
- Milestone: **250** unique closes, **canonical `trade_key`** (`symbol|side|entry_epoch`), **exit_ts ≥ effective US regular session open** (weekday-aware; Fri open if weekend).
- Idempotency: `state/alpaca_milestone_250_state.json` per `session_anchor_et`.

## Message: 250-trade milestone

Header: `ALPACA 250-TRADE MILESTONE` (or `[TEST]`).  
Body: session open UTC, ET anchor date, trade count, sum of `pnl` in exit rows, DATA_READY from latest coverage file (if parsed), `LEARNING_STATUS` from strict gate, latest SPI path glob, `reports/` hint, sample trade_keys.

## Message: data integrity alert

Header: `ALPACA DATA INTEGRITY ALERT` (or `[TEST]`).  
Triggers: coverage % below config; coverage file missing/stale; exit tail missing critical fields; ARMED→BLOCKED; post-close / direction pager eval not PASS/SENT/SKIPPED/PENDING; throttled by cooldowns in `state/alpaca_telegram_integrity_cycle.json`.  
Body: bullet reasons, optional `last_good` snapshot, short operator action line.

## Config surface

`config/alpaca_telegram_integrity.json` — see MEMORY_BANK.md.

## Send helper

Reuses `scripts/alpaca_telegram.send_governance_telegram` (`script_name` discriminates journal/log lines).
