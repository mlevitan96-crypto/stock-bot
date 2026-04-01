# ALPACA_COVERAGE_DATA_READY_CONTRACT_FIX

## Generator

- **Script:** `scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py`
- **Coverage artifact:** `reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_<tag>.md`
- **Parser:** `telemetry/alpaca_telegram_integrity/warehouse_summary.py` — `parse_coverage_markdown`, regex `_DATA_READY_RE = re.compile(r"DATA_READY:\s*(YES|NO)", re.I)`

## Change

After all gate-driven `blockers` are computed, the mission sets `coverage_data_ready = len(blockers) == 0` and writes **exactly one** line in the coverage markdown:

`DATA_READY: YES` or `DATA_READY: NO` (same truth as fail-closed `data_ready`).

## Before / after (snippet)

**Before (no deterministic line; parser returned `data_ready_yes: None`):** older coverage files had only bullet metrics, e.g. `reports/daily/2026-03-24/evidence/ALPACA_TRUTH_WAREHOUSE_COVERAGE_20260324_2109.md` — no `DATA_READY:` line.

**After (droplet run `20260401_1728`):**

```markdown
# ALPACA_TRUTH_WAREHOUSE_COVERAGE_20260401_1728

DATA_READY: NO

- execution join coverage: **100.00%**
```

## Parser proof

`scripts/audit/parse_coverage_smoke_check.py` against latest coverage on droplet produced `parse_coverage_smoke_check.json`:

```json
{
  "coverage_path": "/root/stock-bot/reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_20260401_1728.md",
  "data_ready_yes": false,
  "parse_ok": true,
  "execution_join_pct": 100.0
}
```

`data_ready_yes` is **not** `null` — deterministic boolean.

## Warehouse fail-closed reason (this run)

`DATA_READY: NO` because `blocked_boundary_coverage` gate failed (~17.68% vs 50% threshold). See `ALPACA_TRUTH_WAREHOUSE_BLOCKERS_20260401_1728.md` and `ALPACA_TRUTH_WAREHOUSE_RUN.log`.
