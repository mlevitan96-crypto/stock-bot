# Phase 8 — Repo-wide audit pass (adversarial)

**Date:** 2026-02-18

## 1. Phase 7 endpoints exist and are wired

| Endpoint | Result | Evidence |
|----------|--------|----------|
| `/api/attribution/trade/<trade_id>` | **PASS** | dashboard.py L3810: @app.route, reads logs/attribution.jsonl + logs/exit_attribution.jsonl |
| `/api/effectiveness/signals` | **PASS** | dashboard.py L3870: _load_effectiveness_cached() → signal_effectiveness |
| `/api/effectiveness/exits` | **PASS** | dashboard.py L3880: same cache → exit_effectiveness |
| `/api/effectiveness/blame` | **PASS** | dashboard.py L3890: same cache → entry_vs_exit_blame |
| `/api/effectiveness/counterfactual` | **PASS** | dashboard.py L3901: same cache → counterfactual_exit |

**Evidence paths:** dashboard.py 3810–3908.

## 2. _get_effectiveness_dir() precedence

| Check | Result | Evidence |
|-------|--------|----------|
| First: state/latest_backtest_dir.json → backtests/<path>/effectiveness/ | **PASS** | dashboard.py L3759–3768: latest.exists() → d["path"] → root/path/effectiveness, else root/path |
| Else: newest reports/effectiveness_* | **PASS** | L3772–3774: reports.glob("effectiveness_*"), sorted by mtime, reverse |
| Fallback: reports/governance_comparison | **PASS** | L3775–3776 |

**Evidence path:** dashboard.py 3756–3779.

## 3. Backtest join key correctness

| Check | Result | Evidence |
|-------|--------|----------|
| Join today | **FAIL → FIX** | attribution_loader.load_from_backtest_dir and load_joined_closed_trades use only (symbol, entry_ts_bucket). No trade_id primary; no quality_flags=["join_fallback"]. |
| entry_timestamp written | **PASS** | run_30d_backtest_droplet.py L207–210 copies entry_timestamp/entry_ts into backtest_exits |

**Action:** Add trade_id as primary join when present; add quality_flags=["join_fallback"] when join is by (symbol, entry_timestamp) only. Implement in Step 6.

## 4. Regression guards (entry + exit invariants, fail loudly)

| Check | Result | Evidence |
|-------|--------|----------|
| Entry invariant | **PASS** | regression_guards.py L49–70: uw_composite_v2.compute_composite_score_v2, sum(ac) vs score |
| Exit invariant | **PASS** | L73–92: compute_exit_score_v2, sum(ac) vs s |
| Fails loudly (exit 1, stderr) | **PASS** | L154–157: print GUARD FAILED, return 1 |

**Evidence path:** scripts/governance/regression_guards.py.

---

## Summary

| Item | Status |
|------|--------|
| Phase 7 endpoints | PASS |
| _get_effectiveness_dir precedence | PASS |
| Backtest join (trade_id primary + join_fallback) | FAIL → fix in Phase 8 |
| Regression guards | PASS |

**Overall:** One fix required (join key + quality_flags). Proceed with implementation.
