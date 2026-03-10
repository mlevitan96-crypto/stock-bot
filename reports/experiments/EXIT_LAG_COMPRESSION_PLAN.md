# Exit-Lag Compression Experiment — Plan

**Authority:** CSA + SRE. **Mode:** PAPER TRADING ONLY. **Governance:** Strict; no live exit logic changes.

---

## Phase 0 — Safety & Isolation (SRE)

### Enforced guardrails

- **No live exit logic changes.** All variants are evaluated in shadow only; no code path may modify production exit behavior.
- **No config promotion.** Experiment outputs do not auto-promote to config; any future paper A/B requires explicit CSA + board approval.
- **Shadow-only evaluation.** Replay uses `exit_decision_trace` + attribution; no orders are sent; no write path touches production exits.
- **Explicit paper guardrails.** Any future limited paper A/B must be gated by CSA verdict and board packet; paper mode is explicitly enforced in config.

### Fail closed if

- Any live behavior would change as a result of this experiment.
- Any write path touches production exit logic or production config.

### Data source

- **Droplet only.** Trace and attribution are read from droplet; replay runs on droplet. Local runs are non-authoritative.

---

## Phase 1 — Exit-Lag Compression Candidates

Based on forensic results (eligibility-to-exit lag distribution, first-firing condition, shadow exit-on-first-eligibility delta).

---

### Variant A: Exit on first eligibility (baseline shadow)

- **Description:** Exit at the first trace sample where `exit_eligible` or any exit condition (signal_decay, flow_reversal, stale_alpha, risk_stop) is true.
- **Rationale:** Already proven in shadow; +$115.78 delta vs current realized on 2026-03-09; median lag 7.88 min suggests material leakage.
- **Expected benefit:** Capture unrealized PnL at eligibility; reduce giveback.
- **Expected risk:** Possible whipsaw if eligibility is noisy; premature exit in choppy regimes.

---

### Variant B: Exit if eligibility persists ≥ X minutes

- **Description:** Exit at `first_eligibility_ts + X` minutes (X ∈ {2, 5, 10}), using unrealized PnL at that time from trace.
- **Rationale:** Reduces noise exits; only exit once eligibility has persisted, trading off some giveback for stability.
- **Expected benefit:** Fewer whipsaw exits; more confidence that exit signal is stable.
- **Expected risk:** Additional lag (X min) may increase giveback vs Variant A; longer exposure to reversal.

---

### Variant C: Partial exit (50%) on first eligibility, remainder per current logic

- **Description:** Simulate 50% of position closed at first eligibility (PnL = 0.5 × unrealized_at_first_eligibility) and 50% at actual exit (PnL = 0.5 × realized).
- **Rationale:** Compromise between capturing profit and retaining upside; reduces impact of wrong-way early exit.
- **Expected benefit:** Smoother PnL profile; lower tail if first-eligibility exit is sometimes wrong.
- **Expected risk:** More complex to operate; two exit events; may still lag on the remainder.

---

### Variant D: Flow-reversal–only early exit

- **Description:** Apply “exit at first eligibility” only when `first_firing_condition == "flow_reversal"`; all other trades use current (actual) realized PnL.
- **Rationale:** Forensic showed flow_reversal as dominant first-firing condition; signal_decay/risk_stop may be noisier; test whether early exit on flow_reversal alone improves expectancy without amplifying other exits.
- **Expected benefit:** Target the condition most associated with reversal; avoid early exit on decay/stop noise.
- **Expected risk:** Miss capture when risk_stop or signal_decay fires first and was correct; possible selection bias.

---

## Summary table

| Variant | Rationale | Benefit | Risk |
|--------|-----------|---------|------|
| A | First eligibility = baseline shadow | Max capture at eligibility | Whipsaw, premature exit |
| B (2,5,10 min) | Eligibility persistence | Fewer noise exits | Extra lag, giveback |
| C | 50% at eligibility, 50% actual | Compromise, lower tail | Complexity, remainder lag |
| D | Flow-reversal only | Target reversal-driven exits | Miss other valid early exits |

---

## Output artifacts (mandatory)

- `reports/experiments/EXIT_LAG_SHADOW_RESULTS_<YYYY-MM-DD>.json`
- `reports/experiments/EXIT_LAG_RISK_IMPACT_<YYYY-MM-DD>.md`
- `reports/board/EXIT_LAG_BOARD_PACKET_<YYYY-MM-DD>.md`
- `reports/audit/CSA_EXIT_LAG_VERDICT_<YYYY-MM-DD>.json`

**Exit criteria:** Shadow variants evaluated; risk impact documented; CSA verdict issued; board packet complete.
