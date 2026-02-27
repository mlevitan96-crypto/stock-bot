# Five Ideas to Move Toward Profitability — Multi-Model Synthesis

**Date:** 2026-02-26  
**Context:** Equity governance loop running (46+ cycles), always LOCK with entry overlay MIN_EXEC_SCORE=2.7; recommender keeps choosing "entry"; expectancy still negative (~-0.09/trade). Goal: positive expectancy over last 100 equity trades, win rate ≥ baseline + 2pp.

---

## Model 1 — Quant / Evidence

**Idea 1: Force exit lever into the governance loop and measure it over 100 trades.**

- **Why:** The recommender uses `weak_entry_pct > exit_timing_pct` → entry. Blame may be biased toward "weak entry" so we never test exit. We already have evidence that an **exit** overlay (flow_deterioration=0.27) improved win rate in a 53-trade run (44.26% vs 39.85% baseline) and was LOCKed; that overlay is not currently active in the loop (only entry overlay is). We have not validated exit over 100 trades in the current governance cycle.
- **Action:** Run 1–2 governance cycles with `FORCE_LEVER=exit`: apply the exit overlay (flow_deterioration 0.27 or a small tweak), wait for 100 overlay trades, compare. If LOCK and expectancy improves, keep it and alternate or combine with entry; if REVERT, we have a clear signal that exit alone doesn’t fix it.
- **Effectiveness:** High — breaks the "always entry" loop and uses existing exit evidence; 100-trade gate keeps the decision evidence-based.

---

## Model 2 — Risk / Execution

**Idea 2: Emit and use giveback in effectiveness so the stopping condition is fully testable.**

- **Why:** Stopping condition requires "giveback ≤ baseline + 0.05", but `avg_profit_giveback` is **null** in effectiveness_aggregates and in lock_or_revert_decision. We can’t satisfy or falsify that leg. Exit_effectiveness and exit_attribution can carry giveback; the join or aggregation may not be populating the top-level aggregate.
- **Action:** (1) Trace where giveback should come from (exit_quality_metrics.profit_giveback, exit_effectiveness by reason). (2) Aggregate giveback into effectiveness_aggregates.json (e.g. weighted average by exit reason frequency). (3) Re-run compare so stopping_checks include giveback. Ensures we’re not declaring "done" or "not done" with a missing dimension.
- **Effectiveness:** Medium–high — unblocks a full, honest stopping check and improves LOCK/REVERT quality.

---

## Model 3 — Product / Strategy**

**Idea 3: Alternate entry and exit levers every cycle instead of following the recommender only.**

- **Why:** The loop is stuck in a local optimum: same entry overlay re-applied and re-LOCKed. Even if blame says "entry", trying exit every other cycle (or every N cycles) explores the lever space and may discover that exit improves expectancy when we have more trades (we had 53-trade exit LOCK; 100-trade exit has not been tried in this loop).
- **Action:** In the governance script: if cycle number is even, use recommender; if odd, force exit (or vice versa). Or: use recommender for 2 cycles, then force the other lever for 1 cycle. Log which lever was forced so we can compare forced vs recommended outcomes.
- **Effectiveness:** High — simple change, no new data; ensures both levers get tested under the same 100-trade gate.

---

## Model 4 — Research / Replay**

**Idea 4: Feed replay campaign’s top candidate into the next governance cycle.**

- **Why:** We have an OFFLINE replay engine (exit/entry sweeps, ranked_candidates) and select_lever_from_replay.py, but the ONLINE loop never reads it. Replay ranks by expectancy/win_rate over historical joined trades; the top candidate may be an exit or entry setting we haven’t tried live.
- **Action:** (1) Run `run_equity_replay_campaign.py` on the droplet (or locally with droplet logs fetched). (2) Run `select_lever_from_replay.py --campaign-dir <latest> --out <path>/overlay_config.json`. (3) Either inject this overlay into the next governance run (e.g. copy overlay_config into OUT_DIR and skip A2 recommendation) or run one "replay-driven" cycle: apply replay’s overlay, 100-trade validate, compare. Compare outcome to recommender-driven cycles.
- **Effectiveness:** Medium–high — uses existing infra; bridges OFFLINE discovery and ONLINE validation; one cycle cost to test.

---

## Model 5 — Operations / Governance**

**Idea 5: Add a "revert if no progress" rule so we don’t spin on the same lever indefinitely.**

- **Why:** 46+ cycles of the same entry overlay (2.7) LOCKing doesn’t move expectancy toward zero. Without a progress check, the loop can run forever without trying a different lever or configuration.
- **Action:** In A6 (after LOCK): compare candidate expectancy to the **previous cycle’s candidate** (or to baseline). If we LOCKed but candidate expectancy did not improve vs last cycle (or vs baseline) by a small epsilon (e.g. +0.01/trade or +1% win rate), then either: (a) force the **other** lever next cycle (entry → exit or exit → entry), or (b) increment lever strength (e.g. MIN_EXEC_SCORE 2.7 → 2.9, or flow_deterioration +0.02). Optionally cap "same lever" at 2–3 consecutive LOCKs; on the next LOCK with no improvement, force the other lever.
- **Effectiveness:** High — prevents infinite re-LOCK of the same overlay; creates pressure to try exit or a stronger entry/exit tweak.

---

## Summary: Most Effective Next Steps (Prioritized)

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| 1 | **Force exit for 1–2 cycles** (FORCE_LEVER=exit) and validate over 100 trades | Breaks entry-only loop; tests exit in current regime | Low |
| 2 | **Alternate entry/exit every cycle** (or every N cycles) in the governance script | Ensures both levers get 100-trade tests | Low |
| 3 | **"No progress" rule:** after LOCK, if expectancy didn’t improve vs last cycle, force other lever or bump strength next cycle | Stops spinning on same lever | Medium |
| 4 | **Emit giveback in effectiveness_aggregates** and use it in stopping_checks | Makes stopping condition complete and auditable | Medium |
| 5 | **Run one replay-driven cycle:** top replay candidate → overlay → 100 trades → compare | Connects replay to live; tests best historical lever | Medium |

**Recommended immediate next steps:**  
Do **(1)** and **(2)** together: run the next 1–2 cycles with `FORCE_LEVER=exit`, and add alternation logic so that after an exit cycle we don’t immediately fall back to "entry forever." Then add **(3)** so that if we LOCK with no expectancy improvement, the next cycle tries the other lever or a stronger tweak.
