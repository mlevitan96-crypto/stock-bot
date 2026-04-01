# Phase 2 — SRE-EDGE-001 verify (droplet)

## Commands run

```bash
cd /root/stock-bot
git pull origin main
mkdir -p reports/daily/2026-04-01/evidence
PYTHONPATH=. python3 scripts/audit/export_strict_quant_edge_review_cohort.py \
  --root /root/stock-bot \
  --out-json reports/daily/2026-04-01/evidence/ALPACA_STRICT_GATE_SNAPSHOT_DEDUP_VERIFY_20260401_191124Z.json
PYTHONPATH=. python3 scripts/audit/check_strict_cohort_dedup.py \
  --json reports/daily/2026-04-01/evidence/ALPACA_STRICT_GATE_SNAPSHOT_DEDUP_VERIFY_20260401_191124Z.json
echo EXIT:$?
```

## Export summary (stdout)

- `LEARNING_STATUS`: **ARMED**
- `trades_seen` / `strict_cohort_trade_id_count`: **399**
- `trades_complete`: **399**
- `trades_incomplete`: **0**
- `reconciliation.strict_cohort_len_equals_trades_seen`: **true**

## `check_strict_cohort_dedup.py` output

```json
{
  "json_path": "/root/stock-bot/reports/daily/2026-04-01/evidence/ALPACA_STRICT_GATE_SNAPSHOT_DEDUP_VERIFY_20260401_191124Z.json",
  "cohort_len": 399,
  "unique_len": 399,
  "duplicates": 0
}
```

**EXIT:** `0`

## Gate dedupe telemetry (`evaluate_completeness` direct)

```json
{
  "LEARNING_STATUS": "ARMED",
  "trades_seen": 399,
  "trades_complete": 399,
  "trades_incomplete": 0,
  "exit_attribution_rows_before_trade_id_dedupe": 400,
  "exit_attribution_duplicate_trade_id_rows_removed": 1
}
```

**Interpretation:** One duplicate `trade_id` row was present in the exit-attribution-derived `closed` list; after dedupe, **399** unique closes — cohort length equals unique length.

## Code fix reference

See `reports/daily/2026-04-02/evidence/ALPACA_SRE_EDGE_001_FIX.md` (same repo) or `telemetry/alpaca_strict_completeness_gate.py` (`_dedupe_closed_rows_by_trade_id`).
