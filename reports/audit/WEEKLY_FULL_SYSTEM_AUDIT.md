# Weekly Full System Audit — Checklist

**Purpose:** Deep, adversarial, end-to-end audit of the equity trading system.  
**Scope:** Live services, APIs (Alpaca), dashboards, exit/entry logic (v2), governance loop, replay engine, signals, tests, Memory Bank.  
**Rule:** Do NOT change live trading levers; only inspect, verify, and document.

---

## 1. Services & Processes

| Item | What "healthy" means | What to inspect | Commands / scripts | Evidence to capture |
|------|----------------------|-----------------|-------------------|----------------------|
| stock-bot.service | active, running; deploy_supervisor → main, dashboard, heartbeat | Unit status, WorkingDirectory, ExecStart, drop-in env | `systemctl status stock-bot.service`, `systemctl show stock-bot.service -p Environment` | Status output, env (no secrets), journalctl last 100 lines |
| uw-flow-daemon.service | active if UW flow needed; single instance | Unit status; lock file `state/uw_flow_daemon.lock` | `systemctl is-active uw-flow-daemon.service`, `ls state/uw_flow_daemon.lock` | Status; note if daemon runs outside service (orphan process) |
| Governance loop | Not required to be "running" as a service; when run: completes cycle and writes state | `state/equity_governance_loop_state.json`, `/tmp/equity_governance_autopilot.log` | `cat state/equity_governance_loop_state.json`, `tail -200 /tmp/equity_governance_autopilot.log` | State JSON, log tail |
| Dashboard / API | Dashboard served (e.g. port 5000 or 8080); /api/ping returns 200 | Process listening, /api/ping, /api/version | `curl -s http://localhost:PORT/api/ping`, `curl -s http://localhost:PORT/api/version` | Response body, status code |

**Adversarial checks:** Orphan `main.py` or duplicate `uw_flow_daemon.py` (see `scripts/list_droplet_processes.py`, `scripts/kill_droplet_duplicates.py`). Root disk full (can break logs).

---

## 2. APIs & Broker Integration (Alpaca)

| Item | What "healthy" means | What to inspect | Commands / scripts | Evidence to capture |
|------|----------------------|-----------------|-------------------|----------------------|
| API keys loaded | Keys present (no print of secrets); no RuntimeError from Alpaca | Env from stock-bot.service (masked); main.py / config load | `systemctl show stock-bot.service -p Environment \| tr ' ' '\n' \| grep -E '^ALPACA\|^APCA' \| sed 's/=.*/=***/'` | Confirmation keys exist; no raw keys |
| Positions | System view matches Alpaca dashboard within tolerance | `state/position_metadata.json`, Alpaca API positions | Dashboard `/api/positions` or Alpaca API | Positions count, symbols; note any delta |
| Recent fills | Last N orders/fills consistent | `logs/orders.jsonl`, `logs/trading.jsonl`, Alpaca orders | `tail -20 logs/orders.jsonl`, Alpaca dashboard | Fill count, side, symbol, qty |
| Cash / PnL | Cash and PnL align with Alpaca (e.g. same day) | `state/daily_start_equity.json`, Alpaca account | `/api/pnl/reconcile`, Alpaca account endpoint | Cash, equity, PnL for week |

**Adversarial checks:** Stale daily_start_equity; attribution.jsonl vs Alpaca order IDs; paper vs live key mix-up.

---

## 3. Dashboards & Data Correctness

| Item | What "healthy" means | What to inspect | Commands / scripts | Evidence to capture |
|------|----------------------|-----------------|-------------------|----------------------|
| Endpoint map | Every panel’s data source exists and is readable | `reports/DASHBOARD_ENDPOINT_MAP.md`, dashboard.py routes | Grep routes in dashboard.py; resolve paths from config/registry | Panel → endpoint → file path → schema |
| Key metrics | P&L, win rate, trade count match effectiveness_aggregates / truth_root / Alpaca | effectiveness_aggregates.json, entry_vs_exit_blame.json, dashboard API responses | `cat reports/effectiveness_*/effectiveness_aggregates.json`, `curl /api/executive_summary` | JSON excerpts; mismatch list |
| Schema | Dashboard expects fields that exist in source files | registry paths, dashboard code reading JSON/JSONL | Read dashboard handlers for /api/stockbot/closed_trades, /api/pnl/reconcile | List of required keys; verification result |

