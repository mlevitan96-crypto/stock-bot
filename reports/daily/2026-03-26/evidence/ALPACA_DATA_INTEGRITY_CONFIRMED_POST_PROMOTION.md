# Alpaca Data Integrity — Confirmed Post-Promotion (SRE)

**Droplet:** `/root/stock-bot`  
**UTC:** 2026-03-20T00:35Z  
**Scanner:** `scripts/audit/alpaca_data_readiness_droplet_scan.py`

---

## Scan results

| Metric | Value | Status |
|--------|-------|--------|
| **exit_attribution.jsonl lines** | 2,209 | **OK** — continues to populate |
| **Missing symbol** | 2 | **Unchanged** — same 2 historical rows |
| **Missing PnL** | 2 | **Unchanged** — same 2 historical rows |
| **Missing entry_ts** | 2 | **Unchanged** — same 2 historical rows |
| **Missing exit_ts** | 2 | **Unchanged** — same 2 historical rows |
| **Missing direction_intel_embed dict** | 2 | **Unchanged** — same 2 historical rows |

---

## Integrity status

| Check | Result |
|-------|--------|
| **No new missing fields** | **PASS** — defect count unchanged |
| **Canonical exit_attribution.jsonl continues to populate** | **PASS** — 2,209 lines (same as pre-promotion baseline) |
| **Historical defects unchanged** | **PASS** — 2 known bad rows only |

---

## Promotion impact

- **No data regression** from diagnostic promotion activation.
- **Exit attribution writer** continues to append correctly.
- **Known defects** remain isolated (2 rows; documented in `ALPACA_DATA_INTEGRITY_RESULTS.md`).

---

*SRE — data integrity confirmed; promotion did not introduce new defects.*
