# Multi-cycle expectancy smoothing — note

**Idea:** Track expectancy over the last N cycles, detect stagnation, then trigger a replay-driven or regime-aware "jump" lever to accelerate convergence.

**Why it helps:**
- Alternation and no-progress already force lever switches, but they're local (entry ↔ exit). If both are stuck in a flat band, we never try a *different* exit strength or a replay-top candidate that might be outside the current band.
- Smoothing over N cycles (e.g. 3–5) filters noise; stagnation = no material improvement over that window.
- A "jump" injects a replay-ranked or regime-specific lever so the loop can escape local plateaus.

**Risks:**
- Replay is trained on historical joined data; live regime may differ, so replay lever can underperform (we still LOCK/REVERT on 100 trades).
- Regime-aware levers need regime labels in the data and a clear policy (e.g. "in high-vol downtrend, tighten entry"); that's a larger change.

**Implementation (done):**
- State: `expectancy_history` (last 5 LOCK-cycle expectancies) and `last_replay_jump_cycle` in `state/equity_governance_loop_state.json`.
- Stagnation: last 3 LOCK expectancies with range < ε (0.012); cooldown 2 cycles before another jump.
- Jump: `run_equity_replay_campaign.py` → `select_lever_from_replay.py --campaign-dir <latest> --out state/replay_overlay_config.json`; autopilot reads `REPLAY_OVERLAY_CONFIG` in A3 and uses that overlay for one cycle.
- Loop: `scripts/run_equity_governance_loop_on_droplet.sh`; autopilot: `scripts/CURSOR_DROPLET_EQUITY_GOVERNANCE_AUTOPILOT.sh` (A3 branch for replay overlay).

This is optional and accelerates convergence when the loop is otherwise stuck.
