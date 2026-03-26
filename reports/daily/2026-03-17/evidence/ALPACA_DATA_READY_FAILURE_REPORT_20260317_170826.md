# Alpaca DATA_READY failure report

- **Timestamp:** 20260317_170826
- **Attempts:** 1
- **Blocker file:** `C:\Dev\stock-bot\reports\audit\ALPACA_JOIN_INTEGRITY_BLOCKER_20260317_170826.md`
- **Classification:** SAMPLE_SIZE

## Evidence (blocker preview)

```
# Alpaca data readiness blocker — SAMPLE_SIZE

- **What failed:** Sample size below threshold (min_trades=200, min_final_exits=200).
- **Counts:** trades_total=36, required_trades=200, required_final_exits=200.

## Classification

**SAMPLE_SIZE** — wait for more trades (no code change).

```

## Resolution

Wait for more trades. No code change.
