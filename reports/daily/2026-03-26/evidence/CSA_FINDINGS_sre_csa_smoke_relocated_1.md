# CSA Findings

**Mission ID:** sre_csa_smoke
**Generated (UTC):** 2026-03-05T18:01:43.879341+00:00
**Verdict:** HOLD (**MED** confidence)

## Assumption audit

- Board review and shadow data reflect current production behavior.
- Last-387 (or chosen cohort) is representative for promotion decisions.
- Telemetry and attribution paths are complete for in-scope exits.
- No unmeasured regime shift between review window and deploy.
- Board opportunity_cost / scenario logic is stable across runs.

## SRE anomaly interpretation

SRE status: ANOMALIES_DETECTED
Events in window: 3

- **Benign (no action):** sre_0d5949758bde
- **Silent failure (investigate):** sre_c3018e538d7d
- **PnL / risk / learning threat:** sre_234f68a292d5

**Assumption that may be breaking:** Rate or loss concentration suggests regime change or execution anomaly.

**Experiment or rollback to resolve:**

- Correlate with market hours and recent deploys; consider HOLD until explained.
- Verify exit_attribution and blocked_trades writers; check service health.

## Missing data

- Shadow comparison not provided; advance candidate may be unvalidated.
- Board review lacks exits_in_scope or opportunity_cost_ranked_reasons.

## Counterfactuals not tested

- Alternative time windows (7d, 14d) not compared in this run.
- Rollback impact (reverting B2/paper flags) not re-measured post-enable.
- Different exit-count cohorts (e.g. last750) not compared for stability.

## Value leakage scan

- Ensure board review uses only in-scope exits; no post-cutoff data.
- Shadow runs must not use post-decision execution data.

## Risk asymmetry

Default: downside (bad live paper / production impact) exceeds upside (marginal PnL gain) until proven in shadow and paper.

## Escalation triggers

- Verdict is HOLD, ESCALATE, or ROLLBACK and no CSA_RISK_ACCEPTANCE artifact exists.
- Confidence is LOW on a PROCEED verdict.
- Missing data list is non-empty and mission changes runtime behavior.
- Risk asymmetry note indicates unbounded downside.
- SRE reported anomalies; HIGH-confidence economic-impact events block PROCEED.

## Required next experiments (ranked)

1. Produce shadow comparison (build_shadow_comparison_last387) before any promotion.
2. Run parallel reviews (7d, 14d, 30d, last387) and compare nomination stability.
3. Run shadow comparison after every board review; gate enable on CSA + shadow.
4. Document rollback procedure and run rollback drill before enabling new flags.

## Recommendation

Do not promote until missing data is addressed or explicit CSA_RISK_ACCEPTANCE override is written.

## Override

Override allowed: **yes** (soft veto). To override HOLD/ESCALATE/ROLLBACK, create:

`reports/audit/CSA_RISK_ACCEPTANCE_sre_csa_smoke.md`

with required sections (verdict summary, why override, risk accepted, rollback plan, sign-off).
