# Equity Governance Orchestrator — Runbook

## Scope

- **Strategy:** EQUITY ONLY (wheel ignored).
- **Live engine:** stock-bot.service on droplet.
- **Data:** attribution.jsonl, exit_attribution.jsonl, effectiveness reports, equity only.
- **ONLINE:** Autopilot with 100-trade gate and global stopping condition.
- **OFFLINE:** Equity replay engine (historical trades, campaign of candidate levers).

## Global Stopping Condition (LIVE)

Stop the live improvement loop only when **all** are true over the last ≥100 closed equity trades in the overlay window:

1. **Expectancy > 0** (expectancy_per_trade in effectiveness_aggregates.json).
2. **Win rate ≥ baseline + 2 percentage points.**
3. **Giveback ≤ baseline + 0.05.**
4. **Attribution healthy:** joined_count ≥ 100, no missing fields.

When met: stop applying new levers, write final summary, leave locked config active.

**Continued evaluation:** Each cycle writes `lock_or_revert_decision.json` with `stopping_checks` (expectancy_gt_0, win_rate_ge_baseline_plus_2pp, giveback_le_baseline_plus_005, joined_count_ge_100) so you can see how close you are to the stop. Entry strength lever: recommendation includes `suggested_min_exec_score` (2.7 or 2.9); overlay can use absolute threshold for continued evaluation.

### Risk brake (manual)

If drawdown is unacceptable while the loop runs: **raise MIN_EXEC_SCORE** (e.g. to 3.0) or **pause new entries** until the next lever is applied. Document as a temporary brake; do not change the loop logic. To apply: set env or drop-in MIN_EXEC_SCORE and restart stock-bot; or use overlay with `min_exec_score` in change.

## Part A — ONLINE Autopilot (100-trade gate)

- **Script:** `scripts/CURSOR_DROPLET_EQUITY_GOVERNANCE_AUTOPILOT.sh`
- **Log:** `/tmp/equity_governance_autopilot.log`
- **Cycle:** A1 baseline → A2 lever (entry/exit) → A3 apply overlay → A4 wait ≥100 trades → A5 compare → A6 act (LOCK/REVERT or stop if stopping condition met).

Start on droplet (background):

```bash
python scripts/governance/run_equity_governance_orchestrator.py online
```

Or SSH and run manually:

```bash
cd /root/stock-bot && nohup bash -c 'bash scripts/CURSOR_DROPLET_EQUITY_GOVERNANCE_AUTOPILOT.sh' >> /tmp/equity_governance_autopilot.log 2>&1 &
```

Check status:

```bash
python scripts/governance/run_equity_governance_orchestrator.py status
```

### Board and persona review (live on droplet)

After each governance cycle the loop runs **board and persona review**: Adversarial, Quant, Product/Operator, Execution/SRE, Risk, and Board verdict. It reads current data (state, lock_or_revert_decision, effectiveness_aggregates, expectancy_gate_diagnostic, recommendation) and prior docs (STRATEGIC_REVIEW, PERSONAS_WHAT_TO_DO_DIFFERENTLY, FIVE_IDEAS) and writes:

- `reports/governance/board_review_<timestamp>.md` and `.json`
- `reports/governance/board_review_latest.md` and `board_review_latest.json`

Script: `scripts/governance/run_board_persona_review.py`. To run standalone on droplet: `python3 scripts/governance/run_board_persona_review.py --base-dir /root/stock-bot --out-dir /root/stock-bot/reports/governance`. Plugins dir (if present) is listed in the review output.

## Part B — OFFLINE Replay Engine

- **Data discovery:** `python scripts/replay/discover_equity_data_manifest.py` → `reports/replay/equity_data_manifest.json`
- **Replay scripts:** `scripts/replay/equity_exit_replay.py`, `equity_entry_replay.py`, `equity_regime_replay.py`, `equity_signal_ablation_replay.py`, `equity_target_replay.py`
- **Campaign:** `python scripts/replay/run_equity_replay_campaign.py` → `reports/replay/equity_replay_campaign_<ts>/campaign_results.json`
- **Feed to autopilot:** `python scripts/governance/select_lever_from_replay.py --campaign-dir reports/replay/equity_replay_campaign_<ts> --out <path>/overlay_config.json`

Run offline (no live changes):

```bash
python scripts/governance/run_equity_governance_orchestrator.py offline
```

## Coordination

- **ONLINE** has priority; it never reads replay directly in the current shell script — replay is used to *propose* levers; operator or a future integration can pass `FORCE_LEVER` or copy overlay_config from `select_lever_from_replay.py` into the autopilot run dir.
- **OFFLINE** never changes live config; it only writes campaign_results and ranked_candidates.
- To use replay in a cycle: run `select_lever_from_replay.py`, copy the generated overlay_config into the autopilot OUT_DIR, then run apply_paper_overlay and the rest of the cycle (or extend the shell script to accept --replay-campaign-dir).

## Files Touched

- `scripts/analysis/run_effectiveness_reports.py`: added total_pnl, expectancy_per_trade to effectiveness_aggregates.json.
- `scripts/analysis/compare_effectiveness_runs.py`: added stopping_condition_met, stopping_checks, expectancy in baseline/candidate.
- `scripts/CURSOR_DROPLET_EQUITY_GOVERNANCE_AUTOPILOT.sh`: 100-trade gate, stopping condition, A1–A6 cycle.
- `scripts/replay/*`: discovery, exit/entry/regime/signal_ablation/target replay, campaign orchestrator.
- `scripts/governance/run_equity_governance_orchestrator.py`: online | offline | status.
- `scripts/governance/select_lever_from_replay.py`: B4 feed replay candidates to autopilot.
