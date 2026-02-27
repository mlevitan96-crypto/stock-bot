# Expectancy gate fix — Post-fix review (multi-model)

**Date:** 2026-02-18  
**Purpose:** After unblock proof, challenge conclusions and note any unintended side effects. Do not tune thresholds.

---

## Questions

1. **Did we restore flow without admitting junk?**  
   - Check: expectancy_pass_count > 0, orders submitted; no obvious low-score (e.g. < 3.0) entries if MIN_EXEC_SCORE is 3.0.

2. **Is the floor appropriate?**  
   - We did not change MIN_EXEC_SCORE. Floor remains 3.0 for the composite. If too many marginal trades appear in a later window, that is a separate threshold decision.

3. **Any unintended side effects?**  
   - Expectancy formula now receives cluster composite; ranking unchanged. If blocked_trades or attribution show anomalies, note here.

---

## Multi-model (fill after unblock proof)

| Lens | Note |
|------|------|
| **Adversarial** | Unblock proof window had 0 candidates per cycle (considered=0), so we did not observe post-fix behavior with candidates. Risk: if cluster composite_score is missing or wrong on some code path, we could still pass bad scores to the gate. Mitigation: contract is explicit (composite_exec_score = c.get("composite_score", score)); audit when considered > 0. |
| **Quant** | Score distribution: nuclear audit shows candidate_count=33 in last non-zero cycle; aggregated gate_counts still include score_floor_breach (495) and score_below_min (277). Those counts span pre- and post-restart log; floor (3.0) unchanged. No threshold tuning done. |
| **Product** | Interpretable: one score (composite_exec_score) used for both expectancy and floor check. Auditable: EXPECTANCY_DEBUG=1 logs score_used_by_expectancy, floor, decision. Deploy verified fix present on droplet (grep composite_exec_score). |

---

## Verdict

- [ ] Flow restored; score_floor_breach no longer ~100%. (Inconclusive: proof window had no candidates; re-check when considered > 0.)
- [x] No junk flood observed.
- [x] Threshold tuning explicitly deferred.
