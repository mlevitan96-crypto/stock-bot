# Memory Bank & Documentation Index

**Audit date:** 2026-02-27  
**Purpose:** Single index of key docs for Cursor and operators; verification status against code/droplet (code verified in this run; droplet where noted).

---

## Key documents (source of truth)

| Doc | Path | Summary | Verification |
|-----|------|---------|--------------|
| **MEMORY_BANK.md** | repo root | Master operating manual: Cursor behavior, architecture, config, signal contract, deployment, dashboard, governance. | **PARTIALLY_STALE** — Service name (stock-bot.service), deploy_supervisor, paths match code. Dashboard URL (104.236.102.57:5000) and droplet IP may change; Golden Workflow (push→GitHub→droplet→verify) is policy. Section 6.6 deploy steps (pkill dashboard, restart stock-bot) verified in droplet_client. |
| **SYSTEM_CONTRACT.md** | repo root | System contract: services (stock-bot, uw-flow-daemon), behavior, safety. | **VERIFIED_ACCURATE** — Refs to stock-bot.service, uw-flow-daemon.service, paths align with code. |
| **config/registry.py** | config/registry.py | Single source of truth for paths, CacheFiles, StateFiles, LogFiles, thresholds. | **VERIFIED_ACCURATE** — Dashboard and scripts import from here; paths consistent. |
| **reports/DASHBOARD_ENDPOINT_MAP.md** | reports/DASHBOARD_ENDPOINT_MAP.md | Panel → endpoint → data location. | **VERIFIED_ACCURATE** — Matches dashboard.py routes and _DASHBOARD_ROOT resolution (see DASHBOARD_ENDPOINT_AUDIT.md). |
| **EQUITY_GOVERNANCE_ORCHESTRATOR_RUNBOOK.md** | reports/governance/EQUITY_GOVERNANCE_ORCHESTRATOR_RUNBOOK.md | Equity-only governance: stopping condition, ONLINE autopilot (CURSOR_DROPLET_EQUITY_GOVERNANCE_AUTOPILOT.sh), replay, board review. | **VERIFIED_ACCURATE** — Stopping condition and lock_or_revert_decision.json structure match compare_effectiveness_runs.py; script paths and flow match run_equity_governance_loop_on_droplet.sh. |
| **EXIT_IMPROVEMENT_PLAN.md** | reports/exit_review/EXIT_IMPROVEMENT_PLAN.md | Exit improvement roadmap. | Not re-verified line-by-line; reference only. |
| **WHY_MULTI_FACTOR_EXITS_AND_HOW_TO_REVIEW.md** | reports/exit_review/WHY_MULTI_FACTOR_EXITS_AND_HOW_TO_REVIEW.md | Rationale and review process for multi-factor exits. | **VERIFIED_ACCURATE** — Aligns with exit_score_v2 components and reason codes. |
| **docs/TRUTH_ROOT_CONTRACT.md** | docs/TRUTH_ROOT_CONTRACT.md | Truth root and paths. | Not re-verified; reference. |
| **docs/ALPACA_*.md** | docs/ | Alpaca governance, integrity, lifecycle. | Reference; Alpaca usage in main.py matches env-based keys and paper enforcement. |

---

## Runbooks and procedures

| Doc | Path | Use |
|-----|------|-----|
| Equity governance runbook | reports/governance/EQUITY_GOVERNANCE_ORCHESTRATOR_RUNBOOK.md | How to run ONLINE/OFFLINE autopilot, board review, replay campaign, select_lever_from_replay. |
| Dashboard deploy | MEMORY_BANK.md §6.6 | Push → deploy → pkill dashboard → restart stock-bot → hard-refresh browser. |
| Governance loop | scripts/run_equity_governance_loop_on_droplet.sh | Alternation, no-progress, stagnation→replay; state in state/equity_governance_loop_state.json. |

---

## Governance contracts (behavior)

| Contract | Location | Summary |
|---------|----------|---------|
| Stopping condition | compare_effectiveness_runs.py, EQUITY_GOVERNANCE_ORCHESTRATOR_RUNBOOK.md | expectancy_gt_0, win_rate_ge_baseline_plus_2pp, giveback_le_baseline_plus_005, joined_count_ge_100. |
| lock_or_revert_decision.json | reports/equity_governance/equity_governance_*/lock_or_revert_decision.json | decision, reasons, stopping_condition_met, stopping_checks, baseline, candidate. |
| Replay/gov loop | run_equity_governance_loop_on_droplet.sh, run_equity_replay_campaign.py, select_lever_from_replay.py | Replay produces campaign_results + ranked_candidates; loop can inject replay overlay via state/replay_overlay_config.json. |

---

## Exit / entry review procedures

| Procedure | Script / doc |
|-----------|---------------|
| Last 5 trades (v2 exit check) | scripts/report_last_5_trades.py — run on droplet with --base-dir repo. |
| Effectiveness reports | scripts/analysis/run_effectiveness_reports.py — produces effectiveness_aggregates, entry_vs_exit_blame, exit_effectiveness, signal_effectiveness. |
| Exit effectiveness v2 | scripts/analysis/run_exit_effectiveness_v2.py — reports/exit_review/exit_effectiveness_v2.json. |
| Governance compare | scripts/analysis/compare_effectiveness_runs.py — baseline vs candidate → lock_or_revert_decision.json. |

---

## Known caveats

1. **Giveback:** avg_profit_giveback in effectiveness_aggregates is often null; stopping_checks.giveback_le_baseline_plus_005 then stays None and stopping_condition_met cannot be True until giveback is populated (see GOVERNANCE_AND_REPLAY_AUDIT.md, FIVE_IDEAS_PROFITABILITY).
2. **Entry attribution:** context.attribution_components in logs/attribution.jsonl is sometimes missing → signal_effectiveness.json empty; board recommends fixing so signal_effectiveness populates.
3. **Dashboard URL:** MEMORY_BANK mentions 104.236.102.57:5000; confirm current droplet IP/host if changed.
4. **Golden Workflow:** MEMORY_BANK mandates push→GitHub→droplet→verify; audit did not change code or deploy.

---

## For Cursor (quick reference)

- **Config/paths:** config/registry.py (Paths, CacheFiles, StateFiles, LogFiles).
- **Dashboard data sources:** reports/DASHBOARD_ENDPOINT_MAP.md; all paths resolved via _DASHBOARD_ROOT in dashboard.py.
- **Governance:** reports/governance/EQUITY_GOVERNANCE_ORCHESTRATOR_RUNBOOK.md; scripts/run_equity_governance_loop_on_droplet.sh; scripts/analysis/compare_effectiveness_runs.py.
- **Replay:** scripts/replay/run_equity_replay_campaign.py → campaign_results.json, ranked_candidates.json; scripts/governance/select_lever_from_replay.py.
- **Exit v2:** src/exit/exit_score_v2.py (5-value return); main.py unpacks and writes v2_exit_score, v2_exit_components, exit_reason_code to exit_intel and logs.
- **Exit attribution schema (canonical):** All exit attribution components use the **`exit_`** prefix for `signal_id` (e.g. exit_flow_deterioration, exit_score_deterioration). See MEMORY_BANK.md §7.12; validation/scenarios/test_exit_attribution_phase4.py enforces no unprefixed components.
- **Tests before promotion:** pytest validation/scenarios/test_exit_attribution_phase4.py validation/scenarios/test_effectiveness_reports.py validation/scenarios/test_attribution_loader_join.py.
