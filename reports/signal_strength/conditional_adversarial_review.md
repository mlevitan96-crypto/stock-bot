# Conditional Adversarial Review (Phase 3)

**Mandate:** Challenge spurious correlations, identify stable vs fragile conditions, reject patterns that don’t persist across time. No weight changes.

---

## MODEL B — Challenge spurious correlations

- **Tertile / median splits are sample-dependent.** A “positive expectancy when uw=high” in this sample may flip in the next if boundaries shift. Require: (1) report tertile boundaries and n per cell; (2) re-run on a later window and check sign stability.
- **Small n:** Any slice or signal×condition cell with n < 10 should be marked “unstable”; do not treat as predictive. Flag in conditional_expectancy.md.
- **Selection bias:** Blocked trades are a selected set (score_below_min or expectancy_blocked). Expectancy in this set is not the same as expectancy of the universe. Conditional patterns here answer “when we block, in which conditions would the blocked trade have been good/bad?” not “when should we trade?”
- **Regime_macro is a proxy.** We do not have true “regime up/down/transition” in the data; we have strength of regime/macro components. Don’t overstate as “regime” in narrative.

---

## MODEL C — Stable vs fragile conditions

- **Stable:** Conditions that (1) have n ≥ 20 per cell, (2) show same sign of mean_pnl across overlapping slices (e.g. uw=high and regime_macro=mid), (3) are aligned with prior multi-model edge analysis (e.g. uw EDGE_POSITIVE).
- **Fragile:** (1) Only one slice shows positive expectancy; (2) adjacent slices flip sign (e.g. uw=low positive, uw=mid negative); (3) interaction cells with n < 10; (4) patterns that contradict unconditional delta_mean (e.g. signal is EDGE_NEGATIVE but “positive when X” with tiny n).

---

## MODEL D — Reject patterns that don’t persist across time

- **No out-of-sample check in this run.** To “reject patterns that don’t persist”: (1) run conditional expectancy on T1 (e.g. last 30 days), then T2 (next 30 days); (2) keep only signal×condition pairs where sign(mean_pnl) is the same in T1 and T2 and n is sufficient in both. This phase does not implement T2; recommend it as a follow-up.
- **Single-window result:** Treat all conditional findings as **hypotheses**. Verdict “EDGE IS CONDITIONAL” means “there exist signal×condition cells with positive expectancy in this window”; not “these will persist.”

---

## Synthesis of challenges

| Risk | Mitigation |
|------|------------|
| Spurious correlation | Report n and boundaries; require n ≥ 10 per cell for “positive” claim. |
| Unstable conditions | Prefer slices where multiple cells (e.g. uw high + regime mid/high) agree. |
| Non-persistence | Re-run on another time window; only then treat as stable. |
| Overstatement of “regime” | Label as “regime_macro strength” not “market regime.” |
