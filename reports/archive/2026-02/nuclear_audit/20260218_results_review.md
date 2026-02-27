# Nuclear audit — Results review (multi-model AFTER)

**Date:** 2026-02-18  
**Purpose:** Challenge conclusions and propose the smallest corrective action after audit results.  
**Artifacts:** `reports/nuclear_audit/20260218/` (00_summary.md … 09_verdict.md).

---

## Audit result (from 09_verdict.md)

- **Verdict:** PASS  
- **Why no open trades:** Candidates exist but selected_count=0 (gates blocking; see gate_counts).  
- **Evidence:** 05_entry_pipeline_evidence.md shows 51 candidates considered per cycle, 0 orders; aggregated gate_counts: **expectancy_blocked:score_floor_breach** = 734 (all blocks).

---

## Multi-model challenge to conclusions

### Adversarial

| Conclusion | Challenge |
|------------|-----------|
| “PASS” because we have a “clear gating reason” | The reason is clear but **wrong for product**: every candidate is blocked by the same gate. So either (a) the expectancy gate is misconfigured (score floor too high vs composite threshold), or (b) the composite score passed to the expectancy gate is not the same as the one used for “ACCEPTED” (2.70). PASS = “system not broken”; it does **not** mean “no action needed.” |
| Entries pipeline is “functioning” | It functions only up to the expectancy gate; after that it consistently rejects. So “functioning” is technically true; “allowing entries” is false until the gate is fixed or relaxed. |

**Verdict:** Do not treat PASS as “no follow-up.” The single corrective action (expectancy gate / score_floor_breach) is necessary.

---

### Quant

| Conclusion | Challenge |
|------------|-----------|
| candidate_count = 51, selected_count = 0 | Statistically, 100% rejection by one gate. No variance; this is a **deterministic** block, not noise. |
| MIN_EXEC_SCORE: 3.0 vs composite threshold 2.70 | If the expectancy gate uses MIN_EXEC_SCORE (3.0) as the floor and the score passed in is the composite (e.g. 8.80), score_floor_breach should not fire. So either (1) the score passed to ExpectancyGate is a different (lower) score, or (2) the gate compares against a different floor. Code inspection of `ExpectancyGate.should_enter` and call site is required. |

**Verdict:** Smallest corrective action is **code-level**: locate where `score_floor_breach` is set and align the floor with the composite threshold (or document why 3.0 is required at that stage).

---

### Product

| Conclusion | Challenge |
|------------|-----------|
| “Exact next actions” in 09_verdict | The updated verdict now points to ExpectancyGate + score_floor_breach and 03_config_and_env.md. That is the **smallest** corrective action: one code path (expectancy gate), one config (MIN_EXEC_SCORE vs 2.70), no tuning of strategy parameters elsewhere. |
| Re-run audit after fixes | Correct. After changing the gate or config, re-run `scripts/run_nuclear_audit_on_droplet.py` and confirm gate_counts show orders &gt; 0 or a different, acceptable rejection mix. |

**Verdict:** Adopt the exact next actions in 09_verdict.md. Do **not** start tuning other levers (e.g. exit weights, displacement) until entries are unblocked and audit shows selected_count &gt; 0 or an intentional cap.

---

## Smallest corrective action (synthesis)

1. **Inspect** `ExpectancyGate.should_enter` and the condition that sets `score_floor_breach` (main.py or v32 expectancy gate).  
2. **Align** the score used at that check with the composite score that already passed the 2.70 gate, **or** raise the composite threshold to 3.0 if product intent is to use 3.0 at entry.  
3. **Confirm** MIN_EXEC_SCORE=3.0 in 03_config_and_env.md is intentional for that stage.  
4. **Re-run** nuclear audit after change; require either selected_count &gt; 0 or a documented, intentional gate (e.g. market closed, cap reached).

---

## Proof file sections (for next actions)

| Action | Section |
|--------|--------|
| Expectancy gate / score_floor_breach | 05_entry_pipeline_evidence.md (gate_counts, cycle_summary) |
| MIN_EXEC_SCORE vs composite threshold | 03_config_and_env.md |
| Runtime / state | 01_runtime_health.md |
| Re-run audit | 00_summary.md, 09_verdict.md |
