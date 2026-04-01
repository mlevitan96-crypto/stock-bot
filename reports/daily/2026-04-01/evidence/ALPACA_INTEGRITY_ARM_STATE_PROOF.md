# Phase 3 — Integrity arm state proof (droplet)

## File inspected

`/root/stock-bot/state/alpaca_milestone_integrity_arm.json`

## Raw file contents (captured)

```json
{
  "arm_epoch_utc": null,
  "armed_at_utc_iso": null,
  "session_anchor_et": "2026-04-01"
}
```

## Current ET session anchor (computed)

From `session_anchor_date_et_iso(now)` at capture: **`2026-04-01`** (matches file `session_anchor_et`).

## Verdict: `arm_epoch_utc` for current anchor

**NO** — `arm_epoch_utc` is **`null`**. The integrity milestone counter (`integrity_armed` basis) therefore treats the session as **not armed** for counting until `update_integrity_arm_state` records an epoch when **checkpoint 100 precheck** (`cp_ok`) first becomes true for this anchor (see `telemetry/alpaca_telegram_integrity/milestone.py`).

## Strict runlog / startup banner

- `grep -c startup_banner /root/stock-bot/logs/system_events.jsonl` → **0**
- No `telemetry_chain` lines found in sampled greps of `system_events.jsonl` at capture.

**Evidence gap:** This snapshot does **not** contain a `startup_banner` line proving `strict_runlog_effective` on disk. (Journal sampling for `stock-bot.service` also showed no matching lines in the short window queried.)
