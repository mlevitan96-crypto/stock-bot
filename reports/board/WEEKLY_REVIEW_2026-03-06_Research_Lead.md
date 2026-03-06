# Weekly Review — Research Lead
**Date:** 2026-03-06

## 3 strongest findings
1. 7d primary window; 14d/30d sanity checks noted in mission but require ledger extension (multiple --days or cohorts).
2. Board review (last387) and shadow comparison define cohort; stability across 7d vs 30d is not yet computed in this pipeline.
3. Counterfactuals not tested (from CSA) and missing_data list define next experiments.

## 3 biggest risks
1. Cohort instability (different symbol mix or regime across 7d vs 30d) invalidating comparisons.
2. Missing baselines (do-nothing, buy-and-hold, time-window counterfactuals).
3. Experiment design not answerable (e.g. no clear success criteria or sample size).

## 3 recommended actions (ranked)
1. Add 14d and 30d ledger summaries to weekly run; report nomination stability (e.g. same top shadow across windows).
2. Define one do-nothing or buy-hold baseline and add to board comparison.
3. For each required_next_experiment, add success criteria and minimum N.

## What evidence would change my mind?
Stable nomination across 7d/14d/30d; a documented baseline; and success criteria for each experiment.
