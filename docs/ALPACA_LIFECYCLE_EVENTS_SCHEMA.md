# Alpaca Lifecycle Events Schema (Gate Traces & Shadow Events)

**Authority:** `docs/ALPACA_GOVERNANCE_CONTEXT.md` Section A1 (Truth Contracts).  
**Companion:** `docs/ATTRIBUTION_TRUTH_CONTRACT.md` (attribution/exit records); this doc covers gate traces and shadow stream only.

This document is the single authoritative spec for **required fields** and **WARN vs FAIL** semantics for Alpaca gate-trace and shadow lifecycle events. Producers MUST emit required fields; validators SHOULD report missing fields per the semantics below.

---

## 1. Gate trace events (blocked trades)

**Source:** `state/blocked_trades.jsonl`. Each line is one JSON object produced by `log_blocked_trade()` in `main.py`.

### Required fields (all MUST be present)

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string (ISO 8601) | Time of the block decision. |
| `symbol` | string | Ticker symbol. |
| `reason` | string | Canonical block reason (e.g. `score_below_min`, `expectancy_blocked:score_floor_breach`, `max_positions_reached`). |
| `score` or `candidate_score` | number (or null) | Score at block time; may be null if unavailable. |

### Optional but recommended

- `block_reason` (same as `reason` if present).
- `side`, `direction`, `decision_price`, `would_have_entered_price`, `expected_value_usd`, `candidate_rank`.
- `signals`, `components`, `market_context` for attribution and forensics.

### WARN vs FAIL

- **FAIL:** Missing any of `timestamp`, `symbol`, `reason`. (Without these, blocked-winner forensics and gate attribution cannot run.)
- **WARN:** Missing `score`/`candidate_score`; or missing optional fields. Log a warning; do not fail the pipeline.

---

## 2. Gate stream (logs/gate.jsonl)

**Source:** `log_event("gate", msg, **kw)` in `main.py`; writes to `logs/gate.jsonl` with `{"msg": msg, **kw}`.

Used for real-time gate observability and cycle summaries. Not the primary store for blocked-trade attribution (that is `state/blocked_trades.jsonl`).

### Required fields per record

| Field | Type | Description |
|-------|------|-------------|
| `msg` | string | Gate event kind (e.g. `cycle_summary`, `score_below_min`, `max_positions_reached`). |

### Recommended when blocking a symbol

- `symbol`, `score`, `reason` or `gate_type` for traceability.

### WARN vs FAIL

- **FAIL:** Not used for gate.jsonl (best-effort observability). Validator does not FAIL on gate.jsonl.
- **WARN:** Missing `msg` or empty `msg` for a line that is not `cycle_summary`.

---

## 3. Shadow events (logs/shadow.jsonl)

**Source:** Multiple producers: `telemetry/shadow_experiments.py` (shadow_variant_decision, shadow_variant_summary), `shadow/shadow_pnl_engine.py` (shadow_exit, shadow_pnl_update, shadow_ledger_update, etc.), and any writer that emits `event_type` into this stream.

Consumers (e.g. `reports/_daily_review_tools/generate_shadow_audit.py`) expect `event_type` and type-specific fields.

### Required fields (all shadow records)

| Field | Type | Description |
|-------|------|-------------|
| `event_type` | string | One of: `shadow_candidate`, `shadow_executed`, `shadow_exit`, `shadow_pnl_update`, `shadow_variant_decision`, `shadow_variant_summary`, `shadow_ledger_update`, `score_compare`, `divergence`, or other documented type. |
| Timestamp | string | Either `ts` or `timestamp_utc` (ISO 8601). At least one MUST be present. |

### Required by event_type

| event_type | Additional required fields |
|------------|----------------------------|
| `shadow_candidate` | `symbol`; score-related field (`score`, `v2_score`, or `candidate_score`). |
| `shadow_executed` | `symbol`, `side`, `qty` or quantity, `entry_price` or `entry_ts` (for join). |
| `shadow_exit` | `symbol`; `realized_pnl_usd` or exit outcome field. |
| `shadow_pnl_update` | `symbol`; `unrealized_pnl_usd` or PnL field. |
| `shadow_variant_decision` | `symbol`, `variant_name`, `would_enter` (or equivalent), score-related field. |
| `shadow_variant_summary` | `variant_name`, `candidates_considered` or equivalent. |

### WARN vs FAIL

- **FAIL:** Missing `event_type`; or missing timestamp (`ts` or `timestamp_utc`) on any record. (Breaks audit and daily reports.)
- **WARN:** Missing type-specific required fields (e.g. `shadow_executed` without `symbol`); or unknown `event_type`. Log warning; do not fail production pipeline.

---

## 4. Validation

- **Script:** `scripts/validate_lifecycle_events_schema.py` (see below). Runs over recent `state/blocked_trades.jsonl` and `logs/shadow.jsonl`; emits WARN/FAIL to stdout and optional report file.
- **Contract tests:** Attribution invariants remain in `schema/contract_validation.py` and `docs/ATTRIBUTION_TRUTH_CONTRACT.md`. This doc does not change attribution FAIL criteria (e.g. missing exit_reason_code remains FAIL in contract tests).
- **Governance wiring:** Validator can be invoked from EOD or daily diagnostics; default behavior is WARN-only so production is not broken by schema drift. Use `--fail-on-required` for CI or strict checks after human approval.

---

## 5. References

- **Blocked trade writer:** `main.log_blocked_trade` → `state/blocked_trades.jsonl`.
- **Gate stream:** `main.log_event("gate", ...)` → `logs/gate.jsonl`.
- **Shadow stream:** `telemetry/shadow_experiments.py`, `shadow/shadow_pnl_engine.py` → `logs/shadow.jsonl`.
- **Audit:** `reports/_daily_review_tools/generate_shadow_audit.py` (consumes shadow events).
