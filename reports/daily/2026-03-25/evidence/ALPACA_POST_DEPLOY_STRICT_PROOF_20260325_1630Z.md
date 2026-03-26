# ALPACA POST-DEPLOY STRICT COMPLETENESS PROOF

**Artifact TS:** `20260325_1630Z` (aligned to service `ExecMainStartTimestamp` date)  
**Execution:** Read-only self-audit on droplet `/root/stock-bot`  
**Date generated (UTC):** 2026-03-25 (audit run)

---

## PHASE 0 — CONTEXT & WINDOW

| Field | Value |
|--------|--------|
| **Deploy commit (HEAD)** | `dbfb41f8ee61fddd1fb5f59af973efb5e9116582` |
| **Commit timestamp (git)** | `2026-03-25 09:31:18 -0700` → **2026-03-25T16:31:18Z** (author/committer time; not identical to restart) |
| **Service** | `stock-bot.service` **active** |
| **ExecMainStartTimestamp / ActiveEnterTimestamp** | **Wed 2026-03-25 16:30:40 UTC** |
| **WorkingDirectory** | `/root/stock-bot` |

### STRICT_EPOCH_START (explicit rule)

**Rule:** For post-deploy cohort evaluation, `OPEN_TS_UTC_EPOCH = int(ExecMainStartTimestamp UTC)` = **1774456240** ≡ **2026-03-25T16:30:40+00:00**.

Only `exit_attribution.jsonl` rows whose `timestamp` parses to **≥** this instant are in the **post-deploy strict window** (when cross-checking closes vs deploy).

### Legacy (pre-epoch / ISO) trade_keys — exclusion

**Rule:** A `trade_key` / `canonical_trade_id` is **epoch-era** iff the third segment matches `^[0-9]+$` (Unix second). If the third segment contains `T`, `+`, or non-numeric ISO artifacts, it is **legacy ISO-era** and is **excluded** from join matching against the post-deploy epoch scheme.

Unified stream today: existing `alpaca_entry_attribution` lines (n≈1042) use **historical** `trade_key` shapes; they do **not** populate the post-deploy proof cohort until new epoch-keyed events exist.

---

## PHASE 1 — TERMINAL CLOSE DETECTION

| Check | Result |
|--------|--------|
| `grep -c alpaca_exit_attribution logs/alpaca_unified_events.jsonl` | **0** |

**STATUS: WAITING_FOR_FIRST_POST_DEPLOY_TERMINAL_CLOSE**

**NEXT_TRIGGER:** Re-run this audit after the **first terminal position close** following deploy (new code path appends `alpaca_exit_attribution` with `terminal_close=true`).

**STOP (Phase 1):** No post-deploy unified exit rows exist yet; Phases 2–3 **full chain row-level proof** cannot be executed on live data.

---

## PHASE 2 — CANONICAL ID AUTHORITY (CODE-BASED; NO LIVE ROW)

**AUTHORITATIVE_JOIN_KEY (runtime truth):** **`canonical_trade_id` after `mark_open`**, i.e. **fill-time** `build_trade_key(symbol, side, now)` stored via `set_symbol_attribution_keys(symbol, canonical_trade_id=_ct2)`.

**When intent ≠ fill:** `canonical_trade_id_resolved` in `run.jsonl` records `canonical_trade_id_intent` vs **`canonical_trade_id_fill`**; the **fill** value matches what is stored in attribution keys and what must match orders/unified for strict joins.

**Strict gate precedence (offline auditor):** `telemetry/alpaca_strict_completeness_gate.py` maps `canonical_trade_id_fill` per symbol from `canonical_trade_id_resolved` into `resolved_final`, then treats `effective_ct = resolved_final.get(sym)` so **`trade_intent` can match** when the intent row carried the pre-fill id but the **authoritative** key is the fill id.

**Code locations**

1. Fill authority + resolved emission: `main.py` (Executor `mark_open`) — `set_symbol_attribution_keys(symbol, canonical_trade_id=_ct2)` and optional `jsonl_write(..., event_type: canonical_trade_id_resolved, canonical_trade_id_fill: ...)`.
2. Gate matching: `telemetry/alpaca_strict_completeness_gate.py` — `resolved_final` / `effective_ct` / `entry_decision_ok`.

