# PHASE 4 — Telemetry Reliability Hardening (SRE)

**Timestamp:** 2026-03-26

---

## Changes

### 1. UW cache atomic write (`cache_enrichment_service.py`)

- **Before:** `uw_flow_cache.json.tmp` + `Path.replace` without fsync; race-prone under concurrent readers/writers.
- **After:** `uw_flow_cache.json.<pid>.tmp`, `flush` + `os.fsync`, `os.replace` to resolved absolute destination; `mkdir(parents=True)`.

### 2. Dashboard order timestamp (`dashboard.py` — `api/health_status`)

- **Before:** `float(submitted_at)` failed on pandas `Timestamp`.
- **After:** Use `.timestamp()` when available; preserves string ISO path.

### 3. Alpaca API retries / position drift

- **Not changed in code** (would touch reconciliation policy). Continue to monitor:
  - `[CACHE-ENRICH] WARNING: sleep 3 seconds and retrying https://paper-api.alpaca.markets`
  - `Positions in Alpaca but not in local state`  
  Documented as **SRE follow-up** if drift persists; not a JSONL writer bug.

### 4. Strict gate robustness (`telemetry/alpaca_strict_completeness_gate.py`)

- Index **`exit_intent`** by **`canonical_trade_id` or `trade_key`**.
- Treat **`trade_intent` entered** as joinable if **`canonical_trade_id` OR `trade_key`** ∈ alias set.

---

## Verification

- `tests/test_strict_completeness_forward_parity.py` — synthetic chain **ARMED**.
- Existing `tests/test_alpaca_attribution_parity.py`, `tests/test_alpaca_exit_attribution_contract.py` — **pass**.
