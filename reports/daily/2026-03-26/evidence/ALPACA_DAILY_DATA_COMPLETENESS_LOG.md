# Alpaca Daily Data Completeness Log (SRE)

**Purpose:** During each **US trading day**, confirm decision-grade rows land in **`logs/exit_attribution.jsonl`** (and supporting logs) with no silent drops.

**Scanner:** `scripts/audit/alpaca_data_readiness_droplet_scan.py`  
**Run on droplet:** `cd /root/stock-bot && PYTHONPATH=. python3 scripts/audit/alpaca_data_readiness_droplet_scan.py`

---

## Required fields per closed trade (target)

| Field | Source |
|-------|--------|
| `symbol`, direction (`side` / `direction`) | exit row |
| `entry_ts` / `entry_timestamp`, `exit_ts` / `timestamp` | exit row |
| `realized_pnl` / `pnl` | exit row |
| `exit_reason` / `exit_reason_code` | exit row |
| Signal attribution snapshot | `v2_exit_components`, `attribution_components`, `direction_intel_embed` (per TELEMETRY_STANDARD) |

---

## Log (append newest at top)

| Date (UTC) | Run TS (UTC) | exit_lines | unique_keys | missing_critical | Notes |
|------------|----------------|------------|-------------|------------------|--------|
| 2026-03-20 | 2026-03-20T00:22:47+00:00 | 2209 | 2204 | 2 rows (multi-field) | Baseline after diagnostic deploy; **quarantine 2 bad rows** from strict counts |
| | | | | | |

---

## Daily procedure

1. **After US close** (or intraday for smoke): SSH to droplet, run scanner above.  
2. Record line counts + missing-field counts in the table.  
3. If `missing_*` increases vs prior day → **page SRE** (writer regression, disk, or process crash).  
4. **Append-only:** never truncate `exit_attribution.jsonl` (see `docs/DATA_RETENTION_POLICY.md`).

---

## Automation (optional)

- Add cron: weekday **after** 21:35 UTC (aligned with MEMORY_BANK EOD sync) to run scanner and append one line to this file or to `reports/audit/alpaca_data_completeness.jsonl`.

---

*SRE — completeness is a process guarantee; integrity gaps are tracked in `ALPACA_DATA_INTEGRITY_RESULTS.md`.*
