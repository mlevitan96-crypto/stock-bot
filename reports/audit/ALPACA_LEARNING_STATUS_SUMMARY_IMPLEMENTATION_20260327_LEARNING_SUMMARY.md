# Alpaca learning status summary — implementation

**Timestamp:** `20260327_LEARNING_SUMMARY`

## Module

`scripts/audit/alpaca_learning_status_summary.py`

- `build_summary_dict` — pure synthesis from truth JSON + exit code + optional incident path
- `emit_learning_status_summary` — writes rolling `reports/ALPACA_LEARNING_STATUS_SUMMARY.json` and `reports/audit/ALPACA_LEARNING_STATUS_SUMMARY.md`
- `git_head_sha(root)` — `git rev-parse HEAD`
- CLI: `--root`, `--truth-json`, `--incident-json`, `--window-hours`, `--exit-code`, `--commit-sha`

## Markdown

One-line verdict banner, metrics table, “Why this verdict”, proof links, notes.
