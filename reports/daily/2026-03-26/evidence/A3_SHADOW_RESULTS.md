# A3 shadow results (expectancy score floor)

**Run (UTC):** 2026-03-05 (from last-387 scenario A3; run scripts/shadow/run_a3_expectancy_floor_shadow.py on droplet for live shadow.)

## Parameters

- **Since hours:** 24
- **Baseline floor:** 2.5
- **Delta (one notch):** 0.5
- **Effective floor (shadow):** 2.0

## Deltas

- **Additional admitted trades (would-pass):** 35
- **Estimated PnL delta (USD):** -2.74 **(proxy)**
- **Win rate delta:** not computable without per-block outcome

## Tail-risk notes

- Admitting more low-score trades may increase loss concentration; monitor worst-N if promoted to live.
- Would-admit score range: 2.0–2.5 (effective_floor=2.0).

## Safety

**Shadow only; no live execution changes.** This script does not import or call order placement or gating code.
