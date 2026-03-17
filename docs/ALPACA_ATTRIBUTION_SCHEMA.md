# Alpaca Attribution Schema (Canonical)

**Version:** 1.2.0  
**Purpose:** Decision-grade, tunable attribution. Truth contributions (weight×value), dominant levers, threshold margins. **Canonical join:** `trade_key` for alignment with TRADES_FROZEN. All fields deterministic and versioned.

---

## A) Entry attribution (per trade open)

Emitted at decision time when we open or decide not to open. **Truth:** `raw_signals` and `weights` are the exact values used in the decision; `contributions` = weight×raw_signal; `composite_score` recomputed or asserted equal to runtime score. **Join:** `trade_key` = `symbol|side|entry_time_iso` (see ALPACA_TRADE_KEY_CONTRACT.md).

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Schema version (e.g. "1.2.0") |
| `event_type` | string | `"alpaca_entry_attribution"` |
| `trade_id` | string | Unique trade identifier |
| `trade_key` | string | Canonical join key: symbol\|side\|entry_time_iso (UTC, second) |
| `symbol` | string | Ticker |
| `timestamp` | string | ISO timestamp (UTC) |
| `side` | string | LONG \| SHORT |
| `raw_signals` | object | `{ <signal_name>: value }` — exact values used in decision |
| `weights` | object | `{ <signal_name>: weight }` — exact weights used |
| `contributions` | object | `{ <signal_name>: weight*value }` — per-signal contribution |
| `composite_score` | number \| null | Composite score (recomputed or asserted) |
| `entry_dominant_component` | string \| null | Name of component with max abs(contribution) |
| `entry_dominant_component_value` | number \| null | That contribution value |
| `entry_margin_to_threshold` | number \| null | composite_score − entry_threshold when threshold exists |
| `gates` | object | Gate pass/fail + reason (see below) |
| `decision` | string | OPEN_LONG \| OPEN_SHORT \| HOLD |
| `decision_reason` | string | Human-readable reason |

Gates: `lead_gate`, `exhaustion_gate`, `funding_veto`, `whitelist`, `regime_gate`, `score_threshold`, `cooldown`, `position_exists`. Each: `{ "pass": bool, "reason": string }`.

---

## B) Exit attribution (per evaluation + final exit)

Emitted at each exit evaluation tick (sampling allowed) and **must** be emitted at final exit. Dominant component and pressure margins added for tunability.

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Schema version |
| `event_type` | string | `"alpaca_exit_attribution"` |
| `trade_id` | string | Unique trade identifier |
| `trade_key` | string | Canonical join key: symbol\|side\|entry_time_iso (UTC, second) |
| `symbol` | string | Ticker |
| `timestamp` | string | ISO timestamp (UTC) |
| `exit_components_raw` | object | Raw pressure components |
| `exit_weights` | object | `{ component_name: weight }` |
| `exit_contributions` | object | `{ component_name: contribution }` |
| `exit_pressure_total` | number \| null | Total exit pressure [0..1] |
| `exit_dominant_component` | string \| null | Component with max abs(contribution) |
| `exit_dominant_component_value` | number \| null | That contribution |
| `exit_pressure_margin_exit_now` | number \| null | pressure − threshold_normal |
| `exit_pressure_margin_exit_soon` | number \| null | pressure − threshold_urgent |
| `thresholds_used` | object | `{ "normal": number, "urgent": number }` |
| `eligible_mechanisms` | object | Which mechanisms could fire (booleans) |
| `winner` | string | Actual exit_reason |
| `winner_explanation` | string | Why this mechanism won |
| `snapshot` | object | `pnl`, `pnl_pct`, `pnl_unrealized`, `mfe`, `mae`, `mfe_pct_so_far`, `mae_pct_so_far`, `hold_minutes` at exit |

---

## Persistence

- Entry: `logs/alpaca_entry_attribution.jsonl` (and optionally unified stream with `event_type = alpaca_entry_attribution`).
- Exit: `logs/alpaca_exit_attribution.jsonl` (and optionally unified stream with `event_type = alpaca_exit_attribution`).

Contract: additive only; MUST NOT affect execution. Emitters must not raise in hot paths.
