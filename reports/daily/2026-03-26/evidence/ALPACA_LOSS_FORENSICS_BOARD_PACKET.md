# Board Packet — Alpaca Loss Forensics

## Executive summary

- Window: last **2000** exits. Total PnL **-555.50 USD**.
- Today UTC vs baseline: see day_by_day.
- Join coverage: **67.5%**.

## Causal drivers

See CSA review.

## Recommended next experiments (SHADOW-ONLY)

- Shadow hold/exit grid on frozen CSV (no live changes).
- Blocked-trade counterfactual harness if not already run.

## Hard fixes (data/ops/logic)

- Raise entry-exit join rate (emitters, trade_id parity).
- Ensure protected logs never truncated.

## **DO NOT PROMOTE / DO NOT TUNE** until Truth Gate passes and fixes land.
