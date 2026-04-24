# Alpaca data contract assertion (static proof)

**Mission:** ALPACA PRE-MARKET DATA READINESS PROOF — SYNTHETIC + AUDIT  
**TS:** `20260330_200000Z`  
**Scope:** Static review of contracts and emitters (no live orders; no engine edits).

---

## 1. Where contracts live

| Artifact | Path | Role |
|----------|------|------|
| Validators (best-effort) | `src/contracts/telemetry_schemas.py` | `validate_exit_attribution`, `validate_master_trade_log`, etc. |
| Strict join enforcement | `telemetry/alpaca_strict_completeness_gate.py` | **Operational** completeness for closed trades (read-only eval). |
| Signal context writer | `telemetry/signal_context_logger.py` | Appends `logs/signal_context.jsonl`; **never raises**; can no-op via `ALPACA_SIGNAL_CONTEXT_EMIT`. |
| Join key builder | `src/telemetry/alpaca_trade_key.py` | `trade_key` / side / epoch. |

---

## 2. Mapping mission vocabulary → repo reality

| Mission term | Repo / ops reality |
|--------------|-------------------|
| **entry_decision_made** | **Not** a universal top-level field name. Canonical live proxy: **`run.jsonl`** `event_type=trade_intent` with **`decision_outcome=entered`** (see `scripts/audit/alpaca_event_flow_audit.py` — “entry_decision_made is proxied…”). |
| **signal context (direction + score)** | **`logs/signal_context.jsonl`**: `signals` dict + `final_score` when logger runs; **optional** attribution keys via `attribution_emit_keys` (best-effort). |
| **lifecycle timestamps** | **`exit_attribution.jsonl`**: `entry_timestamp`, `timestamp` (exit); `trade_id` format `open_<SYM>_<ISO>`. |
| **exit_decision_made** | Proxied by **`exit_intent`** on `run.jsonl` + exit attribution row + unified `alpaca_exit_attribution` with `terminal_close`. |
| **exit_attribution** | **`logs/exit_attribution.jsonl`**; schema requires `symbol`, `timestamp`, `entry_timestamp`, `exit_reason` per `telemetry_schemas.py`. |
| **realized_pnl_usd** | Strict gate economic closure uses **`pnl`** on exit row (and related); post-close tooling also uses **`snapshot.pnl`**. Not always named `realized_pnl_usd` in JSONL. |
| **strict completeness join keys** | **`canonical_trade_id` / `trade_key`**, unified entry/exit, orders with `canonical_trade_id`, `trade_intent(entered)`, `exit_intent`, alias resolution via `canonical_trade_id_resolved` when intent≠fill. |

---

## 3. Assertions requested vs verified

| Assertion | Verdict |
|-----------|---------|
| Schemas **structurally enforce** all decision-grade fields at runtime | **NOT PROVEN.** Validators exist but are **not** shown to wrap every write path in this review; engine uses **multiple** emitters with defensive `try`/`pass` patterns. |
| **No legacy fallback** for Alpaca entry | **NOT CERTIFIED globally.** Codebase is large; strict gate is the **authoritative** join check for **closed-trade completeness**, not a proof of zero legacy branches. |
| **No optional/null** fields for decision-grade telemetry | **FALSE as stated.** `validate_exit_attribution` explicitly allows **`direction_intel_embed`** optional; `signal_context` fields like `confidence_bucket` may be null; `_is_num` allows None in places. |

---

## 4. What **is** enforced (board-useful)

1. **`evaluate_completeness`** gives a **PASS/FAIL (ARMED/BLOCKED)** outcome on a cohort with explicit **reason_histogram** — this is the **same** logic used for live strict audits (no relaxation in this mission).  
2. **`telemetry_schemas.py`** documents **minimum** required keys for several log types — useful for **linting** and **audits**, not a total proof of absence of nulls.  
3. **Synthetic lab** (Phase 2) demonstrates a **full chain** that satisfies the strict gate (separate artifact).

---

## 5. Static phase conclusion

**RESULT: PARTIAL / QUALIFIED**

- The mission’s strongest **static** claim (“no optional/null,” “no legacy fallback”) **cannot** be certified from schema files alone.  
- **Strict completeness** is the **actionable** enforcement mechanism for **decision-grade joins** on **closed** Alpaca trades.  
- **No blockers** to proceeding to **synthetic execution** proof (Phase 2–3).

---

*Artifact: static analysis only.*
