# Expectancy gate score contract fix — Plan review (multi-model BEFORE)

**Date:** 2026-02-18  
**Goal:** Restore profitable entries by enforcing a single score contract: expectancy gate evaluates the **same** composite score that passed the prior gate. No tuning sweeps, no disabling gates, no threshold guessing.

---

## Proposed change (minimal)

- **Contract:** `score_used_by_expectancy = composite_score` (post-composite), i.e. the cluster’s `composite_score` that already passed the composite/2.70 filter.
- **Implementation:** At the ExpectancyGate call site in `main.py`, set `composite_exec_score = c.get("composite_score", score)` and pass `composite_exec_score` into `ExpectancyGate.calculate_expectancy` and `ExpectancyGate.should_enter`; use it for `score_floor_breach=(composite_exec_score < Config.MIN_EXEC_SCORE)`.
- **No change:** Recompute logic, weighting, or thresholds. Variable rename only to make the contract explicit (`composite_exec_score`).

---

## Multi-model review

### Adversarial: How could this admit junk trades?

| Risk | Mitigation |
|------|------------|
| Cluster `composite_score` is inflated (e.g. 8.0) and we bypass the UW/survivorship downgrade that currently reduces `score` to ~2.8. | We are **not** removing the prior gate: clusters already passed the composite filter (2.70). The bug was using a **different** score (post–UW/survivorship) for the expectancy gate’s floor check, which made score_floor_breach true for everyone. Using the same composite that passed the prior gate restores the intended contract; MIN_EXEC_SCORE (3.0) still applies to that composite. |
| Lower composite scores (e.g. 3.1) now pass the floor and get traded; some may be marginal. | MIN_EXEC_SCORE=3.0 remains the floor for the **composite** score. We are not lowering the floor. If 3.0 is too low for profitability, that is a separate threshold decision (explicitly out of scope for this fix). |
| Expectancy formula still uses composite; if composite is “wrong” we amplify bad signals. | We are not changing the expectancy formula or inputs other than ensuring the **same** composite is used for both expectancy and floor. Ranking and expectancy semantics are preserved. |

**Verdict:** Risk of admitting junk is limited **if** the composite that passed the prior gate is the intended exec score. The fix removes a **contract violation** (two different scores), not a filter.

---

### Quant: Does this preserve ranking and expectancy?

| Question | Answer |
|----------|--------|
| Ranking | Clusters are already sorted by `composite_score`; we continue to use that same value for expectancy and floor. Order of evaluation unchanged. |
| Expectancy | `calculate_expectancy(composite_score=...)` now receives the cluster composite instead of the post-adjustment score. Expectancy was designed to work off the composite (see v3_2_features: base_ev = (composite_score / 5.0) - 0.5). Using the cluster composite is consistent. |
| score_floor_breach | Becomes `(composite_exec_score < MIN_EXEC_SCORE)`. So we still block composites below 3.0; we just use the **correct** composite value instead of the reduced one. |

**Verdict:** Ranking and expectancy semantics are preserved. The only change is which numeric value is used so it is consistent.

---

### Product: Is this interpretable and auditable?

| Question | Answer |
|----------|--------|
| Interpretable | Yes. “Expectancy gate uses the same composite score that passed the prior gate” is a one-line contract. Naming `composite_exec_score` at the call site makes it auditable. |
| Auditable | Yes. Logs (and optional EXPECTANCY_DEBUG) can show composite_exec_score vs MIN_EXEC_SCORE; no hidden second score. |
| Rollback | Trivial: revert the single change (use `score` again for the gate). No config or schema change. |

**Verdict:** Change is minimal, interpretable, and auditable.

---

## Go / no-go

- **Go.** Proceed with: (1) trace score flow and write score_trace.md, (2) implement the fix with composite_exec_score, (3) deploy and restart paper (no overlay), (4) collect unblock proof, (5) post-fix review. Do not tune thresholds in this change.
