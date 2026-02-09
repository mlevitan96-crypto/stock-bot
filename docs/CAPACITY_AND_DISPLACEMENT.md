# Capacity and Displacement

## Overview

Capacity (max positions) and displacement (replacing a current position with a higher-scoring candidate) control how many positions the engine holds and when it is allowed to swap one position for another. **Regime can influence capacity or displacement policy (e.g. slightly more capacity in high-opportunity regimes) but must never set capacity to zero or fully block trading.**

## Contract

- **Regime is a modifier, not a gate:** No code path may use regime to set capacity to zero or to fully disable trading. Regime may adjust thresholds or preferences only.
- **Displacement:** Governed by `trading/displacement_policy.py` and env/config (see MEMORY_BANK §6.9). Decisions are logged to `logs/system_events.jsonl` with `subsystem=displacement`, `event_type=displacement_evaluated`.
- **Capacity:** Max concurrent positions are set by `MAX_CONCURRENT_POSITIONS` (default 16). Blocked trades are logged to `state/blocked_trades.jsonl` with reasons such as `displacement_blocked`, `max_positions_reached`, `capacity_limit`.

## Displacement Policy

- **Min hold:** Position must be held at least `DISPLACEMENT_MIN_HOLD_SECONDS` (default 1200) before it can be displaced, unless emergency (score &lt; 3 or pnl &lt; -0.5%).
- **Min delta:** Challenger score must exceed current position score by at least `DISPLACEMENT_MIN_DELTA_SCORE` (default 0.75).
- **Thesis dominance:** When `DISPLACEMENT_REQUIRE_THESIS_DOMINANCE` is true, at least one of flow/regime/dark_pool must favor the challenger.
- **Revert:** Set `DISPLACEMENT_MIN_HOLD_SECONDS=0`, `DISPLACEMENT_MIN_DELTA_SCORE=0`, `DISPLACEMENT_REQUIRE_THESIS_DOMINANCE=false` to effectively disable displacement constraints.

## Capacity

- **Max positions:** From config/env `MAX_CONCURRENT_POSITIONS` (default 16). When at capacity, new entries are blocked unless displacement is allowed (challenger displaces an existing position).
- **Per-cycle limits:** `MAX_NEW_POSITIONS_PER_CYCLE` can further limit new entries per loop.

## Monitoring

- **Diagnostic script:** `scripts/displacement_capacity_diagnostic.py` — for the last N days, reports displacement_blocked, max_positions_reached, capacity_blocked by reason and by mode:strategy; optional correlation with current regime.
- **Logs:** Filter `logs/system_events.jsonl` for `subsystem=displacement` and `event_type=displacement_evaluated`; use `details.allowed`, `details.reason`, `details.delta_score`, `details.age_seconds` for audit.
- **Blocked trades:** `state/blocked_trades.jsonl` and EOD/Board reports surface blocked counts by reason.

## Regime-Aware Behavior (Non-Gating)

In high-opportunity regimes (e.g. BEAR for shorts, BULL for longs), capacity or displacement thresholds may be tuned to allow slightly more activity. In low-opportunity regimes, thresholds may be more conservative. **In all cases, trading is never fully blocked by regime alone.** Capacity and displacement blocks are due to position count and policy rules only.
