# ALPACA_250_TELEGRAM_DRY_RUN

## Scope
- **No Telegram HTTP** performed.
- **Did not run** `run_alpaca_telegram_integrity_cycle.py --dry-run` when `should_fire` could be True: in current code, dry-run `send_msg` returns True and **`mark_milestone_fired` would run**, mutating state without a real send (hazard).

## Environment (after merging `.env` / `.alpaca_env` like runner)
- **TELEGRAM_BOT_TOKEN set:** True
- **TELEGRAM_CHAT_ID set:** True

## Message construction
- `format_milestone_250(...)` with current **snap** (truncated preview):

```
ALPACA 250-TRADE MILESTONE
Counting basis: integrity_armed
Count floor (UTC): (not armed — waiting for green DATA_READY + coverage + strict ARMED + exit probe)
Session open (UTC): 2026-04-01T13:30:00+00:00
Session anchor (ET date): 2026-04-01
Unique closed trades (canonical keys): 0
Realized PnL sum since count floor (USD): 0.0
DATA_READY: YES
Strict LEARNING_STATUS: ARMED
SPI snapshot: none found under reports/
Reports: reports/daily/*/evidence/
```
