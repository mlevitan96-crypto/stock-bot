# Adversarial synthesis — score autopsy (droplet evidence)

Every claim cites droplet file path + stat.

---

## 1) Prosecution

**Claim:** The composite score is collapsed by the **post-composite adjustment chain** (signal_quality → uw → survivorship) before it reaches the expectancy gate, not by component regression or unit mismatch.

**Evidence:**
- `reports/decision_ledger/decision_ledger.jsonl`: 3037 events; **score_final** min=0.170, max=1.039, mean=0.211 (droplet).
- Pre-adjustment **signal_raw.score** (cluster composite) median=3.871 (same ledger).
- Drop ≈ 3.7 points between cluster and gate input.
- `logs/signal_quality_adjustments.jsonl`, `logs/uw_entry_adjustments.jsonl`, `logs/survivorship_entry_adjustments.jsonl` each have 2000 recent rows (droplet) — adjustment chain is active.

---

## 2) Defense

**Claim:** Unit/scale mismatch and “threshold too high” are ruled out; historical executed trades used the same threshold and scale.

**Evidence:**
- `logs/attribution.jsonl`: 1110 executed trades with **entry_score**; all 1110 ≥ MIN_EXEC_SCORE (2.5); min=3.019, max=8.800, mean=5.084 (droplet).
- MIN_EXEC_SCORE=2.5 from config (same scale as composite score).
- So MIN_EXEC_SCORE is **not** mis-scaled vs historical executed trades.

---

## 3) SRE/Operations

**Claim:** No pipeline bug or silent drop; bars alignment not yet proven as cause of the adjustment deltas.

**Evidence:**
- Every blocked event has explicit gate_name + reason + measured (decision_ledger).
- Score path: cluster composite_score → apply_signal_quality_to_score → apply_uw_to_score → apply_survivorship_to_score → composite_exec_score → expectancy gate. No missing step.
- Bars timestamp/lookback: not yet audited on droplet for 20 blocked examples; adjustment logs show score_before/score_after and would reveal if raw_signal or context is wrong.

---

## 4) Board verdict

- **Dominant cause:** Composite score is reduced by **~3.7 points** between cluster output (median 3.87) and expectancy gate input (median 0.17) by the **adjustment chain** (signal_quality, uw, survivorship). Which of the three dominates requires inspecting the three adjustment logs on the droplet (score_before/score_after per step).
- **MIN_EXEC_SCORE:** Correct scale; executed trades historically above 2.5.
- **Bars alignment:** Not ruled in/out; minimal next step is to sample 20 blocked events, resolve bars used in scoring, and check timestamps/lookbacks for those symbols.
