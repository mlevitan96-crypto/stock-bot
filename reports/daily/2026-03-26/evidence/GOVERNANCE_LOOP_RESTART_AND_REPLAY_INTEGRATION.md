# Governance Loop Restart and Replay Integration

**Timestamp:** 2026-02-28 (UTC)  
**Orchestrator:** Autonomous multi-model governance orchestrator  
**Commit (droplet):** c9ce815 — Governance: fix overlay lever .lower() on None; ensure lever string in overlay

---

## Phase 1 — System readiness (verified)

- **reports/audit/EXIT_ATTRIBUTION_PREFIX_FIX_VERIFICATION.md** — present and recent.
- **reports/audit/PHASE1_DROPLET_RESULTS.json** — present; stock_bot_active, uw_daemon_active, alpaca_alignment.
- **reports/audit/PHASE1_ALPACA_ALIGNMENT.json** — present; positions_count 18, status ACTIVE.
- **Pytest spine:** Passed in last deploy (10/10 on droplet: exit_attribution_phase4, effectiveness_reports, attribution_loader_join).
- **/api/governance/status:** Verified pre-restart; response included expectancy_per_trade, win_rate, avg_profit_giveback (null), stopping_condition_met, stopping_checks, source_decision, source_aggregates.

---

## Phase 2 — Replay-driven lever selection (integrated)

**Code changes:**

1. **scripts/governance/select_lever_with_replay.py** (new)  
   - Loads live recommendation (recommendation.json) and baseline effectiveness_aggregates (live expectancy).  
   - Finds latest `reports/replay/equity_replay_campaign_*/` and reads ranked_candidates (from ranked_candidates.json or campaign_results.json).  
   - **Hierarchy:** If no-progress or alternation set FORCE_LEVER in the loop, autopilot uses it. Else:  
     - Compare live vs top replay candidate (expectancy, trade_count ≥ 30).  
     - If replay has trade_count ≥ 30 and replay expectancy > live baseline expectancy → choose replay lever and build overlay from replay candidate.  
     - Else → use live recommendation and build overlay from live (GOVERNANCE_ENTRY_THRESHOLD / GOVERNANCE_EXIT_STRENGTH).  
   - Writes **overlay_config.json** for the cycle and prints chosen lever (entry/exit).

2. **scripts/CURSOR_DROPLET_EQUITY_GOVERNANCE_AUTOPILOT.sh**  
   - **A2:** When FORCE_LEVER is unset, runs `select_lever_with_replay.py` (recommendation, baseline-dir, out-dir); LEVER set from script output; overlay_config.json written by script.  
   - **A3:** (1) If REPLAY_OVERLAY_CONFIG set (stagnation path) → use that overlay. (2) Else if OUT_DIR/overlay_config.json exists (from replay-driven selection) → use it. (3) Else build overlay from LEVER + recommendation (inline Python).  
   - Defensive fix: `(j.get('lever') or 'exit').lower()` when reading overlay to avoid AttributeError on None.

**Loop script (run_equity_governance_loop_on_droplet.sh)** unchanged in hierarchy:  
- No-progress override → force opposite lever (entry ↔ exit).  
- Even cycle → force exit (alternation).  
- Stagnation → run replay campaign and use select_lever_from_replay → REPLAY_OVERLAY_CONFIG.  
- Else → autopilot A2 uses select_lever_with_replay (live vs top ranked_candidates).

---

## Phase 3 — Loop restart on droplet

- **Kill:** Existing governance loop processes killed (pkill run_equity_governance_loop_on_droplet, CURSOR_DROPLET_EQUITY_GOVERNANCE_AUTOPILOT).  
- **Sync:** `git fetch origin && git reset --hard origin/main` — droplet at c9ce815.  
- **Start:** `python scripts/governance/run_equity_governance_orchestrator.py online --loop` (from local); orchestrator runs nohup of `scripts/run_equity_governance_loop_on_droplet.sh` on droplet.  
- **PID:** Loop process confirmed (e.g. `bash scripts/run_equity_governance_loop_on_droplet.sh`).  
- **Log:** `/tmp/equity_governance_autopilot.log` (present; line count 9300+).

---

## Phase 4 — Loop startup verification (log tail)

**First cycle (00:17) had a one-off failure** (overlay lever .lower() on None); fixed in c9ce815.

**Second cycle (00:21) — success:**

