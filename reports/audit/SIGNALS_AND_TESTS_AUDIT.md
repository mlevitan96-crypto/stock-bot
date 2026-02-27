# Phase 5 — Signals, Tests, and Diagnostics Audit

**Audit date:** 2026-02-27  
**Scope:** Enumeration of entry/exit signals, signal health, test suites, diagnostic scripts, recommendations.

---

## 1. Signals enumeration

### 1.1 Exit signals (v2)

**Source:** `src/exit/exit_score_v2.py` — components dict and attribution_components list.

| signal_id | Description | Weight (contribution) |
|-----------|-------------|------------------------|
| flow_deterioration | Entry vs now flow_strength drop | 0.20 |
| darkpool_deterioration | Dark pool bias drop | 0.10 |
| sentiment_deterioration | Sentiment flip to NEUTRAL or change | 0.10 |
| score_deterioration | Entry vs now composite score drop (normalized) | 0.25 |
| regime_shift | Entry vs now regime label change | 0.10 |
| sector_shift | Entry vs now sector change | 0.05 |
| vol_expansion | Realized vol 20d above threshold | 0.10 |
| thesis_invalidated | Thesis flag | 0.10 |
| earnings_risk | Earnings risk flag | 0.0 (in weights) |
| overnight_flow_risk | Overnight flow risk flag | 0.0 (in weights) |

**Verdict:** All components have signal_id and contribution_to_score in attribution_components; no opaque components (test_exit_attribution_phase4 enforces this).

### 1.2 Entry signals

**Source:** Composite entry score from main.py / uw_composite_v2 (flow clusters, dark pool, gamma/greeks, net premium, realized vol, option volume levels). Attribution: context.attribution_components (list of {signal_id, contribution_to_score}) in logs/attribution.jsonl.

**Contract (MEMORY_BANK 4.1):** flow_conv, flow_magnitude, signal_type, direction, flow_type, etc. Normalization and validation in config/uw_signal_contracts and scoring pipeline.

**Health:** Signals are computed in scoring pipeline; distributions visible via /api/scores/distribution, telemetry. Constant or NaN-heavy signals would indicate upstream bug (e.g. missing UW cache). Not run in this audit (no live telemetry).

**Attribution:** Board docs note entry context.attribution_components sometimes missing → signal_effectiveness.json empty. Fix: ensure every open_* attribution record includes context.attribution_components.

---

## 2. Signals in effectiveness reports

- **exit_effectiveness:** By exit_reason_code (from v2: hold, intel_deterioration, stop, replacement, profit, etc.) — frequency, avg_realized_pnl, avg_profit_giveback, pct_saved_loss, pct_left_money.
- **signal_effectiveness:** Per signal_id from **entry** attribution (entry_attribution_components). Requires joined rows to have entry_attribution_components; if attribution.jsonl does not log them, signal_effectiveness is empty.
- **Exit components** appear in exit_effectiveness by reason_code, and in exit_attribution.jsonl as v2_exit_components / attribution_components.

**Verdict:** Exit signals are present in attribution and effectiveness when v2 is live. Entry signal_effectiveness depends on entry attribution logging (known gap).

---

## 3. Tests

### 3.1 Relevant test files (verified present)

| Test file | Purpose |
|-----------|---------|
| validation/scenarios/test_exit_attribution_phase4.py | exit_score_v2 5-value return, attribution sum = score, no opaque components, build_exit_attribution_record, exit_quality_metrics shape |
| validation/scenarios/test_effectiveness_reports.py | build_exit_effectiveness produces giveback when present; build_entry_vs_exit_blame has unclassified_pct |
| validation/scenarios/test_attribution_loader_join.py | Join by trade_id vs fallback; quality_flags join_fallback |

### 3.2 Other test locations

- **tests/test_truth_router.py** — Truth router.
- **validation/scenarios/** — test_tightened_profitability_levers, test_proactive_root_cause, test_scoring_pipeline_fixes, test_partial_failure, test_exit_timing_policy, test_chaos_modes, test_uw_micro_signals, test_api_drift, test_cron_diagnose_and_fix, test_attribution_schema_contract, test_state_persistence, test_replay_signal_injection, test_raw_signal_engine, test_eod_confirmation, test_trade_guard.
- **scripts/test_*.py** — test_alpaca_connection, test_wheel_watchlists, test_wheel_governance, test_wheel_analytics_contract, test_signal_propagation.
- **archive/** — Many diagnostic/investigation scripts (test_dashboard_*, test_uw_*, test_composite_scoring, etc.).

### 3.3 Test run status

**Local:** `pytest` not installed in the environment used; tests were not executed.  
**Recommendation:** On droplet or CI: `pip install pytest && pytest validation/scenarios/test_exit_attribution_phase4.py validation/scenarios/test_effectiveness_reports.py validation/scenarios/test_attribution_loader_join.py -v`. Add to pre-promotion checklist.

---

## 4. Diagnostics

| Script | Purpose |
|--------|---------|
| scripts/test_alpaca_connection.py | Alpaca API connectivity (requires env) |
| scripts/dashboard_uw_audit.py | Dashboard + UW audit; checks stock-bot.service active |
| scripts/governance/system_state_check_droplet.py | stock-bot.service, env, drop-in |
| scripts/list_droplet_processes.py | Orphan main/dashboard/uw processes |
| scripts/kill_droplet_duplicates.py | Dry-run or kill duplicates |
| scripts/run_scoring_integrity_audit_on_droplet.py | systemd units, git, scoring |
| scripts/run_full_audit_on_droplet.py | Full audit (git, restart, status) |

**Verdict:** Diagnostics exist; run on droplet for health checks. No change in this audit.

---

## 5. Recommendations

1. **Regression test for exit attribution:** Already covered by test_exit_attribution_phase4 (5-value return, reason_code in allowed set, attribution sum = score). Add optional test that main.py import and unpack of compute_exit_score_v2 returns 5 values (e.g. import main and assert callable signature or run one trade through test harness).
2. **Entry attribution:** Add or extend test that joined closed trades include entry_attribution_components when attribution.jsonl has them (attribution_loader join preserves context).
3. **Run tests before promotion:** Document in runbook: run `pytest validation/scenarios/test_exit_attribution_phase4.py validation/scenarios/test_effectiveness_reports.py validation/scenarios/test_attribution_loader_join.py` before applying any new lever to live/paper.
4. **Signal health:** Optional: add a small script or dashboard panel that samples score telemetry and flags constant or all-NaN signal_id series.

---

## 6. Summary

| Item | Status |
|------|--------|
| Exit signals (v2) enumerated | VERIFIED |
| Exit signals in attribution/effectiveness | VERIFIED (when v2 live) |
| Entry signals (composite) | Documented; attribution_components gap noted |
| test_exit_attribution_phase4 | Present; covers v2 return and attribution |
| test_effectiveness_reports | Present; covers giveback and blame |
| test_attribution_loader_join | Present; covers join logic |
| Pytest run | Not run (pytest not installed in audit env) |
| Diagnostics | Listed; run on droplet as needed |
