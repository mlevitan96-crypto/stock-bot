# ALPACA unified exit attribution zero — proof summary (20260325_1702Z)

## Phase 0 (SRE)

| Field | Value |
|--------|--------|
| `current_utc` | 2026-03-25T17:01:08Z (audit); `stock-bot.service` restarted 2026-03-25T17:01:20Z |
| Host uptime | ~30 days |
| `stock-bot.service` | active |
| `trading-bot.service` | inactive (supervisor-managed child per deploy layout) |
| `terminal_closes_since_deploy_count` (exit_attribution.jsonl, floor `DEPLOY_START` 1774456240) | **30** |
| Same count (orders `close_position`) | **30** |
| Example symbols + timestamps (≤5) | MS `2026-03-25T16:54:24Z`, XLE `2026-03-25T16:54:21Z`, LOW `2026-03-25T16:54:19Z`, WFC `2026-03-25T16:54:16Z`, JPM `2026-03-25T16:54:13Z` |

## Emitter path (CSA + SRE)

- **Code path:** `append_exit_attribution` (`src/exit/exit_attribution.py`) → `emit_exit_attribution` (`src/telemetry/alpaca_attribution_emitter.py`) → append `alpaca_exit_attribution` to `logs/alpaca_unified_events.jsonl` (canonical `LOG_DIR = REPO / "logs"`).
- **`grep -c alpaca_exit_attribution logs/alpaca_unified_events.jsonl`:** **31** (> 0).
- **Emitter invoked on live path:** **Yes** — production rows present (e.g. XLE terminal close with full schema); not only dry-run.
- **Resolved unified path:** `/root/stock-bot/logs/alpaca_unified_events.jsonl`.

## Root cause (historical “zero”)

- **Not** a permanent “emitter never runs” failure: unified file contains many `alpaca_exit_attribution` lines aligned with post–16:30:40Z closes.
- Prior “zero” readings are consistent with **audit timing** (before post-deploy closes landed) or **wrong window**, not a missing code path.
- **Residual risk (fixed):** inner `except Exception: pass` around the emit block could hide import/runtime failures; replaced with `learning_blocker` event `unified_exit_emit_exception` (non-trading).

## Diagnostics (additive, removable)

- Validation / IO failures: `learning_blocker` reasons `alpaca_exit_validation_blocked`, `alpaca_jsonl_append_failed`.
- Optional success/fail emit trace: set `ALPACA_UNIFIED_EXIT_EMIT_DIAG=1` → `alpaca_unified_exit_emit_attempt` lines in `logs/run.jsonl`.

## Vacuous “ARMED” fix (CSA)

- **Before:** `trades_seen == 0` could yield `LEARNING_STATUS: ARMED` (no incomplete rows).
- **After:** `trades_seen == 0` ⇒ `LEARNING_STATUS: BLOCKED`, `learning_fail_closed_reason: NO_POST_DEPLOY_PROOF_YET`.
- **Confirmed in repo:** `telemetry/alpaca_strict_completeness_gate.py` + pytest `test_gate_blocks_vacuous_zero_trades`.

## Phase 5 strict gate (post-deploy window `--open-ts-epoch 1774456240`)

| Metric | Value |
|--------|--------|
| `trades_seen` | 30 |
| `trades_complete` | 0 |
| `trades_incomplete` | 30 |
| `LEARNING_STATUS` | **BLOCKED** |
| `learning_fail_closed_reason` | **incomplete_trade_chain** |

Learning remains **fail-closed**: chain incomplete (entry/unified entry/orders/exit_intent joins), not “ARMED without proof.”

## CSA final verdict

**BLOCKED** — remaining condition: **`incomplete_trade_chain`** (e.g. `entry_decision_not_joinable_by_canonical_trade_id`, `missing_unified_entry_attribution`, `no_orders_rows_with_canonical_trade_id`, `missing_exit_intent_for_canonical_trade_id` on post-deploy exits). Unified exit lines exist; **full strict chain** is not yet satisfied.

## Deploy note

After `stock-bot.service` restart at **2026-03-25T17:01:20Z** (epoch **1774458080**), update `DEPLOY_START` in `scripts/alpaca_post_deploy_terminal_close_audit.py` when you want counts strictly “since this code refresh.”
