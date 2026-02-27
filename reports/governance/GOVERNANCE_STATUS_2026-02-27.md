# Equity governance loop — current status

**As of:** 2026-02-27 (after many hours of runs)  
**Source:** Droplet state, run history, and baseline effectiveness.

---

## Current status

- **Loop:** Running on droplet. Log: `/tmp/equity_governance_autopilot.log`.
- **State:** `last_lever=entry`, `last_decision=REVERT`, `last_candidate_expectancy=-0.217`.
- **Baseline (current):** Expectancy per trade ≈ **-0.096**, win rate ≈ **39.5%** (no overlay).
- **Stopping condition:** Not met (expectancy still &lt; 0; no run has LOCKed).

---

## Have any passed?

**No.** **Zero** runs have passed (LOCK). All **15** completed runs so far ended in **REVERT**.

Stopping requires all of: expectancy &gt; 0, win rate ≥ baseline + 2pp, giveback ≤ baseline + 0.05, joined_count ≥ 100. None of the overlay candidates have met these.

---

## Levers dismissed (REVERT)

Every tried lever worsened expectancy and/or win rate vs baseline, so all were reverted.

| Lever type | Times tried | Result |
|------------|-------------|--------|
| **Entry: min_exec_score = 2.9** | 8 | REVERT — candidate expectancy worse than baseline (~-0.10 to -0.22 vs -0.09) |
| **Exit: flow_deterioration tweak** | 7 | REVERT — candidate expectancy worse |

So far the loop has **only** tried:
- Raising the entry threshold (MIN_EXEC_SCORE 2.9), and  
- Slightly strengthening the exit (flow_deterioration).

The **down-weight worst signal** entry lever has **not** been tried yet: baseline `signal_effectiveness.json` on the droplet is empty (`{}`), so `top5_harmful` is empty and the recommender never selects `entry_lever_type=down_weight_signal`.

---

## Signals with positive vs negative impact

**On the droplet we don’t have per-signal impact right now.**

- `reports/effectiveness_baseline_blame/signal_effectiveness.json` is empty (`{}`).
- So we cannot list “signals dismissed” or “signals with positive impact” from live data.

Empty `signal_effectiveness` usually means either:
- Joined closed trades don’t have `entry_attribution_components` (per-signal contributions), or  
- There aren’t enough such trades in the baseline window to build the report.

Once attribution is populated and effectiveness reports are run on that data, you’ll get:
- **Harmful (dismiss / down-weight):** low win_rate, negative avg_pnl, high MAE.
- **Positive impact:** higher win_rate, positive avg_pnl — candidates to keep or up-weight.

---

## Summary

| Question | Answer |
|----------|--------|
| Current status | Loop running; last decision REVERT (entry lever); baseline exp ≈ -0.096 |
| Any passed? | No — 0 LOCK, 15 REVERT |
| Levers dismissed | Entry min_exec_score=2.9 (8×); exit tweak (7×) |
| Down-weight worst signal tried? | No — not selected (no signal_effectiveness data) |
| List of signals dismissed / positive impact | Not available — baseline signal_effectiveness is empty |

---

## Next steps (optional)

1. **Fix signal_effectiveness on droplet**  
   Ensure joined closed trades include `entry_attribution_components` and re-run effectiveness so `signal_effectiveness.json` is populated. Then the loop can recommend and try the down-weight-worst-signal lever.

2. **Keep loop running**  
   It will keep alternating entry/exit and trying levers until stopping condition is met or you stop it.

3. **Inspect attribution pipeline**  
   Confirm that exit attribution + join step writes component-level entry data into the joined dataset used for effectiveness (so per-signal stats can be computed).
