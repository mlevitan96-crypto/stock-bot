# Live Pipeline Audit — Attribution and Exit Attribution

**Goal:** Confirm live writes `logs/attribution.jsonl` and `logs/exit_attribution.jsonl` with schema needed for effectiveness and score-vs-profitability.

## Where records are written

- **Entry attribution:** `main.py` — `jsonl_write("attribution", attribution_record)` (e.g. ~2139, ~1775, ~6940). Log dir from `LOG_DIR` → `logs/attribution.jsonl`.
- **Exit attribution:** `src/exit/exit_attribution.py` — `append_exit_attribution(rec)`. Writes to `OUT` = `logs/exit_attribution.jsonl` (or `EXIT_ATTRIBUTION_LOG_PATH`). Called from `main.py` `log_exit_attribution` (~2193–2282).

## Schema to verify on droplet

- **attribution.jsonl:** Should have `entry_score`, `context` (with `attribution_components` if available), and fields needed for join (e.g. symbol, ts, trade_id).
- **exit_attribution.jsonl:** Should have `exit_reason`, `entry_timestamp`, symbol, and `exit_quality_metrics` (e.g. profit_giveback, mfe, mae) when available.

## Gaps to fix before Monday (if any)

1. Ensure attribution record at entry includes **entry_score** so effectiveness and score-vs-profitability can use it.
2. Ensure exit record includes **exit_quality_metrics** where compute_exit_quality_metrics is used so effectiveness can compute giveback/blame.

## Quick check on droplet

```bash
tail -n 1 logs/attribution.jsonl | python3 -c "import sys,json; d=json.load(sys.stdin); print('entry_score' in d or 'entry_score' in d.get('context',{}))"
tail -n 1 logs/exit_attribution.jsonl | python3 -c "import sys,json; d=json.load(sys.stdin); print('exit_reason' in d, 'exit_quality_metrics' in d)"
```
