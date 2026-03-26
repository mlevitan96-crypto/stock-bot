# CSA Findings

**Mission ID:** csa_smoke
**Generated (UTC):** 2026-03-05T17:17:28.847472+00:00
**Verdict:** PROCEED (**MED** confidence)

## Assumption audit

- Board review and shadow data reflect current production behavior.
- Last-387 (or chosen cohort) is representative for promotion decisions.
- Telemetry and attribution paths are complete for in-scope exits.
- No unmeasured regime shift between review window and deploy.
- Shadow comparison ranking (proxy_pnl_delta) is sufficient for advance decisions.
- Board opportunity_cost / scenario logic is stable across runs.

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

## Required next experiments (ranked)

1. Run parallel reviews (7d, 14d, 30d, last387) and compare nomination stability.
2. Run shadow comparison after every board review; gate enable on CSA + shadow.
3. Document rollback procedure and run rollback drill before enabling new flags.

## Recommendation

CSA does not block. Proceed only if other gates pass; prefer HIGH confidence.

## Override

Override allowed: **yes** (soft veto). To override HOLD/ESCALATE/ROLLBACK, create:

`reports/audit/CSA_RISK_ACCEPTANCE_csa_smoke.md`

with required sections (verdict summary, why override, risk accepted, rollback plan, sign-off).
