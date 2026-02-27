# Nuclear audit — Plan review (multi-model BEFORE)

**Date:** 2026-02-18  
**Purpose:** Review audit plan and failure modes before running destructive/stop actions.  
**Scope:** Entries + data + wiring on droplet; assume system broken until proven clean.

---

## Audit plan summary

- **Runtime:** tmux session, pane capture, state file (no GOVERNED_TUNING_CONFIG/overlay).
- **Git/drift:** HEAD, status, last 20 commits, critical file modifications.
- **Config/env:** Key env vars, effective config (MAX_OPEN_POSITIONS, caps, thresholds, cooldowns, paper flags), “disable entries” check.
- **Data freshness:** Market data timestamps, caches, system time.
- **Entry pipeline:** Evidence from logs (candidates, gate_counts, rejection reasons) or safe diagnostic; candidate_count, selected_count, top rejection reasons.
- **Positions/capacity:** Bot state positions, exchange paper positions, why open=0, cap blocking.
- **Logs/attribution:** attribution.jsonl, exit_attribution.jsonl recently appended; expected keys and join keys.
- **Recent errors:** ERROR/Traceback in last N minutes/hours; repeated exceptions.

**No destructive/stop actions** in this audit (read-only plus existing process observation). The only “invasive” step is reading logs and state; we do not kill tmux or change config.

---

## Multi-model review (BEFORE)

### Adversarial

| Risk | Mitigation |
|------|------------|
| Audit script itself has a bug and misreports “PASS” (false negative). | Verdict rules are explicit (FAIL if process not running, entries disabled, data stale, 0 candidates without reason, repeated exceptions, attribution not flowing). Multiple proof files allow manual spot-check. |
| We trust “gate_counts” from logs but the main loop stopped writing them (e.g. crash before cycle_summary). | We require both (1) recent cycle_summary lines with considered/gate_counts and (2) heartbeat/timestamps in tmux pane; if no recent cycle_summary, we treat as “no evidence” → FAIL or unclear. |
| Config dump is incomplete and we miss a “disable entries” switch. | We explicitly grep for PAPER/LIVE, MAX_*POSITIONS, MIN_EXEC_SCORE, and any env that might disable trading; we list “disable entries” as explicit check. |
| Data “freshness” is checked via file mtime but the feed is broken and files are touched by something else. | We record file mtime and size; we also check system time. If we have no separate “feed health” API, we note “freshness = file timestamps only” in report. |

**Verdict:** Plan is sound for a read-only audit. Biggest residual risk: false PASS if log parsing misses a silent failure (e.g. loop running but never reaching entry logic). We mitigate by requiring both runtime heartbeat and entry-pipeline evidence (candidates or clear gating reason).

---

### Quant

| Risk | Mitigation |
|------|------------|
| “Top rejection reasons” from gate.jsonl are aggregated over a short window and may be noisy. | We report raw counts and last N cycle_summary lines; verdict uses “clear, correct gating reason” not “statistically significant.” |
| candidate_count = 0 could be correct (market closed, no clusters). | We require “clear reason” (e.g. no_clusters, market_closed_block_entry, or time window). We check system time and session filters so “market closed” is verifiable. |
| Attribution join keys (trade_id) might be missing on one side only after a deploy. | We explicitly verify join keys on both attribution.jsonl and exit_attribution.jsonl and note in 07. |

**Verdict:** Plan is sufficient for a binary PASS/FAIL and “why no open trades?”. For deeper quant work (e.g. score distribution of candidates), a separate diagnostic run would be needed; this audit does not do that.

---

### Product

| Risk | Mitigation |
|------|------------|
| Audit runs but user still has “no open trades” and no actionable next step. | Deliverables include “top 5 blockers” and “exact next actions (max 5), each tied to a proof file section.” So every blocker maps to a report section and a concrete fix. |
| Running the script from a different machine than droplet could confuse paths. | Script uses DropletClient and runs all commands on droplet in project_dir; proof artifacts are written locally under reports/nuclear_audit/<date>/. |
| Multi-model “after” review might be forgotten. | We mandate 20260218_results_review.md after results, challenging conclusions and proposing smallest corrective action. |

**Verdict:** Plan aligns with product goal: prove or disprove “entries + data + wiring” and give a clear next-action list. No tuning or strategy changes.

---

## Failure modes considered

1. **Paper process not running** → FAIL; proof in 01_runtime_health.md.
2. **Process running but stuck (no new cycle_summary)** → FAIL; evidence in 01 (pane) and 05 (no recent gate cycle_summary).
3. **Entries disabled by config** → FAIL; evidence in 03_config_and_env.md.
4. **Data stale** → FAIL; evidence in 04_data_freshness.md.
5. **0 candidates with no clear reason** → FAIL; evidence in 05_entry_pipeline_evidence.md.
6. **Repeated exceptions in loop** → FAIL; evidence in 08_recent_errors.md.
7. **Attribution/logging not flowing** → FAIL; evidence in 07_logs_and_attribution_flow.md.
8. **Hidden drift (critical file modified)** → FAIL; evidence in 02_git_and_drift.md.

---

## Go / no-go

- **Go.** No destructive actions; audit is read-only and observation-only. Proceed to run `scripts/run_nuclear_audit_on_droplet.py` and produce the report bundle. After results, complete `reports/nuclear_audit/20260218_results_review.md` with multi-model challenge and smallest corrective action.
