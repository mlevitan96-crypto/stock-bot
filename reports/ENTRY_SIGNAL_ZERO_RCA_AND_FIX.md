# Entry Signal 0.00 — Root Cause and Fix

**Date:** 2026-02-17  
**Context:** Dashboard Open Positions showed Entry Signal Strength 0.00 for 11 of 12 positions; only LCID showed 4.00.

---

## Summary

The "0 signal" in the Positions table is **Entry Signal Strength** = `entry_score` from `state/position_metadata.json`. Most positions showed 0.00 because their metadata was created by **reconciliation or health-check** when the position was discovered in Alpaca *after* the fact (e.g. order submitted → fill detected later, or restart sync). Those paths did not have access to the original composite score and wrote metadata **without** `entry_score` (or with 0.0).

---

## Root causes

1. **Pending-fill path**  
   When an order is submitted but not immediately filled, the engine does not call `mark_open()` (reconciliation is expected to do that when the fill appears). The score was never persisted, so when reconciliation or health check later added the position to metadata, they had no score to store.

2. **Health check adding missing positions**  
   In `main.py`, when the continuous health check adds a position that exists in Alpaca but not in bot metadata (`missing_in_bot`), it created a new metadata dict that did not include `entry_score`; it only *preserved* `entry_score` from existing metadata (empty for new symbols).

3. **Startup reconciliation**  
   `startup_reconcile_positions()` added missing positions from Alpaca with a metadata dict that had no `entry_score` key at all.

4. **Position reconciliation loop**  
   When syncing executor and metadata, it used existing `entry_score` or 0.0 and did not attempt to recover a score from elsewhere.

---

## Fixes implemented

1. **Pending-fill score persistence**  
   - New state file: `state/pending_fill_scores.json` (symbol → `{score, ts}`).  
   - When we log `entry_submitted_pending_fill`, we now call `persist_pending_fill_score(symbol, score)`.  
   - Reconciliation or health check can later read this when they add the position and set `entry_score`.

2. **Recovery helper**  
   - New module: `utils/entry_score_recovery.py`.  
   - `persist_pending_fill_score(symbol, score)` — write score for pending fills.  
   - `recover_entry_score_for_symbol(symbol, pop_pending=True)` — returns score from:  
     - `state/pending_fill_scores.json` (then removes that symbol if `pop_pending`), else  
     - last `open_<symbol>_*` record in `logs/attribution.jsonl` (context.entry_score).

3. **Health check**  
   When adding a missing position, we now try `recover_entry_score_for_symbol(symbol)` and set `entry_score` in the new metadata (or 0.0 if nothing recovered). We log `health_check.entry_score_recovered` when a score is recovered.

4. **Startup reconciliation**  
   Same: when creating metadata for a missing position, we call the recovery helper and set `entry_score`; we log `reconcile.entry_score_recovered` when recovered.

5. **Position reconciliation loop**  
   When updating metadata for a symbol that has `entry_score` 0.0, we try `recover_entry_score_for_symbol(symbol)` and use the result for both `position_metadata` and `executor_opens[symbol]["entry_score"]`. We audit-log `entry_score_recovered` when used.

---

## Existing positions with 0.00

For positions that *already* have 0.00 in metadata:

- **Going forward:** The next time reconciliation or health check runs and touches that symbol (e.g. metadata refresh), recovery will run and may fill in a score from attribution if there is a recent `open_` record for that symbol.  
- **One-time backfill:** Run `python scripts/backfill_entry_scores_from_attribution.py` to update `state/position_metadata.json` for all symbols that currently have missing or zero `entry_score` by using the last `open_` record in `logs/attribution.jsonl` per symbol. This only updates metadata on disk; it does not change Alpaca or executor state.

---

## Verification

- After deployment, when an order is submitted but not yet filled, `state/pending_fill_scores.json` should contain that symbol and score.  
- After the fill is detected and reconciliation/health check adds the position, metadata for that symbol should have a non-zero `entry_score` (and the dashboard should show it).  
- Run `python scripts/audit_signal_propagation.py --minutes 15` to confirm open positions have recent signal evaluation; entry score display is from metadata, not from that audit.  
- Optionally run the backfill script once to fix existing 0.00 positions that have attribution history.
