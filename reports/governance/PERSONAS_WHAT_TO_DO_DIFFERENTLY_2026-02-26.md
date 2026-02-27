# Personas: What to do differently?

**Date:** 2026-02-26  
**Context:** Loop is live (100-trade gate, alternation, no-progress, entry strength 2.7/2.9, stopping_checks, replay on stagnation). Expectancy still negative; REVERTs common; giveback still null in aggregates.

---

## Adversarial

**Mostly aligned.** We have blame, one lever at a time, no new pipelines.

**Do differently:**  
- **Expectancy gate / score ledger:** The doc called out “Expectancy gate is blocking heavily; ledger shows low scores (0.17–1.05) vs MIN_EXEC_SCORE (2.5). If the *only* trades getting through are marginal, we may be selecting for bad expectancy by construction.” We have **not** investigated that.  
- **Recommendation:** Run a **one-time diagnostic**: compare scores in the ledger (or attribution) at entry vs MIN_EXEC_SCORE; check whether the universe is mostly marginal and whether that could explain flat/negative expectancy. Don’t change the loop; add evidence so we’re not “selecting for bad expectancy by construction.”

---

## Quant

**Aligned** on blame, gate, weak_entry vs exit_timing, alternation.

**Do differently (optional):**  
1. **WTD vs 30D:** Use “WTD vs 30D entry_exit_intelligence” to justify a **risk brake** (e.g. “this week worse → tighten to 3.0 or pause”). Right now we don’t run WTD effectiveness or compare it to 30D in the loop. Optional: run WTD effectiveness periodically; if WTD is clearly worse than 30D, document or temporarily raise MIN_EXEC_SCORE.  
2. **Entry lever variety:** Phase B1 says “down-weight the **single worst** signal (from signal_effectiveness) or slightly raise MIN_EXEC_SCORE.” We only do the latter. Quant could say: add **down-weight worst signal** as an entry-lever option (e.g. from recommendation’s top5_harmful), so we can test “fewer bad-signal trades” vs “higher threshold” separately.

---

## Product / Operator

**Aligned:** One baseline, one lever per cycle, LOCK/REVERT, no fragmentation.

**Do differently:**  
- **Gate length:** Doc said “≥50 closed trades”; we use 100. Product could go either way: “100 is better evidence” (no change) or “50 would cycle faster and learn quicker.” So either **keep 100** or **consider 50** for faster iteration. No strong “must change” from this persona.

---

## Execution / SRE

**Aligned** on join integrity and loop running on droplet.

**Do differently:**  
- **Expectancy gate / score truth:** “Investigate why scores in ledger are so low (0.17–1.05) vs MIN_EXEC_SCORE (e.g. 2.5). If scores are pre-adjust and post-adjust is higher, ensure gate truth and dashboard reflect the same logic.” We have **not** done this.  
- **Recommendation:** Same as Adversarial: **one-time investigation** — scores at entry (ledger/dashboard/attribution), pre vs post adjust, and whether gate/dashboard are consistent. Fix any mismatch; then either “universe is low-score” (gate vs pipeline) or “reporting bug” (fix it).

---

## Risk

**Aligned:** UW not in loop; brake is documented.

**Do differently:**  
- **Use the brake when it hurts:** If drawdown is actually painful, **apply** the brake (e.g. MIN_EXEC_SCORE 3.0 or pause) for a cycle or two and document it, instead of only having it in the runbook. So: “do differently” only if current drawdown is unacceptable — then actually tighten or pause and log the decision.

---

## Summary: concrete “do differently” by persona

| Persona   | Do differently (concrete) |
|-----------|----------------------------|
| Adversarial | **Investigate expectancy gate / score ledger:** Are we only trading marginal scores? One-time diagnostic (ledger/attribution scores vs MIN_EXEC_SCORE). |
| Quant      | (1) **Optional:** WTD vs 30D effectiveness to justify risk brake. (2) **Optional:** Add “down-weight worst signal” as an entry lever variant. |
| Product   | No must-change. Option: consider 50-trade gate for faster cycles. |
| Execution/SRE | **Same as Adversarial:** Investigate score ledger vs MIN_EXEC_SCORE; ensure gate truth and dashboard align. |
| Risk      | **If drawdown is unacceptable:** Actually apply brake (e.g. 3.0 or pause) and document; don’t only document it. |

**Highest overlap:** Adversarial and Execution/SRE both want the **score / expectancy-gate diagnostic** so we’re not selecting for bad expectancy by construction. That’s the one “do differently” that multiple personas would call for today.
