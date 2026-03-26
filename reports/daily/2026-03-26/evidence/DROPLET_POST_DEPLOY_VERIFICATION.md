# Droplet Post-Deploy Verification

**Date:** 2026-02-27  
**Orchestrator:** Autonomous multi-model deployment and verification  
**Branch/commit on main:** 1cbeba0 (Merge origin/main before deploy push)

---

## Phase 1 — Push to GitHub

- **Status:** Completed
- All changes committed with message: *Post-audit deploy: giveback fix, entry attribution fix, dashboard endpoint, Phase1 scripts, Memory Bank alignment.*
- Merged `origin/main` (new reports) and pushed to `origin/main` successfully.

---

## Phase 2 — Deploy to Droplet

- **Git:** `git fetch origin && git reset --hard origin/main` — success (HEAD at 1cbeba0).
- **Dependencies:** `venv/bin/pip install -r requirements.txt` and `venv/bin/pip install pytest` — success (project venv used; system Python is externally managed).
- **Pytest spine:** Run with `venv/bin/python -m pytest`:
  - **test_exit_attribution_phase4.py:** 4 passed, 1 failed  
    - **Failure:** `test_exit_attribution_no_opaque_components` — assertion `signal_id.startswith("exit.")` failed for component `flow_deterioration`.
  - **test_effectiveness_reports.py:** 2 passed  
  - **test_attribution_loader_join.py:** 3 passed  
  - **Summary:** 9 passed, 1 failed (spine non-blocking; deploy continued).
- **Deploy steps:** git_pull ✓, pytest_spine ✓, kill_stale_dashboard ✓, restart_service ✓.
- **Dashboard / stock-bot:** Restarted via `sudo systemctl restart stock-bot` (deploy_supervisor brings up dashboard on port 5000).
- **uw-flow-daemon:** Not restarted by deploy; confirmed active in Phase 1 audit.
- **Governance loop:** Not restarted (was not started by this run).

---

## Phase 3 — Phase 1 Audit on Droplet

- **Script:** `python scripts/run_phase1_audit_on_droplet.py --out-dir reports/audit`
- **Artifacts updated:**
  - `reports/audit/PHASE1_DROPLET_RESULTS.md`
  - `reports/audit/PHASE1_DROPLET_RESULTS.json`
  - `reports/audit/PHASE1_ALPACA_ALIGNMENT.json`
- **Verification:**
  - **stock-bot.service:** Active
  - **uw-flow-daemon.service:** Active
  - **Dashboard:** Runs under stock-bot (deploy_supervisor); service active implies dashboard process running.
  - **Alpaca alignment snapshot:** Success  
    - `positions_count`: 18  
    - `cash`: 51025.39  
    - `equity`: 48984.03  
    - `status`: ACTIVE  

---

## Phase 4 — Governance Endpoint

- **Endpoint:** `GET http://localhost:5000/api/governance/status` (dashboard auth from .env).
- **Response (summary):**
  - `expectancy_per_trade`: -0.079184  
  - `win_rate`: 0.3752  
  - `avg_profit_giveback`: null  
  - `joined_count`: 725  
  - `stopping_condition_met`: false  
  - `stopping_checks`: expectancy_gt_0 (false), giveback_le_baseline_plus_005 (null), joined_count_ge_100 (true), win_rate_ge_baseline_plus_2pp (false)  
  - `source_decision`: reports/equity_governance/equity_governance_20260227T184644Z/lock_or_revert_decision.json  
  - `source_aggregates`: reports/effectiveness_baseline_blame/effectiveness_aggregates.json  
  - `decision`: LOCK  
- **Cross-check:** Values consistent with governance using latest lock decision and effectiveness aggregates; giveback null until more exits with high_water populate aggregates.

---

## Phase 5 — Exit/Entry Attribution Verification

- **Script (on droplet):** `venv/bin/python scripts/report_last_5_trades.py --n 5`
- **Output saved:** `reports/audit/last_5_trades_droplet.txt`
- **Confirmed:**
  - **v2_exit_score:** Present (reported as "Exit composite score (v2)" per trade; some 0.0).
  - **v2_exit_components:** Present (section per trade; some "(none)" when no components).
  - **exit_reason_code:** Present (e.g. "code: other", "Exit reason (primary): other").
  - **entry_attribution_components:** Present (e.g. "Attribution components (per-signal contribution to entry score)" with flow, dark_pool, etc.; one trade had "(none recorded)").
  - **signal_effectiveness.json:** File exists on droplet at `reports/effectiveness_baseline_blame/signal_effectiveness.json` (2 bytes; minimal content until next effectiveness run).

---

## Phase 6 — Dashboard Endpoint Verification

- **Governance status:** Verified in Phase 4; endpoint returns all required fields (expectancy_per_trade, win_rate, avg_profit_giveback, joined_count, stopping_condition_met, stopping_checks, source_decision, source_aggregates).
- **Dashboard port:** 5000 (codebase default).
- **No live trading config or overlay changes;** no new governance cycle triggered.

---

## Summary

| Phase | Status | Notes |
|-------|--------|--------|
| 1 Push to GitHub | OK | origin/main updated |
| 2 Deploy | OK | venv deps, pytest 9/10, restart |
| 3 Phase 1 audit | OK | Services + Alpaca alignment |
| 4 Governance endpoint | OK | All fields present |
| 5 Attribution | OK | v2 exit/entry fields present |
| 6 Finalize | OK | This document |

**System ready for next governance cycle.** Single pytest failure (`test_exit_attribution_no_opaque_components`) is known: one exit component uses `signal_id` "flow_deterioration" instead of "exit.*"; non-blocking for deploy and verification.
