# ALPACA STRICT COMPLETENESS REPAIR — PROOF

**Artifact TS:** 20260325_1800 (UTC naming)  
**Repo commits:** `39a89ac` (telemetry repair), `dbfb41f` (CLI `sys.path` fix)  
**Droplet:** `/root/stock-bot`, `stock-bot.service` **active** after `git pull` + `systemctl restart stock-bot.service`

---

## PLAN_VERDICT: APPROVE (revisions incorporated)

**Restatement:** Unify Alpaca learning surfaces under one UTC-second-epoch `trade_key` / `canonical_trade_id`, always set `canonical_trade_id` on `trade_intent(entered)`, emit `canonical_trade_id_resolved` when intent vs fill second differs, enrich unified entry/exit with economics (`fees_usd=0`, `realized_pnl_usd`, `terminal_close`), wire exit attribution to unified with those fields, keep paper trading and strategy logic unchanged.

**Revisions applied:**
1. Intent-time id vs fill-time id: `mark_open` overwrites keys with fill-time canonical; `run.jsonl` gets `canonical_trade_id_resolved` when intent ≠ fill.
2. `trade_key` third segment migrates from ISO to **Unix epoch int (UTC, second floor)** — **not** backward-compatible with pre-deploy unified rows or orders; strict gate is **forward-correct** for new cohorts.
3. `mark_open` uses **timezone-aware** `datetime.now(timezone.utc)` for position open instant (metadata + canonical).

**Multi-model review (two passes):** (A) SRE: droplet `main.py` local drift caused stash pop conflict — resolved with `git reset --hard` to origin so runtime matches repo. (B) CSA: historical trades remain BLOCKED until a full post-deploy close produces epoch-aligned unified + orders + intents.

---

## PHASE 0 — SRE (droplet)

| Check | Result |
|--------|--------|
| Service | `stock-bot.service` **active**, `WorkingDirectory=/root/stock-bot` |
| `grep -c alpaca_entry_attribution logs/alpaca_unified_events.jsonl` (pre new closes) | **1042** |
| `grep -c alpaca_exit_attribution logs/alpaca_unified_events.jsonl` (pre new closes) | **0** |

*Note: exit count stays 0 until the first **terminal** close after deploy; new emitter writes `alpaca_exit_attribution` with `terminal_close=true`.*

---

## PHASE 1 — Timestamp normalization (single rule)

**Function:** `normalize_entry_ts_to_utc_second(x) -> int` in `src/telemetry/alpaca_trade_key.py`

| Input type | Rule |
|------------|------|
| `datetime` | Naive → UTC; aware → convert to UTC; **microseconds stripped**; `int(timestamp)` |
| `int` / `float` | `int(float(x))` |
| ISO `str` | `fromisoformat`, Z → offset, same UTC floor |

**`build_trade_key(symbol, side, entry_time)`** → `{SYMBOL}|{LONG\|SHORT}|{epoch}`

**Surfaces (conceptual):**

| Surface | Source of `entry_time` | TZ / precision |
|---------|------------------------|----------------|
| `trade_intent` (entered) | `datetime.now(timezone.utc)` at emit | UTC aware, second-aligned epoch in id |
| `mark_open` / metadata | `datetime.now(timezone.utc)` at fill callback | Same |
| `open_*` trade_id | Metadata `entry_ts` ISO (microsecond in string; epoch id uses **floor second**) | UTC |
| `orders.jsonl` | `merge_attribution_keys` → `canonical_trade_id` from keys | Epoch id string |
| `exit_intent` | Metadata keys | Epoch id |
| `exit_attribution` | `entry_timestamp` string | Parsed to UTC second |
| Unified entry/exit | Emitter `trade_key` / `canonical_trade_id` | Epoch id |

---

## PHASE 2–4 — Code touchpoints (Alpaca only)

- `main.py`: `_emit_trade_intent` sets `canonical_trade_id` for `entered`; `learning_blocker` on failure; `mark_open` + `canonical_trade_id_resolved` row.
- `src/telemetry/alpaca_attribution_emitter.py`: entry/exit unified rows include `canonical_trade_id`, `fees_usd=0`; exit adds `terminal_close`, `realized_pnl_usd`.
- `src/exit/exit_attribution.py`: passes canonical + terminal + PnL + fees into `emit_exit_attribution`.
- `telemetry/learning_blocker_emit.py`: append-only `learning_blocker` events.
- `telemetry/alpaca_strict_completeness_gate.py` + `scripts/alpaca_strict_completeness_gate.py`: deterministic gate (CLI fixes `sys.path` on droplet).

---

## PHASE 5 — Strict completeness (droplet, post-deploy)

Ran: `python3 scripts/alpaca_strict_completeness_gate.py --root /root/stock-bot`

**Snapshot (historical window, US/Eastern open today):**

- `trades_seen`: **112** (example run; varies with session)
- `trades_complete`: **0**
- `LEARNING_STATUS`: **BLOCKED** (expected: pre-deploy ISO keys vs new epoch keys; no unified exit lines yet)

**Forward expectation:** After the first **new** round-trip (intent → fill → orders with keys → exit_intent → unified exit with `terminal_close`), `trades_complete` should increment for that trade only. Partials do not emit terminal unified exit.

---

## PHASE 6 — Tests

`pytest` (local): `tests/test_alpaca_entry_ts_normalization.py`, `tests/test_alpaca_*_attribution_contract.py`, `tests/test_alpaca_attribution_parity.py` — **pass**.

---

## Example joined chain (template for next closed trade)

Use the same `canonical_trade_id` (epoch form) across:

1. `run.jsonl` → `event_type=trade_intent`, `decision_outcome=entered`, `canonical_trade_id=SYM|LONG|{epoch}`
2. Optional `canonical_trade_id_resolved` if fill second ≠ intent second
3. `logs/orders.jsonl` → rows with `canonical_trade_id` (via `log_order` merge)
4. `run.jsonl` → `exit_intent` with `canonical_trade_id`
5. `logs/alpaca_unified_events.jsonl` → `alpaca_exit_attribution` with `terminal_close=true`, `realized_pnl_usd`, `fees_usd=0`
6. `logs/exit_attribution.jsonl` → `pnl`, `exit_price`

---

## CSA FINAL VERDICT

**BLOCKED** for strict completeness on **historical** trades in the current window (schema migration + no post-deploy terminal unified exits yet).  
**Forward path:** **ARMED** only after at least one post-deploy terminal close validates 100% join on the **epoch** id (operational proof, not assumed).

---

## Multi-model confirmation

- **Quant:** One `trade_key` per flat position; partial scale-outs are not terminal; terminal close = one `append_exit_attribution` path.
- **SRE:** Rollback = `git revert` + restart; logs append-only; no strategy flags changed.