**BLOCKER: CANONICAL_ID_PRECEDENCE_INCONSISTENT:** **NONE** (single authority: fill-time key; resolver row + gate bridge intent drift only).

---

## PHASE 3 — FULL CHAIN PROOF

**Not applicable** until Phase 1 non-zero. Required rows for the **first** post-deploy terminal trade will be:

- `trade_intent` entered + `canonical_trade_id`
- `orders.jsonl` entry rows (merged keys)
- `exit_intent` + `canonical_trade_id`
- `orders.jsonl` exit rows
- Unified `alpaca_exit_attribution`: `terminal_close=true`, `realized_pnl_usd`, `fees_usd=0`
- `exit_attribution.jsonl`

**Partial fills:** Not evaluated (no terminal close in window). **Requirement:** partials must **not** mint new `trade_key` for the same flat position (code path: same per-symbol keys until close).

---

## PHASE 4 — STRICT COMPLETENESS GATE

**Window A — US/Eastern market open today (built-in gate):** (run separately if needed; historical cohort remains BLOCKED for epoch migration reasons.)

**Window B — post-deploy only (`open_ts_epoch=1774456240`):**

| Metric | Value |
|--------|--------|
| trades_seen | **0** |
| trades_complete | **0** |
| trades_incomplete | **0** |
| reason_histogram | `{}` |
| LEARNING_STATUS (mechanical gate) | **ARMED** (vacuous: zero trades ⇒ no failing trade) |

**CSA interpretation:** Mechanical ARMED on an **empty** window is **not** sufficient to ARM learning globally; see Phase 5.

---

## PHASE 5 — SELF-AUDITING QUESTIONS (ANSWERED)

1. **Which canonical ID is authoritative for joins?**  
   **Fill-time `canonical_trade_id`** set in `mark_open` (`_ct2`), propagated via `merge_attribution_keys_into_record` on orders and metadata-backed `exit_intent`.

2. **Where is precedence enforced?**  
   **`main.py`** `mark_open`: overwrites keys with `_ct2`; optional **`canonical_trade_id_resolved`** documents intent→fill; **`telemetry/alpaca_strict_completeness_gate.py`** uses `canonical_trade_id_fill` per symbol to accept `trade_intent` when intent id differed.

3. **Strict completeness forward-only?**  
   **YES.** Legacy ISO `trade_key` rows cannot match epoch-era keys; pre-deploy history does not satisfy strict (A) without backfill/migration.

4. **Remaining join ambiguities?**  
   **NONE** resolved in code for authority; **operational gap:** no post-deploy terminal sample yet to empirically verify one full chain.

5. **Temporal rules for evaluated trades?**  
   **N/A** (no trades in post-deploy window). Invariant when data exists: exit timestamp ≥ entry timestamp (gate checks).

6. **Learning safe to ARM right now?**  
   **NO.** Reason: **zero** `alpaca_exit_attribution` unified rows; **no** post-deploy terminal close proof; fail-closed for end-to-end strict completeness.

7. **Condition BLOCKED → ARMED?**  
   At minimum: **≥1** terminal close in unified stream with `terminal_close=true` + full chain present for that `trade_id`/`canonical_trade_id`, and strict gate on an appropriate window reports **trades_complete ≥ 1** with no blocking reasons (or explicit policy for cohort scope).

---

## CSA FINAL VERDICT

**BLOCKED** for **global / proven strict completeness** (no post-deploy unified terminal exit; empty post-deploy window).  
**Phase 1 outcome is valid:** **WAITING_FOR_FIRST_POST_DEPLOY_TERMINAL_CLOSE**.

---

## Next automatic trigger

Re-run this audit **after first terminal close** (or on a schedule); success criterion: `grep -c alpaca_exit_attribution logs/alpaca_unified_events.jsonl` **≥ 1** with `terminal_close` true on newest rows.
