# SECOND_CHANCE_POLICY_SPEC

**Classification:** Temporal policy (paper-only). **Not** a signal, threshold, exit, or sizing change.

## Trigger

When the live engine blocks an entry with `displacement_blocked` (displacement policy denied swap despite a displacement candidate).

## Recorded state

- Original entry intent: symbol, direction, composite score and components, decision timestamp, displaced incumbent symbol, policy reason, effective min-exec at block time.

## Schedule

- Exactly **one** re-evaluation after `DELAY_SECONDS` (default **60**, env `PAPER_SECOND_CHANCE_DELAY_SECONDS`).

## Re-evaluation admission (paper)

At re-evaluation time, a **hypothetical** re-entry is marked **allowed** only if:

1. **A — Intent validity:** Original score still meets the **stricter** of (a) effective min-exec at block time and (b) current `MIN_EXEC_SCORE` (threshold drift fail-closed).
2. **B — No duplicate:** Challenger symbol not already an open position.
3. **C — Capacity / displacement:** Either portfolio has a free slot (`n < MAX_CONCURRENT_POSITIONS`), **or** the original incumbent is still held and `evaluate_displacement` now returns **allowed** under current config (same policy code as live; read-only broker + local metadata).

If any check fails, outcome is **blocked** with an explicit `reeval_block_reason`. **No second retry.**

## Live trading

- **No orders** are placed by this mechanism. Worker uses `list_positions` only.
- First-pass block is never reversed in the engine; paper outcome is audit-only unless a future **separate** governance step promotes it.

## Reversibility

- Disable env flag `PAPER_SECOND_CHANCE_DISPLACEMENT`, stop optional worker timer, archive logs. Queue file can be truncated after evidence capture.

## Failure mode

- Any Alpaca read error during re-eval → **blocked** (`alpaca_list_positions_error:*`).
