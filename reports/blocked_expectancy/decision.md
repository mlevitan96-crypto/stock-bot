# Blocked-trade expectancy — decision (Case A/B/C)

## Evidence

- Gate counts on droplet (2026-02-19): **score_below_min** (37, 14, 26) and **expectancy_blocked:score_floor_breach** (1, 14). All candidates blocked; no orders.
- Current threshold: **MIN_EXEC_SCORE = 3.0** (config/registry.py and expectancy_floor in gate).
- Blocked candidates have scores below 3.0; many are in [2.0, 3.0) (score_floor_breach = composite_score < expectancy_floor).

## Case choice: **A — Threshold too high**

- **Rationale:** Scores are not mis-scaled (same composite pipeline as before); the floor at 3.0 is excluding a range of candidates that may be profitable. Replay (when run on droplet with state/blocked_trades.jsonl + bars) will show which score buckets have positive mean expectancy. A single-step, reversible fix is to lower the floor so that the next bucket (e.g. 2.5–3.0) is admitted.
- **Case B (scores mis-scaled):** Not chosen; no signal rescaling without evidence of systematic compression.
- **Case C (both):** Deferred; apply threshold first, then re-evaluate.

## Recommendation

- **Adjust MIN_EXEC_SCORE** from **3.0** to **2.5** (config-only).
- **Expectancy floor** in the expectancy gate is already set from `Config.MIN_EXEC_SCORE` (main.py), so lowering MIN_EXEC_SCORE will lower the floor and admit candidates with composite_score in [2.5, 3.0).
- **Reversible:** Set `MIN_EXEC_SCORE=3.0` in env or revert the default to restore prior behavior.

## Expectancy of admitted bucket

- To be filled after **replay on droplet**: run `python3 scripts/blocked_expectancy_analysis.py` on droplet (or `python scripts/run_blocked_expectancy_on_droplet.py` locally) and read `bucket_analysis.md` for the 2.5–3.0 bucket (mean_pnl_pct, win_rate, n). If that bucket has positive mean expectancy and n ≥ 5, the fix is data-justified.
