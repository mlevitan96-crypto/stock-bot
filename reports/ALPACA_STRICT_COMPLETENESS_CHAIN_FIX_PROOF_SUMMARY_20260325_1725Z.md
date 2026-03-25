# ALPACA strict completeness — chain fix proof summary (20260325_1725Z)

## PLAN_VERDICT

**APPROVE** (executed). Plan: diagnose 30/30 incomplete with authoritative join semantics, fix gate + telemetry plumbing (no strategy change), test, deploy, prove on live windows, write artifacts.

**Failure-mode review:** Per-symbol “latest fill” as join key (multi-trade collision on same ticker); intent vs fill epoch skew; orders inheriting wrong runtime `canonical_trade_id` during direction/flip blocks; unified entry indexed on one key only; exit_intent missing canonical when metadata sparse; vacuous ARMED (already fixed earlier).

---

## 1) STRICT_EPOCH_START used and why

| Field | Value |
|--------|--------|
| **STRICT_EPOCH_START (UTC)** | `2026-03-25T17:01:20Z` |
| **Epoch seconds** | `1774458080` |
| **Why** | Service restart after prior telemetry hardening; used as the **post-deploy proof window** for *new* terminal closes only. |
| **Note** | `scripts/alpaca_post_deploy_terminal_close_audit.py` `DEPLOY_START` aligned to `1774458080`. |

Gate on `--open-ts-epoch 1774458080` at audit time: **`trades_seen == 0`** → **`LEARNING_STATUS: BLOCKED`**, **`learning_fail_closed_reason: NO_POST_DEPLOY_PROOF_YET`** (no terminal close in that window yet).

---

## 2) Top incomplete reasons BEFORE and AFTER

**BEFORE (prior strict gate on cohort `1774456240`–`1774458080`, pre–alias/collision fix):**  
30/30 incomplete with mixed histogram (including misleading partial joins from per-symbol latest-fill key collision).

**AFTER (gate `c9dae8b` + live audit on same historical cohort, `--open-ts-epoch 1774456240`):**

| Reason | Count (30 trades) |
|--------|-------------------|
| `entry_decision_not_joinable_by_canonical_trade_id` | 30 |
| `missing_unified_entry_attribution` | 30 |
| `no_orders_rows_with_canonical_trade_id` | 30 |
| `missing_exit_intent_for_canonical_trade_id` | 30 |

**Interpretation:** Historical JSONL for that batch still lacks joinable surfaces (or `canonical_trade_id_resolved` edges never linked those intent IDs to those fill keys). **Forward-only** fixes (`log_order` metadata canonical, `_emit_exit_intent` key backfill) do not rewrite past rows.

---

## 3) Three sample trades — chain matrix BEFORE vs AFTER

**Sample trade_ids:** `open_XLP_2026-03-25T16:13:49.500754+00:00`, `open_XLV_2026-03-25T16:13:51.428831+00:00`, `open_DIA_2026-03-25T16:14:00.096212+00:00`.

| Matrix cell | BEFORE (wrong per-symbol join experiment) | AFTER (per-trade `trade_key` + aliases) |
|-------------|---------------------------------------------|----------------------------------------|
| `trade_intent_entered_present` | Inconsistent / misleading | **false** (no matching entered intent in alias set for these trades) |
| `unified_entry_attribution_present` | false | **false** (no unified entry row keyed to that `trade_key`) |
| `orders_rows_canonical_trade_id_present` | false / misleading | **false** (no `orders.jsonl` row with `canonical_trade_id` in alias set; sample rows showed runtime LONG key vs position SHORT key) |
| `exit_intent_keyed_present` | false | **false** |
| `unified_exit_terminal_close` | true | **true** |
| `exit_attribution_jsonl_row` | true | **true** |

---

## 4) AUTHORITATIVE_JOIN_KEY and enforcement

- **Rule (documented):** Per closed trade, **authoritative join string = `trade_key` from unified `alpaca_exit_attribution`**, else derived from `open_{SYM}_{entry_ts}` plus **exit row side** (SHORT/LONG). **Alias expansion:** undirected `canonical_trade_id_intent` ↔ `canonical_trade_id_fill` from `canonical_trade_id_resolved` in `run.jsonl`. **Not used:** a single per-symbol “latest fill” (avoids multi-position collision).
- **Code:** `telemetry/alpaca_strict_completeness_gate.py` — `AUTHORITATIVE_JOIN_KEY_RULE`, `_expand_canonical_aliases`, unified entry dual-index (`trade_key` + `canonical_trade_id`), `normalize_side` for TID fallback.
- **Orders:** `main.py` `log_order` — if event has no `canonical_trade_id`, **stamp from `StateFiles.POSITION_METADATA` for that symbol** before `merge_attribution_keys_into_record` (additive).
- **Exit intent:** `main.py` `_emit_exit_intent` — backfill `canonical_trade_id` (and related keys) from `get_symbol_attribution_keys(symbol)` when metadata omitted them.

---

## 5) LEARNING_STATUS and remaining condition

| Window | Verdict |
|--------|---------|
| `--open-ts-epoch 1774458080` | **BLOCKED** — **`NO_POST_DEPLOY_PROOF_YET`** (`trades_seen == 0`) |
| `--open-ts-epoch 1774456240` (historical cohort) | **BLOCKED** — **`incomplete_trade_chain`** (all four join reasons still present on frozen logs) |

**ARMED** requires a post-`1774458080` terminal close cohort with `trades_complete == trades_seen` and `trades_incomplete == 0` under the strict gate (not observed in this run).

---

## 6) Diagnostics (`learning_blocker`)

- **Count:** `grep learning_blocker /root/stock-bot/logs/run.jsonl` → **0** at audit time (substring match; dedicated emitter remains on validation/emit failure paths from prior work).
- **Examples:** none in sample tail.

---

## Deploy

- Repo: `076bb03` on `main` (includes gate + `log_order` + `_emit_exit_intent` + audit script + tests).
- Droplet: `git pull`; **`stock-bot.service` restarted** when deploying `main.py` changes.

---

## Tests (mandatory)

- `tests/test_alpaca_entry_ts_normalization.py`: resolution alias chain → **ARMED**; shared canonical on entry+exit orders → **ARMED**; existing incomplete / vacuous tests still pass.
