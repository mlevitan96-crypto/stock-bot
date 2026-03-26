# ALPACA POST-DEPLOY STRICT PROOF — SUMMARY (copy-paste)

## Context
- **Droplet:** `/root/stock-bot`, `stock-bot.service` **active**
- **HEAD:** `dbfb41f8ee61fddd1fb5f59af973efb5e9116582`
- **Service start (UTC):** `2026-03-25T16:30:40+00:00` → **STRICT_EPOCH_START epoch:** `1774456240`
- **Unified `alpaca_exit_attribution` count:** **0** → **STATUS: WAITING_FOR_FIRST_POST_DEPLOY_TERMINAL_CLOSE**

## Decisions
- **Legacy ISO `trade_key`s:** excluded from epoch-era strict joins (third segment not all digits).
- **Authoritative join key:** **fill-time `canonical_trade_id`** from `mark_open` (`main.py`); `canonical_trade_id_resolved.canonical_trade_id_fill` is the reconciled fill id; gate uses it in `telemetry/alpaca_strict_completeness_gate.py` to match `trade_intent` when intent≠fill.
- **BLOCKER CANONICAL_ID_PRECEDENCE_INCONSISTENT:** **NONE**

## Proof excerpts
- `grep -c alpaca_exit_attribution logs/alpaca_unified_events.jsonl` = **0**
- Post-deploy window gate (`open_ts_epoch=1774456240`): `trades_seen=0`, empty histogram
- Trading: **unchanged** (read-only audit)

## CSA FINAL VERDICT
**BLOCKED** for learning ARM (no end-to-end post-deploy proof yet).  
Phase 1 **STOP** is **valid:** **WAITING_FOR_FIRST_POST_DEPLOY_TERMINAL_CLOSE**.

## Self-audit Q&A (short)
| # | Answer |
|---|--------|
| Authoritative ID | Fill-time `canonical_trade_id` after `mark_open` |
| Precedence in code | `main.py` mark_open + `alpaca_strict_completeness_gate.py` `resolved_final` |
| Forward-only? | **YES** (epoch vs ISO migration) |
| Ambiguities | **NONE** in code; **empirical proof pending** |
| Temporal rules | **N/A** (no trades in window) |
| ARM safe now? | **NO** (0 unified exits) |
| Flip to ARM | First terminal close + full chain + gate clean on defined cohort |

## Next automatic trigger
**Re-run after first post-deploy terminal close** — watch: `alpaca_exit_attribution` count **> 0** in `alpaca_unified_events.jsonl`.
