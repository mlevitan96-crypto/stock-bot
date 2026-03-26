# STOP-GATE 0 — Data completeness contract (CSA)

**Artifact:** `ALPACA_DATA_COLLECTION_STOP_GATE_0_CSA_20260326_2015Z`  
**Scope:** Alpaca only.

## CSA directive

**APPROVED AS WRITTEN. PROCEED.**

## PERFECT DATA COLLECTION (contract)

All must be true for every live trade in the certified window:

| ID | Requirement |
|----|----------------|
| A | Every live trade produces: entry decision → execution submit → execution fill(s) → terminal close (logged per authoritative mapping). |
| B | Terminal close reflected in execution sidecar stream **and** unified events. |
| C | Join keys consistent decision → execution → terminal (`trade_id`, `canonical_trade_id`, `trade_key` family). |
| D | No stale writers; timestamps advance monotonically where comparable. |
| E | No silent drops, retries without success, or swallowed exceptions (must be detectable in logs or metrics). |

## Repo mapping (authoritative)

See `reports/audit/ALPACA_DATA_COMPLETENESS_CONTRACT_CSA_20260326.md` for field-level mapping (`run.jsonl`, `orders.jsonl`, `exit_attribution.jsonl`, `alpaca_unified_events.jsonl`).

**Note:** “Execution sidecar” is interpreted as **`logs/orders.jsonl`** (in-process order/fill logging) unless a separate unit is added and named in deploy docs.
