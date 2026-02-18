# Expectancy gate fix — Unblock proof (short window)

**Purpose:** After deploy + restart, observe 5–10 cycles and confirm entries are unblocked.

---

## How to collect

1. **On droplet** (or via DropletClient): tail gate and run logs.
2. **Option A:** Run nuclear audit after 10–15 min: `python scripts/run_nuclear_audit_on_droplet.py` and use `reports/nuclear_audit/<date>/05_entry_pipeline_evidence.md` for gate_counts and cycle_summary.
3. **Option B:** On droplet: `tail -n 500 logs/gate.jsonl` and parse for `cycle_summary` (considered, orders) and `expectancy_blocked` (reason=score_floor_breach vs expectancy_passed).

---

## Metrics to record

| Metric | Source | Before fix (from nuclear audit) | After fix (fill) |
|--------|--------|---------------------------------|------------------|
| candidate_count (considered) | cycle_summary | 51 | |
| expectancy_pass_count | gate events / cycle_summary | 0 | |
| orders_submitted_count | cycle_summary.orders | 0 | |
| score_floor_breach % of blocks | gate_counts | ~100% | |
| gate_counts (top) | gate.jsonl | expectancy_blocked:score_floor_breach 734 | |

---

## PASS criteria

- expectancy_pass_count > 0
- score_floor_breach no longer ~100% of expectancy blocks
- No explosion in low-score trades (optional: spot-check composite_exec_score in logs if EXPECTANCY_DEBUG=1 was used)

---

## Placeholder (fill after observation)

```
Date: ___________
Cycles observed: ___________
candidate_count (last cycle): ___________
expectancy_pass_count (approx): ___________
orders_submitted_count (last 5–10 cycle_summary): ___________
gate_counts (top): ___________
PASS / FAIL: ___________
```
