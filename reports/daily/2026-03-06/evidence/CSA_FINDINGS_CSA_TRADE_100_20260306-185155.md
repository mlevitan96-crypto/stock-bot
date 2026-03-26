# CSA Findings

**Mission ID:** CSA_TRADE_100_20260306-185155
**Generated (UTC):** 2026-03-06T18:51:55.803831+00:00
**Verdict:** HOLD (**MED** confidence)

## Assumption audit

- Board review and shadow data reflect current production behavior.
- Last-387 (or chosen cohort) is representative for promotion decisions.
- Telemetry and attribution paths are complete for in-scope exits.
- No unmeasured regime shift between review window and deploy.
- Shadow comparison ranking (proxy_pnl_delta) is sufficient for advance decisions.
- Board opportunity_cost / scenario logic is stable across runs.

## SRE anomaly interpretation

SRE status: ANOMALIES_DETECTED
Events in window: 3

- **Benign (no action):** sre_b3a3bc3c22dc
- **Silent failure (investigate):** sre_2bbcf8caceac
- **PnL / risk / learning threat:** sre_14d8b08ec131

**Assumption that may be breaking:** Rate or loss concentration suggests regime change or execution anomaly.

**Experiment or rollback to resolve:**

- Correlate with market hours and recent deploys; consider HOLD until explained.
- Verify exit_attribution and blocked_trades writers; check service health.

## Missing data

- Board review lacks exits_in_scope or opportunity_cost_ranked_reasons.

## Counterfactuals not tested

- Alternative time windows (7d, 14d) not compared in this run.
- Rollback impact (reverting B2/paper flags) not re-measured post-enable.
- Different exit-count cohorts (e.g. last750) not compared for stability.
- Shadow advance: live paper outcome vs shadow proxy not yet observed.

## Value leakage scan

- Ensure board review uses only in-scope exits; no post-cutoff data.
- Shadow runs must not use post-decision execution data.

## Risk asymmetry

Asymmetry: advancing a shadow has unbounded downside (live paper loss); holding has bounded opportunity cost. Rollback cost non-zero.

## Escalation triggers

- Verdict is HOLD, ESCALATE, or ROLLBACK and no CSA_RISK_ACCEPTANCE artifact exists.
- Confidence is LOW on a PROCEED verdict.
- Missing data list is non-empty and mission changes runtime behavior.
- Risk asymmetry note indicates unbounded downside.
- SRE reported anomalies; HIGH-confidence economic-impact events block PROCEED.
## Automation Evidence

Cursor Automations governance layer (pre-merge/pre-deploy) outputs ingested as first-class evidence.

- **Governance integrity status:** ok
- **Last run (UTC):** 2026-03-05T21:07:05.107788+00:00
- **Anomalies:** (none)

- **Open automation-related issues:** Open issues from Security Review or Governance Integrity are not loaded in this script; check GitHub for labels automation-anomaly, security-review.


## Required next experiments (ranked)

1. Run parallel reviews (7d, 14d, 30d, last387) and compare nomination stability.
2. Run shadow comparison after every board review; gate enable on CSA + shadow.
3. Document rollback procedure and run rollback drill before enabling new flags.

## Recommendation

Do not promote until missing data is addressed or explicit CSA_RISK_ACCEPTANCE override is written.

## Override

Override allowed: **yes** (soft veto). To override HOLD/ESCALATE/ROLLBACK, create:

`reports/audit/CSA_RISK_ACCEPTANCE_CSA_TRADE_100_20260306-185155.md`

with required sections (verdict summary, why override, risk accepted, rollback plan, sign-off).
