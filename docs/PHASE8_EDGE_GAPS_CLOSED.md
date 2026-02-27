# Phase 8 / Phase 9 — Edge gaps closed (and remaining)

**Date:** 2026-02-18

## Closed

### Trade linkage / join correctness

- **Join key:** `attribution_loader.load_joined_closed_trades` uses **trade_id** as primary join when present (entry trade_id `open_*`, exit trade_id or decision_id). Fallback: (symbol, entry_ts_bucket) with **quality_flags=["join_fallback"]**.
- **Backtest:** `load_from_backtest_dir` always uses (symbol, entry_ts); every row gets **quality_flags=["join_fallback"]** (backtest outputs have no trade_id today).
- **Contract:** Only entries with trade_id starting with `"open_"` are indexed in `entry_by_trade_id`; other formats fall back to key join (documented in attribution_loader docstring).
- **Validation:** `validation/scenarios/test_attribution_loader_join.py` — trade_id primary (no join_fallback), symbol+ts fallback (join_fallback), backtest dir (join_fallback).

## Remaining (optional / do later)

### H1) Execution quality (entry + exit)

- **Not implemented.** Placeholder for: expected_price vs fill_price, spread at decision, slippage (bps), liquidity flags (wide_spread, low_volume). Add to attribution snapshots and/or exit_quality_metrics when needed.

### H2) Post-exit excursion

- **Partially wired:** `run_effectiveness_reports.py` reads `exit_quality_metrics.post_exit_excursion` and reports `avg_post_exit_excursion` when present. **No writer** yet: compute from bars (max favorable/adverse move within X minutes after exit) and store in exit_quality_metrics.

### H3) Trade linkage hardening

- **Missing trade_id:** When entry or exit records lack trade_id, set **quality_flags=["missing_trade_id"]** and **missing_reason** (never invent IDs). Not yet applied everywhere; add when auditing writers.

## How to validate

- **Join logic:** `python -m unittest validation.scenarios.test_attribution_loader_join -v`
- **Guards:** `python scripts/governance/regression_guards.py`
- **Dashboard:** Trade ID lookup uses live logs only (last 5000/3000 lines); documented in reports/phase7_proof/README.md and DASHBOARD_PANEL_INVENTORY.md.
