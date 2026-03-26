# INTRADAY BOARD VERDICT

**Date:** 2026-03-09

## Where was edge today?

Edge appeared in 27 trades that had positive unrealized PnL (MFE > 0). Many gave back (profit_giveback) or reversed; a minority closed as small winners.

## Why didn't we capture it?

Realized PnL: **-124.19 USD**. Majority of trades were losers; exit logic (signal_decay, flow_reversal) closed after drawdown. Green-then-red count: 4 (small dollar impact).

## What single change would have helped most?

No single change from one day. Evidence: exit timing (green-then-red) cost ~0.30 USD; bulk of loss was from trades that never went green (MFE=0). Earlier exits would not have turned the day profitable.

## What should NOT be changed based on one day?

Do not relax signal_decay thresholds or max_positions based on 2026-03-09 alone. Do not attribute loss primarily to exit timing; entry/symbol selection and regime dominated.