**Canonical sources (per MEMORY_BANK / DASHBOARD_ENDPOINT_MAP):**  
- Closed trades: `logs/attribution.jsonl`, `logs/exit_attribution.jsonl`.  
- PnL reconcile: Alpaca API, `state/daily_start_equity.json`, `logs/attribution.jsonl`.  
- Health: `state/health.json`, `/api/system/health`.

---

## 4. Exit / Entry Logic & Attribution (incl. v2 Exit Fix)

| Item | What "healthy" means | What to inspect | Commands / scripts | Evidence to capture |
|------|----------------------|-----------------|-------------------|----------------------|
| v2 exit live | main.py uses 5-value return from compute_exit_score_v2; no 4-value unpack | `src/exit/exit_score_v2.py`, main.py call site | Grep `compute_exit_score_v2` and unpack in main.py | Line numbers; confirm 5 values |
| report_last_5_trades | v2_exit_score, v2_exit_components, exit_reason_code present | Script output, joined rows from attribution_loader | `python scripts/report_last_5_trades.py --base-dir . --n 5` | Sample output; presence of v2 fields |
| exit_attribution.jsonl | Each line has v2_exit_components, v2_exit_score, exit_reason_code | `logs/exit_attribution.jsonl` | `tail -5 logs/exit_attribution.jsonl \| jq -c '{v2_exit_score,v2_exit_components,exit_reason_code}'` | Sample lines |
| Entry MIN_EXEC_SCORE | Overlays applied (e.g. paper-overlay.conf); env visible in service | systemd drop-in, GOVERNANCE_ENTRY_THRESHOLD / MIN_EXEC_SCORE | `cat /etc/systemd/system/stock-bot.service.d/*.conf` (no secrets) | Threshold in use |
| Effectiveness reports | entry_vs_exit_blame, exit_effectiveness, effectiveness_aggregates | run_effectiveness_reports.py output dirs | `python scripts/analysis/run_effectiveness_reports.py --start 2026-02-01 --end 2026-02-27 --out-dir reports/audit/effectiveness_sample` | Aggregates JSON; blame JSON; exit_effectiveness JSON |

**Adversarial checks:** All exits coded as "signal_decay"; one signal dominating exit_reason_code; missing attribution_components in attribution.jsonl.

---

## 5. Governance Loop & Replay Engine

| Item | What "healthy" means | What to inspect | Commands / scripts | Evidence to capture |
|------|----------------------|-----------------|-------------------|----------------------|
| Loop script | Alternation (even cycle = exit), no-progress override, 100-trade gate, stopping condition | `scripts/run_equity_governance_loop_on_droplet.sh`, state file | Read script; `cat state/equity_governance_loop_state.json` | State schema; cycle logic |
| lock_or_revert_decision.json | stopping_condition_met, stopping_checks (expectancy_gt_0, win_rate_ge_*, giveback_le_*, joined_count_ge_100) | Latest `reports/equity_governance/equity_governance_*/lock_or_revert_decision.json` | `cat reports/equity_governance/equity_governance_*/lock_or_revert_decision.json` (latest) | Full JSON |
| compare_effectiveness_runs | LOCK/REVERT logic and stopping_checks match design | `scripts/analysis/compare_effectiveness_runs.py` | Read code; run with baseline/candidate dirs | Decision output |
| Replay: canonical ledger | Optional: canonical_equity_trades.jsonl exists and recent | `reports/replay/canonical_equity_trades.jsonl` | `python scripts/replay/build_canonical_equity_ledger.py --out reports/replay/canonical_equity_trades.jsonl` | File presence, line count |
| Replay campaign | run_equity_replay_campaign.py produces campaign_results.json, ranked_candidates.json | `reports/replay/equity_replay_campaign_*/` | `python scripts/replay/run_equity_replay_campaign.py` | campaign_results.json; ranked_candidates.json; sanity check trade_count, expectancy |

