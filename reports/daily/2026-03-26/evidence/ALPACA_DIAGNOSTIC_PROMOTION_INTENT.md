# Alpaca Diagnostic Promotion — Intent & Scope (CSA)

**UTC:** 2026-03-20  
**Capital risk:** **None** — Alpaca **paper** only (no live cash).

---

## Promotion type

| Field | Value |
|-------|--------|
| **Type** | **DIAGNOSTIC** — not performance-final; not a profit guarantee |
| **Venue** | **Live paper trading** (production paper endpoint / paper engine) |
| **Goal** | Reduce **loss magnitude** and/or **trade frequency** while **improving attribution clarity** (which exit driver fires when composite decays) |

---

## What success looks like (qualitative)

- Observable shift in **`exit_reason_code`** / exit intel mix (e.g. fewer uninformative `hold`-dominated outcomes where deterioration is present).
- Cleaner **`v2_exit_components`** / `attribution_components` alignment with realized outcomes over the evaluation window.
- **No** requirement to “beat the market” in this phase.

---

## What is out of scope

- Live **real-money** trading.
- Final promotion of a profit rule (separate gate).
- Broad refactors unrelated to the single diagnostic lever.

---

## Governance

- Reconciliation fixes (`master_trade_log` ↔ `exit_attribution` ID harmonization) may proceed **in parallel**; this promotion does not depend on perfect cross-log joins.
- Data integrity monitoring continues via `scripts/audit/alpaca_data_readiness_droplet_scan.py`.

---

*CSA — diagnostic intent recorded.*
