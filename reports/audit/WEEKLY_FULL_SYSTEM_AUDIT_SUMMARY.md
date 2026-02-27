# Weekly Full System Audit — Summary

**Date:** 2026-02-27  
**Scope:** Live services, APIs (Alpaca), dashboards, exit/entry logic (v2), governance loop, replay engine, signals, tests, Memory Bank.  
**Rule observed:** No live trading levers changed; inspection and documentation only.

---

## Critical (RED) — Must fix before next live week

| Issue | Where | Action |
|-------|--------|--------|
| **Giveback never populated** | effectiveness_aggregates.avg_profit_giveback; stopping_checks.giveback_le_baseline_plus_005 | Stopping condition cannot be met until giveback is computed. Trace exit_quality_metrics.profit_giveback from exit_attribution join → effectiveness aggregation; fix pipeline or defaults so giveback is non-null when MFE/data allow. |
| **Droplet service/log state not verified** | Phase 1 | Run service checks on droplet (systemctl status stock-bot, uw-flow-daemon; journalctl; confirm no orphan main/dashboard). Capture result in SERVICES_AND_APIS_STATUS.md or linked proof. |

---

## Important (YELLOW) — Should fix soon

| Issue | Where | Action |
|-------|--------|--------|
| **Entry attribution missing → signal_effectiveness empty** | logs/attribution.jsonl context.attribution_components | Ensure every open_* record includes context.attribution_components (list of {signal_id, contribution_to_score}). Re-run effectiveness so signal_effectiveness.json populates; unblocks “down-weight worst signal” lever. |
| **Orphan processes (from prior reports)** | Droplet: tmux main.py, uw_flow_daemon not from service | Standardize: single main from stock-bot.service; single UW daemon from uw-flow-daemon.service. Use scripts/kill_droplet_duplicates.py --dry-run then fix. |
| **Dashboard giveback not exposed** | Dashboard has no panel for avg_profit_giveback | Stopping condition depends on giveback; consider a small “Governance” panel or link showing latest effectiveness_aggregates path and key fields (or “Run effectiveness report” hint). |
| **Tests not run in audit** | validation/scenarios/ | Add to pre-promotion checklist: run pytest for test_exit_attribution_phase4, test_effectiveness_reports, test_attribution_loader_join (install pytest if needed). |

---

## Solid (GREEN) — Confirmed correct

| Area | Finding |
|------|--------|
| **v2 exit fix** | exit_score_v2 returns 5 values; main.py unpacks all 5 and writes v2_exit_score, v2_exit_components, exit_reason_code to exit_intel and logs. No 4-value bug. |
| **Governance loop structure** | Alternation (even cycle = exit), no-progress override, 100-trade gate, stopping_checks schema, state file update — all verified in script and compare_effectiveness_runs.py. |
| **Replay engine** | run_equity_replay_campaign.py, build_canonical_equity_ledger.py, select_lever_from_replay.py — structure and I/O verified. |
| **Dashboard endpoints** | Panel → endpoint → file mapping matches dashboard.py and registry; paths use _DASHBOARD_ROOT. |
| **Alpaca integration (code)** | Keys from env; paper enforcement; get_account/positions used correctly. No code bugs found. |
| **Exit attribution tests** | test_exit_attribution_phase4 enforces 5-value return, reason_code in allowed set, attribution sum = score. |
| **Effectiveness report logic** | build_exit_effectiveness, build_entry_vs_exit_blame, effectiveness_aggregates — logic verified; giveback propagation is the gap. |
| **Memory Bank / runbook alignment** | SERVICE_NAME, script paths, stopping condition text, lock_or_revert_decision schema — match code. |

---

## Prioritized recommendations

### P0 — Must fix before next live week

1. **Populate giveback:** Fix effectiveness pipeline so avg_profit_giveback is set when exit_quality_metrics.profit_giveback exists on joined rows; re-run effectiveness on droplet and confirm stopping_checks.giveback_le_baseline_plus_005 can be True.
2. **Verify droplet services:** Run Phase 1 commands on droplet; document status (stock-bot.service, uw-flow-daemon, logs, orphans) and any Alpaca discrepancy.

### P1 — Should fix soon

3. **Entry attribution:** Ensure attribution.jsonl logs context.attribution_components for every entry; re-run effectiveness so signal_effectiveness.json is usable.
4. **Clean processes:** Resolve orphan main.py / uw_flow_daemon; run kill_droplet_duplicates (dry-run first).
5. **Pre-promotion tests:** Document and run pytest for exit attribution + effectiveness + attribution_loader_join before any lever promotion.

### P2 — Nice-to-have / future hardening

6. **Governance panel:** Dashboard widget or link for latest effectiveness_aggregates (joined_count, win_rate, expectancy, giveback) or “Run effectiveness report.”
7. **Regression test:** Add test that main.py’s use of compute_exit_score_v2 is 5-value unpack (e.g. import and assert or minimal harness).
8. **MEMORY_BANK_INDEX:** Keep reports/audit/MEMORY_BANK_INDEX.md updated when new runbooks or contracts are added.

---

## For Cursor (future runs)

- **Memory Bank:** Use MEMORY_BANK.md for behavior and contracts; use reports/audit/MEMORY_BANK_INDEX.md for doc index and caveats.
- **Canonical dashboards/endpoints:** reports/DASHBOARD_ENDPOINT_MAP.md; canonical closed trades = logs/attribution.jsonl + logs/exit_attribution.jsonl (join).
- **Governance and replay:** Trust scripts/run_equity_governance_loop_on_droplet.sh, scripts/analysis/compare_effectiveness_runs.py, scripts/replay/run_equity_replay_campaign.py, scripts/governance/select_lever_from_replay.py. Latest decision = reports/equity_governance/equity_governance_*/lock_or_revert_decision.json.
- **Tests before promotion:** Run `pytest validation/scenarios/test_exit_attribution_phase4.py validation/scenarios/test_effectiveness_reports.py validation/scenarios/test_attribution_loader_join.py`.
- **What’s real:** v2 exit is live in code; governance loop and replay are structurally sound; giveback and entry attribution are the main data gaps. **What’s broken:** giveback null prevents stopping condition; droplet state unverified in this run. **What to fix next:** P0 then P1 list above.

---

## Audit artifacts (all in reports/audit/)

| File | Content |
|------|---------|
| WEEKLY_FULL_SYSTEM_AUDIT.md | Phase 0 — Full checklist (services, APIs, dashboards, exit/entry, governance, replay, signals, tests, Memory Bank). |
| SERVICES_AND_APIS_STATUS.md | Phase 1 — Services and Alpaca integration; droplet commands to run. |
| DASHBOARD_ENDPOINT_AUDIT.md | Phase 2 — Panel → endpoint → file → schema; canonical sources; recommendations. |
| EXIT_ENTRY_AUDIT.md | Phase 3 — v2 exit code verification; report_last_5_trades and effectiveness; droplet checks. |
| GOVERNANCE_AND_REPLAY_AUDIT.md | Phase 4 — Loop script, lock_or_revert_decision, replay campaign, canonical ledger. |
| SIGNALS_AND_TESTS_AUDIT.md | Phase 5 — Exit/entry signals list; tests and diagnostics; recommendations. |
| MEMORY_BANK_INDEX.md | Phase 6 — Key docs, runbooks, contracts, verification status, caveats, “For Cursor” quick ref. |
| WEEKLY_FULL_SYSTEM_AUDIT_SUMMARY.md | Phase 7 — This summary (RED/YELLOW/GREEN, P0/P1/P2, For Cursor). |
