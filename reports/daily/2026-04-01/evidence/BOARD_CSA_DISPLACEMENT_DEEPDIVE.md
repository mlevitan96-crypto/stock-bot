# BOARD_CSA — Displacement deep dive

**Evidence anchors:** `scripts/audit/run_displacement_deepdive_addon.py` (droplet run), `DISPLACEMENT_OVERRIDE_MAP.json`, `DISPLACEMENT_GOOD_VS_BAD_SEPARATION.json`, `DISPLACEMENT_EXIT_EMULATOR_RESULTS.json`, upstream `BLOCKED_COUNTERFACTUAL_PNL_FULL.json`.

## 1) Still within decision-time information (no lookahead)?

**Mostly yes, with one explicit boundary.**

- **Entry intent / gate context:** Reconstructed from `state/blocked_trades.jsonl` at `block_ts`, plus `logs/score_snapshot.jsonl` joined by **nearest snapshot at or before** block time (no future snapshots).
- **Counterfactual PnL:** Uses post-`block_ts` prices from the blocked-why pipeline (`BLOCKED_COUNTERFACTUAL_PNL_FULL.json`); that is **outcome** data used only for labeling GOOD/BAD and opportunity stats — it must **not** be fed into any live decision rule. The separation rules in Phase 11 use only features available at or before `block_ts` (hour, distance-to-threshold, ATR/volume from bars **ending before/at entry bar**, concurrency in the same minute, snapshot join flag).
- **Exit emulator:** Forward path on 1m bars from the **entry bar index** onward; no peeking at bars before the modeled entry bar for exit triggers beyond the documented ATR proxy window.

**Residual risk:** If any upstream blocked row or snapshot timestamp were mis-normalized, lookahead could appear; CSA defers to the blocked-why pipeline’s own timestamp contract for counterfactual bars.

## 2) Confusing counterfactual with realizable PnL?

**Yes, if interpreted naïvely — must keep the distinction explicit.**

- Counterfactual and emulator outputs are **hypothetical** paths (fixed-horizon variant A and simplified stop/TP/time-stop on 1m bars). They **do not** include full production exit state, partial fills, spread model, or displacement policy dynamics after a hypothetical fill.
- **Actionable control** should be **paper / governance** first: e.g. conditional review of displacement vetoes, not automatic size-up from counterfactual mean alone.

## 3) Is proposed conditionalization reversible and safe?

**Yes, if implemented as paper-only policy.**

- The top univariate signals (e.g. `dist_thr` split in `DISPLACEMENT_GOOD_VS_BAD_SEPARATION.json`) are **weak** (small impurity reduction) and **stability splits** show the single rule does not reliably beat baseline accuracy on time/symbol splits — so any lever should be **documentation + optional human review**, not silent auto-override of `displacement_gate`.
- **Rollback:** Revert the paper rule or toggle a config flag that only affects reporting/checklists, not order submission.