- **Baseline rebuild:** A1 baseline effectiveness run; joined_count=2320, total_losing_trades=1431; expectancy_gate_diagnostic written.  
- **Lever selection:** A2 Replay-driven lever selection (live vs top replay candidate).  
  - Lever selection: **live -> entry** (live_expectancy=-0.087621, overlay_config written).  
  - No ranked_candidates or replay not stronger → live recommendation used.  
- **A3:** Using overlay from replay-driven lever selection → **lever=entry**.  
- **Apply overlay:** paper_overlay.env written (MIN_EXEC_SCORE=2.7); stock-bot restarted with overlay active.  
- **A4:** Waiting for >=100 closed trades (since 2026-02-28); Overlay joined_count=0 (polling).  
- **No attribution or giveback errors** in log; joined rows from baseline (2320) confirm baseline completeness.  
- **Stopping condition:** Evaluable after A5/A6 when overlay window reaches 100 trades; current run is in A4 wait.

---

## Governance / status snapshot

Pre-restart (Phase 1) snapshot from `/api/governance/status`:

- **expectancy_per_trade:** -0.079184  
- **win_rate:** 0.3752  
- **avg_profit_giveback:** null (expected until next effectiveness run with giveback populated)  
- **stopping_condition_met:** false  
- **stopping_checks:** expectancy_gt_0 (false), giveback_le_baseline_plus_005 (null), joined_count_ge_100 (true), win_rate_ge_baseline_plus_2pp (false)  
- **source_decision:** reports/equity_governance/equity_governance_20260227T184644Z/lock_or_revert_decision.json  
- **source_aggregates:** reports/effectiveness_baseline_blame/effectiveness_aggregates.json  

Post-restart, the dashboard may show nulls for the new overlay run until the next lock_or_revert_decision is written (after A5 compare). Endpoint structure and stopping_checks remain correct.

---

## Confirmations

- **Replay-driven lever selection is active:** A2 runs select_lever_with_replay when FORCE_LEVER is unset; log shows "A2 Replay-driven lever selection (live vs top replay candidate)" and "Lever selection: live -> entry (live_expectancy=..., overlay_config written)".  
- **Attribution and giveback:** Baseline run completed with joined_count 2320; no attribution or giveback errors in log; giveback logic and exit_ prefix (canonical) in place from prior deploy.  
- **Stopping condition evaluable:** Stopping checks (expectancy_gt_0, win_rate_ge_baseline_plus_2pp, giveback_le_baseline_plus_005, joined_count_ge_100) are computed in compare_effectiveness_runs and written to lock_or_revert_decision.json; dashboard reads them for /api/governance/status.  
- **No manual overlay or config changes:** Only loop restart and selection logic upgrade; no live trading config or overlay applied manually.

---

## First 50–60 lines of loop log (successful cycle 00:21)

```
[2026-02-28T00:21:49Z] === GOVERNANCE CYCLE 1 ===
[2026-02-28T00:21:49Z] Lever variety: cycle=1 ENTRY_THRESHOLD=2.7 EXIT_STRENGTH=0.02
[2026-02-28T00:21:49Z] === EQUITY GOVERNANCE AUTOPILOT (100-trade gate) ===
[2026-02-28T00:21:49Z] OUT_DIR=reports/equity_governance/equity_governance_20260228T002149Z BASELINE_DIR=reports/effectiveness_baseline_blame
[2026-02-28T00:21:49Z] MIN_CLOSED_TRADES=100
[2026-02-28T00:21:49Z] A1 Baseline effectiveness (equity from logs) -> reports/effectiveness_baseline_blame
...
[2026-02-28T00:21:49Z] Baseline joined_count=2320 total_losing_trades=1431
...
[2026-02-28T00:21:50Z] A2 Replay-driven lever selection (live vs top replay candidate)
Lever selection: live -> entry (live_expectancy=-0.087621, overlay_config written)
[2026-02-28T00:21:50Z] Lever=entry
[2026-02-28T00:21:50Z] A3 Using overlay from replay-driven lever selection -> lever=entry
...
[2026-02-28T00:21:52Z] A3 Restarted stock-bot with overlay active
[2026-02-28T00:21:52Z] A4 Waiting for >=100 closed trades (since 2026-02-28)
[2026-02-28T00:21:53Z] Overlay joined_count=0
```

---

**Verification complete.** Equity governance loop restarted with replay-driven lever selection integrated; loop is running and waiting for the next 100 closed trades before A5 compare and stopping-condition check.
