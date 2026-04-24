# ALPACA DEEP ROOT CAUSE + FIX PLAN (Stage 2)

- UTC `20260330_181609Z`

## Root causes of apparent inactivity

1. **Risk freeze (`max_drawdown_exceeded`)** — When active (see `run.jsonl` / `freeze.jsonl`), **new entries** are suppressed early in `run_once`. This explains **no new trades** independent of exit math.
2. **Position cap** — **32/32** slots full; rotation requires exits or displacement.
3. **Exit math not satisfied** — At capture: no stop/trail/profit hit; stale timers not elapsed; **v2 exit score** well below 0.80; structural exits not asserting.
4. **Metadata** — Widespread **entry_score==0** and missing **v2** blocks **disable decay exits** and **mute v2 deterioration vs entry**.

## Operator fix plan (advisory — no code changes in this task)

- Reconcile **peak_equity** vs live account equity if drawdown freeze is false positive.
- Backfill **position_metadata** (`entry_score`, `v2`, `entry_reason`, regime) on open.
- If faster rotation desired: review **stale windows**, **v2 0.80 bar**, and **capacity** policy.
- Confirm **evaluate_exits** in journal/worker_debug aligns with expected cadence.
