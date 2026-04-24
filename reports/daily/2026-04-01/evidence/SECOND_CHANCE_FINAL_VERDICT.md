# SECOND_CHANCE_FINAL_VERDICT

## Did second-chance materially improve paper PnL?

**NO** (descriptive, joined subset). Allowed-row mean 60m variant A: **-0.968325** USD; baseline displacement_blocked mean 60m: **0.405592** USD. See `SECOND_CHANCE_PNL_EVALUATION.json`.

## Did it introduce new risk?

**NO** to live trading (no orders). **YES** if paper outcomes are misread as live edge — governance risk only; evidence: `paper_only` fields in JSONL + worker audit.

## Extended paper run or abandon?

**Proceed to extended paper run** (scheduled worker + accumulate JSONL) **if** governance wants more N; **do not** promote to live without a separate promotion review.

## Next single question before live consideration

**If second-chance `allowed` had been executed live, would realized fills match variant-A bars PnL after spreads, latency, and post-displacement book dynamics?** (Requires shadow fills or paper-account replay, not bars-only counterfactuals.)
