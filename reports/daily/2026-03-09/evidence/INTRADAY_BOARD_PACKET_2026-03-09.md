# INTRADAY BOARD PACKET — 2026-03-09

## Was there portfolio-level unrealized edge?

Yes (peak 50.8495 USD, drawdown to EOD 60.8833 USD).

## Why wasn't it captured?

exit eligibility lag (ELIGIBLE_BUT_LATE); reversal before eligibility (GREEN_REVERSAL); many trades never went green (52/174)

## Did displacement_blocked help or hurt?

Blocked count: 2000. Counterfactual PnL not computed (bars not used). Evidence inconclusive.

## What single change would have helped most?

Exit timing (capture at eligibility) for eligible-but-late and green-reversal trades. No tuning recommended from one day.

## What must NOT change?

Do not change exit thresholds or gating based on one day.
