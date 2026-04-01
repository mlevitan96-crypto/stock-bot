# Phase 4 — 250 milestone eligibility (no send)

## Config (authoritative)

`/root/stock-bot/config/alpaca_telegram_integrity.json`:

- `milestone_counting_basis`: **`integrity_armed`**
- `milestone_trade_count`: **250**

## State file

`/root/stock-bot/state/alpaca_milestone_250_state.json` (captured):

```json
{
  "fired_milestone": false,
  "last_count": 0,
  "session_anchor_et": "2026-04-01"
}
```

## Rebuilt snapshot (read-only Python, production logic)

Same calls as `runner_core` uses for `snap` + `should_fire_milestone` (no `send_msg`, no `update_integrity_arm_state` mutation in this snippet — **read** arm file only):

```json
{
  "now_utc_iso": "2026-04-01T19:12:36.546386+00:00",
  "computed_session_anchor_et": "2026-04-01",
  "config_milestone_counting_basis": "integrity_armed",
  "config_milestone_trade_count": 250,
  "integrity_arm_state_raw": {
    "arm_epoch_utc": null,
    "armed_at_utc_iso": null,
    "session_anchor_et": "2026-04-01"
  },
  "arm_epoch_utc_used_for_snapshot": null,
  "snapshot": {
    "session_anchor_et": "2026-04-01",
    "unique_closed_trades": 0,
    "counting_basis": "integrity_armed",
    "count_floor_utc_iso": "(not armed — waiting for green DATA_READY + coverage + strict ARMED + exit probe)",
    "integrity_armed": false,
    "realized_pnl_sum_usd": 0.0
  },
  "should_fire_milestone_250": false,
  "fired_milestone_in_state": false
}
```

## Answers (evidence-backed)

| Question | Answer |
|----------|--------|
| **milestone_counting_basis** | `integrity_armed` (from config) |
| **session_anchor_et** | `2026-04-01` |
| **unique_closed_trades** (for milestone) | **0** (because `arm_epoch_utc` is null) |
| **Eligible for 250 right now?** | **NO** — count is 0 vs target 250 |
| **Primary reason** | **`arm_epoch_utc` missing** → not integrity-armed for counting (not “already fired”) |
| **Already fired for this anchor?** | **NO** — `fired_milestone` is **false** |

## Note

Strict gate **`LEARNING_STATUS: ARMED`** (separate subsystem) coexists with **milestone integrity arm file** still showing `arm_epoch_utc: null`. Milestone 250 uses **`integrity_armed`** counting basis per config, not the strict gate object directly.
