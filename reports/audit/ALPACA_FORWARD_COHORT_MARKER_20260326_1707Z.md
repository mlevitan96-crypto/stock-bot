# ALPACA forward cohort marker (20260326_1707Z)

## Deploy / restart marker

- **DEPLOY_TS_UTC epoch:** `1774544849.0` (2026-03-26T17:07:29Z)
- **Git HEAD after reset:** `0b75150b46850618647f8e41f3e6c68226c1ce8a`
- Services restarted immediately after deploy (see `ALPACA_DEPLOY_20260326_1707Z.md`).

## Phase 2 observation (this run)

Certification script did **not** wait 60 minutes or until ≥10 entered + ≥10 economic closes.

**Measured immediately post-deploy:**

- Forward economic closes (`exit_attribution.jsonl`, exit_ts ≥ deploy): **0**
- Forward entered intents with canonical ids (parity audit): **0**

**forward_cohort_vacuous:** `True`

Therefore the post-deploy cohort is **not yet eligible** for Phase 3–4 “perfect chain” certification under the stated minimums.
