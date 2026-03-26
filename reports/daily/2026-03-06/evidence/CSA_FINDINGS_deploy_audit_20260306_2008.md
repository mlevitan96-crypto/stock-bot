# CSA Findings

**Mission ID:** deploy_audit_20260306_2008
**Generated (UTC):** 2026-03-06T20:08:29.941200+00:00
**Verdict:** HOLD (**LOW** confidence)

## Assumption audit

- Board review and shadow data reflect current production behavior.
- Last-387 (or chosen cohort) is representative for promotion decisions.
- Telemetry and attribution paths are complete for in-scope exits.
- No unmeasured regime shift between review window and deploy.

## SRE anomaly interpretation

SRE status: OK
Events in window: 0

- **Benign (no action):** (none)
- **Silent failure (investigate):** (none)
- **PnL / risk / learning threat:** (none)

**Assumption that may be breaking:** (none inferred)

**Experiment or rollback to resolve:**

- No SRE events or all benign.

## Missing data

- Board review JSON not provided; cannot validate scenario alignment.
- Shadow comparison not provided; advance candidate may be unvalidated.

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
## Automation Evidence

Cursor Automations governance layer (pre-merge/pre-deploy) outputs ingested as first-class evidence.

- **Governance integrity status:** ok
- **Last run (UTC):** 2026-03-05T23:59:46.034046+00:00
- **Anomalies:** (none)

- **Open automation-related issues:** Open issues from Security Review or Governance Integrity are not loaded in this script; check GitHub for labels automation-anomaly, security-review.


## Required next experiments (ranked)

1. Produce shadow comparison (build_shadow_comparison_last387) before any promotion.
2. Run parallel reviews (7d, 14d, 30d, last387) and compare nomination stability.
3. Run shadow comparison after every board review; gate enable on CSA + shadow.
4. Document rollback procedure and run rollback drill before enabling new flags.

## Recommendation

Do not promote until missing data is addressed or explicit CSA_RISK_ACCEPTANCE override is written.

## Override

Override allowed: **yes** (soft veto). To override HOLD/ESCALATE/ROLLBACK, create:

`reports/audit/CSA_RISK_ACCEPTANCE_deploy_audit_20260306_2008.md`

with required sections (verdict summary, why override, risk accepted, rollback plan, sign-off).
