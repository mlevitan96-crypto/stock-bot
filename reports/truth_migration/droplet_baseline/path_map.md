# Truth path map — writer → file, reader → file (droplet-first baseline)

**Purpose:** Authoritative map of what the live bot writes and what dashboard/EOD/audits read. Derived from codebase and droplet docs; run baseline capture on droplet to confirm.

---

## 1. Current authoritative sources (live on droplet)

| Truth type | Current path(s) | Writer | Reader(s) |
|------------|-----------------|--------|-----------|
| **Trades evidence** | `logs/attribution.jsonl`, `logs/orders.jsonl`, `logs/run.jsonl` (trade_intent, exit_intent) | main.py, AlpacaExecutor | dashboard (closed trades, exec summary), EOD, audits |
| **Gate truth** | `logs/expectancy_gate_truth.jsonl` (when `EXPECTANCY_GATE_TRUTH_LOG=1`) | main.py (expectancy gate block) | full_signal_review_on_droplet, run_closed_loops_checklist, funnel, dashboard contract (panel “Expectancy Gate” may reference `logs/gate_truth.jsonl` — alias or legacy name) |
| **Signal health** | `logs/signal_health.jsonl` | signal_health.append_signal_health (from main.py) | Dashboard contract “Signal Health” |
| **Exit truth** | `logs/exit_truth.jsonl` | src/exit/exit_truth_log.append_exit_truth | Dashboard contract “Exit Truth”, EOD exit review |
| **Exit attribution (v2)** | `logs/exit_attribution.jsonl` | src/exit/exit_attribution.append_exit_attribution | Dashboard closed trades, exit effectiveness, reports |
| **Score telemetry** | `state/score_telemetry.json` | telemetry/score_telemetry.record → _save_telemetry | Dashboard “Score Telemetry” panel, audits |
| **Score snapshot** | `logs/score_snapshot.jsonl` | score_snapshot_writer.append_score_snapshot | Truth audit, funnel, decision ledger, blocked expectancy |
| **Signal score breakdown** | `logs/signal_score_breakdown.jsonl` (when `SIGNAL_SCORE_BREAKDOWN_LOG=1`) | main.py (same block as gate truth) | Signal review, diagnostics |

**Note:** Dashboard contract in scripts references `logs/gate_truth.jsonl`; actual live file is `logs/expectancy_gate_truth.jsonl`. Align contract to one canonical name (CTR: `gates/expectancy.jsonl`).

---

## 2. Writer → legacy path (for mirror)

| Writer / module | Legacy path | CTR path (Phase 1) |
|-----------------|-------------|---------------------|
| exit_attribution | logs/exit_attribution.jsonl | exits/exit_attribution.jsonl |
| exit_truth_log | logs/exit_truth.jsonl | exits/exit_truth.jsonl |
| main.py (expectancy gate truth) | logs/expectancy_gate_truth.jsonl | gates/expectancy.jsonl |
| signal_health | logs/signal_health.jsonl | health/signal_health.jsonl |
| score_telemetry | state/score_telemetry.json | telemetry/score_telemetry.json |
| score_snapshot_writer | logs/score_snapshot.jsonl | telemetry/score_snapshot.jsonl |
| main.py (signal_score_breakdown) | logs/signal_score_breakdown.jsonl | health/signal_score_breakdown.jsonl (optional) |

Execution (orders/fills): optional migration; primary evidence today is `logs/orders.jsonl`, `logs/attribution.jsonl` — can add `execution/orders.jsonl`, `execution/attribution.jsonl` later.

---

## 3. Reader → source (today = legacy; Phase 2 = CTR option)

| Consumer | Current source | Phase 2 (CTR) |
|----------|----------------|---------------|
| Dashboard contract (panels) | See dashboard_contract.json (logs/exit_truth.jsonl, logs/signal_health.jsonl, state/score_telemetry.json, logs/gate_truth.jsonl → expectancy_gate_truth) | Contract points to CTR paths; EOD validates CTR freshness |
| EOD / run_dashboard_truth_audit.sh | Files listed in contract; freshness by mtime | Same; contract path = CTR path |
| full_signal_review_on_droplet | logs/expectancy_gate_truth.jsonl, logs/signal_score_breakdown.jsonl, logs/score_snapshot.jsonl | Can prefer CTR when enabled |
| run_closed_loops_checklist | logs/expectancy_gate_truth.jsonl | Can prefer CTR |

---

## 4. journalctl / run evidence

- **Live trades:** journalctl -u stock-bot.service (evidence: order_id, filled, submit_entry). Not a file path; audit uses log output.

---

## 5. Droplet baseline capture (to run on droplet)

- `reports/truth_migration/droplet_baseline/systemd_snapshot.txt` — output of systemctl show stock-bot, ls -la of WorkingDirectory, env.
- `reports/truth_migration/droplet_baseline/freshness_scan.json` — mtime, size, path for each truth file above.

Script: `scripts/truth/capture_droplet_baseline.sh` (see below or separate deliverable).
