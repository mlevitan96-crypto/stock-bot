# Alpaca live-forward poll (non-vacuous cohort)

**TS:** `20260326_2315Z`

## Implementation

`scripts/audit/alpaca_forward_poll_droplet.py` — SSH to Alpaca droplet, rerun `forward_parity_audit.py` on an interval until:

- `forward_economic_closes >= --min-closes` and `forward_trade_intents_with_ct_and_tk >= --min-intents`, or
- optional `--success-on-non-vacuous-only` (exit when audit exit code ≠ 2),

or `--max-wait-min` elapses.

## Proof this run

**Not executed** in this session (no long-running SSH poll captured). The script is the **deliverable** for Phase 6 operational use.

## Certification label

**LIVE_FORWARD_PENDING** for Alpaca until a poll run produces a non-vacuous forward cohort and downstream trace/parity artifacts.
