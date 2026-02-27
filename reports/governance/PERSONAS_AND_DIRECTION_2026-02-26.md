# Personas, multi-model alignment, and direction check

**Date:** 2026-02-26  
**Context:** Governance loop live with alternation, no-progress, giveback, 100-trade gate, and multi-cycle replay jump. Expectancy still negative (~-0.11). Trading active (2400+ attributions, 1800+ today).

---

## 1. Are we still moving in the right direction?

**Yes.** The strategy in the strategic review and Five Ideas is being executed:

| Persona / doc | Guidance | Current state |
|---------------|----------|----------------|
| **Adversarial** | Don’t add new pipelines before fixing blame; one effectiveness → entry vs exit | We have blame; one lever at a time; no new discovery pipelines added. |
| **Quant** | Blame baseline, gate on trade count, weak_entry vs exit_timing | 100-trade gate; recommender uses blame; alternation + no-progress force exit when stuck. |
| **Product** | One canonical baseline, one lever → 50-trade (we use 100) → LOCK/REVERT | Baseline dir fixed; one overlay per cycle; LOCK/REVERT on 100 trades. |
| **Execution/SRE** | Join integrity, expectancy gate | Join working (2500+ joined); loop runs on droplet. |
| **Risk** | Optional brake (raise MIN_EXEC_SCORE or pause); don’t rely on UW for profit yet | UW not in loop; brake is optional and documented. |

**Five Ideas:** All five are implemented (force exit / alternation, giveback, no-progress, replay-driven cycle, and now multi-cycle stagnation → replay jump).

So: **no course change.** The loop is the right structure; we keep running it and let it explore entry vs exit and, on stagnation, replay.

---

## 2. Other ideas worth pursuing (from strategic review Section 4 + personas)

**High value, low effort**

- **Stopping checks visibility**  
  Ensure `stopping_checks` in `lock_or_revert_decision.json` are always populated (expectancy_gt_0, win_rate_ge_baseline_plus_2pp, giveback_le_baseline_plus_005, joined_count_ge_100). They depend on baseline/candidate giveback; verify giveback is present in effectiveness_aggregates on the droplet so we see how close we are to the stop.

**Medium value**

- **Tighten as a lever**  
  Quant/Risk: “Raise MIN_EXEC_SCORE (e.g. 3.0) so only strongest signals trade.” Add an **entry lever variant** in the loop: e.g. MIN_EXEC_SCORE 2.7 vs 2.9 vs 3.0. Recommender or replay could choose strength, not just “entry vs exit.”  
- **Regime filter (later)**  
  Use structural_intelligence (regime, market_context_v2) to reduce size or disable in clearly adverse regimes. Reduces drawdown; entry/exit fix still needed for positive expectancy in normal regimes.  
- **Symbol/sector filter (later)**  
  If signal_effectiveness or blame shows certain symbols/sectors lose more, exclude or down-weight until baseline is positive.

**Defer**

- **UW as profit lever**  
  Keep UW as overlay/filter after equity baseline is profitable; bar-based forward returns and UW-conditioned policies come after.  
- **More discovery pipelines**  
  Don’t add new ones; use existing win-finding/edge as research and feed candidates into the same 100-trade governance loop.

---

## 3. Do we adjust?

**Direction: no.** Stay with: blame → one lever at a time → 100-trade gate → LOCK/REVERT → alternation + no-progress + replay on stagnation.

**Tactical adjustments (optional)**

1. **Populate stopping_checks**  
   Confirm giveback is in baseline/candidate aggregates so `compare_effectiveness_runs` always writes the four stopping_checks. No loop change.

2. **Entry strength as a lever**  
   Allow overlay to specify MIN_EXEC_SCORE (e.g. 2.7, 2.9, 3.0) so the loop can “tighten first” without a separate workflow. Recommender or replay could propose the value.

3. **Optional risk brake**  
   Document: “If drawdown is unacceptable, manually raise MIN_EXEC_SCORE or pause new entries until next lever is applied.” No code change; runbook only.

4. **Replay every N cycles (optional)**  
   Today we only run replay on stagnation. Could also run a replay campaign every N cycles and inject top candidate as one cycle (in addition to stagnation). Lower priority.

---

## 4. Summary

- **Direction:** Correct. Personas and multi-model ideas are aligned and implemented.  
- **New ideas:** Mainly stopping_checks visibility, then entry-strength lever and (later) regime/symbol filters.  
- **Adjustment:** No strategic change. Optional tactics: ensure stopping_checks are filled, add MIN_EXEC_SCORE as an entry-lever variant, document risk brake, optionally replay every N cycles.
