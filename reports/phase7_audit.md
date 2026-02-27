# Phase 7 — Adversarial repo audit (treat everything as guilty)

**Date:** 2026-02-18  
**Scope:** Phase 3 entry attribution, Phase 4 exit attribution, Phase 5 reports, Phase 6 overlay usage, invariants.

---

## 1. Phase 3 entry attribution (ENTRY_DECISION + ENTRY_FILL)

| Check | Result | Evidence |
|-------|--------|----------|
| Entry attribution written for live | **PASS** | `main.py::log_attribution()` (L1706) writes via `jsonl_write("attribution", { "type": "attribution", "trade_id", "symbol", "pnl_usd", "context" })`. Context is stored as-is. |
| Context includes attribution_components at entry | **PASS** | Before `log_attribution` at L9517, `context["attribution_components"] = _composite_meta.get("attribution_components")` is set (L9454–9457). |
| ENTRY_DECISION / ENTRY_FILL snapshots | **PASS** | `log_attribution` calls `write_snapshot_safe(..., event="ENTRY_FILL" \| "ENTRY_DECISION", ...)` (L1715–1723). `main.py` L9154–9162 writes ENTRY_DECISION before placing order. |
| Backtest/lab parity | **PASS** | `historical_replay_engine.py` L475–477 preserves `attribution_components` when present in context. |

**Evidence paths:** `main.py` 1706–1731, 9454–9517, 9154–9162; `historical_replay_engine.py` 475–477.

---

## 2. Phase 4 exit attribution (EXIT_DECISION + EXIT_FILL)

| Check | Result | Evidence |
|-------|--------|----------|
| Exit attribution written | **PASS** | `main.py` L2145–2226: `build_exit_attribution_record()` + `append_exit_attribution(rec)` to `logs/exit_attribution.jsonl`. |
| EXIT_DECISION snapshot | **PASS** | L7011–7035: EXIT_DECISION snapshot with v2_exit_attribution_components in composite_meta. |
| EXIT_FILL snapshot | **PASS** | L1909–1932: EXIT_FILL written in `log_exit_attribution` via `write_snapshot_safe(..., "EXIT_FILL", ...)`. |
| decision_id / trade_id / timestamps | **PASS** | `src/exit/exit_attribution.py` builds record with `entry_timestamp`, `timestamp` (exit), `decision_id`; join key is symbol+entry_timestamp. |

**Evidence paths:** `main.py` 1825–2226, 7011–7035, 1909–1932; `src/exit/exit_attribution.py`.

---

## 3. Phase 5 reports (logs + backtest dirs)

| Check | Result | Evidence |
|-------|--------|----------|
| From logs | **PASS** | `scripts/analysis/run_effectiveness_reports.py` L301–309: `load_joined_closed_trades(attr_path, exit_path)` with `logs/attribution.jsonl` and `logs/exit_attribution.jsonl`. |
| From backtest dir | **PASS** | Same script L299–300: `load_from_backtest_dir(args.backtest_dir)` when `--backtest-dir` is set. |
| Join key | **PASS** | `attribution_loader.py`: entry key = `symbol|entry_ts_bucket(ts)` from trades; exit key = `symbol|entry_ts_bucket(entry_timestamp)` from exits. Backtest exits must have `entry_timestamp` (now copied in `run_30d_backtest_droplet.py` L207–210). |

**Evidence paths:** `scripts/analysis/run_effectiveness_reports.py` 284–320; `scripts/analysis/attribution_loader.py` 140–178; `scripts/run_30d_backtest_droplet.py` 207–210.

**Caveat:** Backtest dirs produced before `entry_timestamp` was copied into backtest_exits may yield zero joined rows; re-run backtest or use logs for those windows.

---

## 4. Phase 6 overlay loader used in production exit path

| Check | Result | Evidence |
|-------|--------|----------|
| Exit scoring uses merged weights | **PASS** | `src/exit/exit_score_v2.py` L37–42: `_get_exit_weights()` calls `get_merged_exit_weights(EXIT_WEIGHTS)` from `config.tuning.tuning_loader`. |
| Score and attribution use weights | **PASS** | L85: `build_exit_attribution_components(..., weights=...)` uses `weights if weights is not None else _get_exit_weights()`. L186: score formula uses `w = _get_exit_weights()`. |

**Evidence paths:** `src/exit/exit_score_v2.py` 37–42, 85, 186.

---

## 5. Invariants

| Invariant | Result | Evidence |
|-----------|--------|----------|
| Entry: composite_score == sum(entry attribution_components) | **PASS** | `validation/scenarios/test_uw_micro_signals.py::test_composite_phase3_sum_equals_score_after_v2()`; `scripts/governance/regression_guards.py::guard_attribution_invariants()` (entry path). |
| Exit: exit_score == sum(exit attribution_components) | **PASS** | `validation/scenarios/test_exit_attribution_phase4.py` (L61–62); `regression_guards.py::guard_attribution_invariants()` (exit path). |

**Evidence paths:** `validation/scenarios/test_uw_micro_signals.py` 212–233; `validation/scenarios/test_exit_attribution_phase4.py` 55–62; `scripts/governance/regression_guards.py`.

---

## Summary

| Phase | Status | Notes |
|-------|--------|--------|
| Phase 3 entry attribution | **PASS** | Written for ENTRY_DECISION + ENTRY_FILL; context includes attribution_components; backtest parity. |
| Phase 4 exit attribution | **PASS** | Written for EXIT_DECISION + EXIT_FILL; join keys present. |
| Phase 5 reports | **PASS** | Run from logs and from backtest dirs; join requires entry_timestamp in backtest_exits (now ensured). |
| Phase 6 overlay | **PASS** | Exit scoring uses tuning_loader merged weights in production path. |
| Invariants | **PASS** | Entry and exit sum == score verified in tests and regression_guards. |

**Overall: PASS** — No missing corners that block Phase 7. Proceed with dashboard, automation, backfill, and first governed cycle.
