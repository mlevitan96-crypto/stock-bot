# STOP-GATE 2 — CSA final verdict: Alpaca trade data collection

**Artifact:** `ALPACA_DATA_COLLECTION_CLOSEOUT_20260326_2015Z`  
**Date:** 2026-03-26

---

## Verdict (choose one)

### **NO-GO**

Alpaca trade data collection is **not** certified **complete, correct, fresh, and joinable** for continuing live trading under the **PERFECT** contract.

**Trading must be treated as UNSAFE** from a **data-collection certification** perspective until blockers are cleared and this certification is **re-run on the Alpaca droplet** with full artifacts.

---

## Exact blockers

| # | Blocker | Evidence |
|---|---------|----------|
| 1 | **Droplet Phase 1 not executed** | `ALPACA_DATA_PIPELINE_HEALTH_20260326_2015Z.md` — no journal / `systemctl` captures |
| 2 | **Execution logging absent (workspace)** | `logs/orders.jsonl` **0 bytes** — `ALPACA_DATA_FRESHNESS_AUDIT_20260326_2015Z.md` |
| 3 | **Unified terminal close not aligned to exits** | Ratio **0.028** — `ALPACA_EVENT_FLOW_COUNTS_20260326_2015Z.md` / JSON |
| 4 | **exit_attribution join key missing** | No `trade_id` in local `exit_attribution.jsonl` — `ALPACA_JOIN_INTEGRITY_AUDIT_20260326_2015Z.md` |
| 5 | **Cross-log staleness** | `run.jsonl` / `exit_attribution.jsonl` mtimes **lag** `alpaca_*` — freshness audit |
| 6 | **Traces show no orders join** | `orders_rows_matching_canonical_keys: 0` in traces — JSON |
| 7 | **Certification scope** | Local/dev log mix (fixtures); **not** production-only cohort |

---

## Artifacts delivered (this run)

| Phase | File |
|-------|------|
| STOP-GATE 0 | `reports/audit/ALPACA_DATA_COLLECTION_STOP_GATE_0_CSA_20260326_2015Z.md` |
| 1 | `reports/audit/ALPACA_DATA_PIPELINE_HEALTH_20260326_2015Z.md` |
| 2 | `reports/audit/ALPACA_EVENT_FLOW_COUNTS_20260326_2015Z.md` + `reports/ALPACA_EVENT_FLOW_COUNTS_20260326_2015Z.json` |
| 3 | `reports/audit/ALPACA_JOIN_INTEGRITY_AUDIT_20260326_2015Z.md` |
| 4 | `reports/audit/ALPACA_DATA_FRESHNESS_AUDIT_20260326_2015Z.md` |
| 5 | `reports/audit/ALPACA_DATA_FAILURE_MODES_20260326_2015Z.md` |
| STOP-GATE 1 | `reports/audit/ALPACA_DATA_ADVERSARIAL_REVIEW_20260326_2015Z.md` |
| STOP-GATE 2 | This file |

---

## Tooling change

- `scripts/audit/alpaca_event_flow_audit.py`: added `--json-out` and **fallback** trace sampling from unified `trade_id` when `exit_attribution` lacks `trade_id`.

---

## Next actions (to pursue DATA_COLLECTION_CERTIFIED)

1. Run Phase 1 journal capture on **Alpaca droplet**; name all trading + telemetry + integrity units.  
2. Ensure **`logs/orders.jsonl`** receives submits/fills under live paper trading (non-zero, growing).  
3. Ensure **`exit_attribution.jsonl`** includes **`trade_id`** (or publish approved join reconstruction).  
4. Raise unified **`terminal_close`** coverage to contract expectation **or** CSA **written exception** with end date.  
5. Re-run `alpaca_event_flow_audit.py` on droplet with production window (e.g. 72h / 7d) and attach new `<TS>` artifacts.