**Adversarial checks:** giveback null in effectiveness_aggregates (stopping check giveback_le_baseline_plus_005 always null). Replay candidates with trade_count &lt; 30 or unrealistic expectancy.

---

## 6. Signals & Features

| Item | What "healthy" means | What to inspect | Commands / scripts | Evidence to capture |
|------|----------------------|-----------------|-------------------|----------------------|
| Enumeration | All entry/exit signals listed and mapped to code | main.py, exit_score_v2.py, uw_composite_v2 / scoring | Grep signal_id, flow_deterioration, score_deterioration, etc. | List of signal_ids and sources |
| Computation | No constant or NaN-heavy signals | Logs, telemetry, score distribution | `/api/scores/distribution`, logs | Sample distributions |
| Attribution | Each signal present in attribution and effectiveness | attribution.jsonl context.attribution_components; exit_attribution v2_exit_components | report_last_5_trades; signal_effectiveness.json | Per-signal presence |

---

## 7. Tests & Diagnostics

| Item | What "healthy" means | What to inspect | Commands / scripts | Evidence to capture |
|------|----------------------|-----------------|-------------------|----------------------|
| Unit / integration | Relevant tests pass | validation/scenarios/, tests/, scripts/test_*.py | `pytest validation/ tests/ -v --tb=short` (or project test runner) | Pass/fail count; failures |
| Diagnostics | Dry-run selectors, synthetic lab, Alpaca connection test | scripts/test_alpaca_connection.py, dashboard audit | `python scripts/test_alpaca_connection.py` (with env); `python scripts/dashboard_uw_audit.py` | Exit code; key output |
| Regression | Exit attribution and effectiveness tests exist and pass | test_exit_attribution_phase4, test_effectiveness_reports, test_attribution_loader_join | Run above tests | Status |

---

## 8. Memory Bank & Documentation

| Item | What "healthy" means | What to inspect | Commands / scripts | Evidence to capture |
|------|----------------------|-----------------|-------------------|----------------------|
| MEMORY_BANK.md | Claims match code and droplet (services, paths, contracts) | MEMORY_BANK.md vs config/registry.py, deploy paths, service names | Diff key sections vs actual paths and behavior | VERIFIED_ACCURATE / PARTIALLY_STALE / STALE_OR_WRONG |
| Runbooks | EQUITY_GOVERNANCE_ORCHESTRATOR_RUNBOOK, EXIT_IMPROVEMENT_PLAN, WHY_MULTI_FACTOR_EXITS | reports/governance/, reports/exit_review/ | Read and cross-check with scripts and state | Section-by-section verification |
| MEMORY_BANK_INDEX | Single index of key docs, summaries, links, caveats | New or updated MEMORY_BANK_INDEX.md in repo | Create/update reports/audit/MEMORY_BANK_INDEX.md | Index file |

---

## Execution Order

1. **Phase 0** — This checklist (refine with adversarial pass).
2. **Phase 1** — Services & APIs → SERVICES_AND_APIS_STATUS.md.
3. **Phase 2** — Dashboards → DASHBOARD_ENDPOINT_AUDIT.md.
4. **Phase 3** — Exit/entry & attribution → EXIT_ENTRY_AUDIT.md.
5. **Phase 4** — Governance & replay → GOVERNANCE_AND_REPLAY_AUDIT.md.
6. **Phase 5** — Signals & tests → SIGNALS_AND_TESTS_AUDIT.md.
7. **Phase 6** — Memory Bank & docs → MEMORY_BANK_INDEX.md + verification table.
8. **Phase 7** — Synthesis → WEEKLY_FULL_SYSTEM_AUDIT_SUMMARY.md.

---

*Generated for weekly full system audit. Run on droplet where possible; local-only checks marked in phase reports.*
