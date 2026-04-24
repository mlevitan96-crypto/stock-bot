# BLOCKED_WHY_FINAL_VERDICT

## Single biggest BAD_GATE by opportunity_cost (60m, Variant A)

- **`displacement_blocked`** — **`pnl_60m_opportunity_cost` = 6859.3297** USD, **n = 5705** (`BLOCKED_GATE_SCORECARD.json` → `biggest_bad_gate_by_oc_60m`).

## Single biggest GOOD_GATE by loss_prevented (60m, Variant A, gate_class filter)

- **`max_new_positions_per_cycle`** — **`pnl_60m_loss_prevented` = -151.3238** USD (sum of negative PnLs), **n = 180** (`BLOCKED_GATE_SCORECARD.json` → `biggest_good_gate_by_loss_prevented_60m`).

## Primary recognition failure

- **Taxonomy:** `OVERRIDE_CONFLICT`  
- **One-line why:** Displacement capacity policy sets `policy_allowed=False` (without qualifying override), blocking challengers that—under post-hoc minute bars—often show **positive** 60m Variant-A PnL.  
- **Evidence:** `BLOCKED_WHY_DIAGNOSIS.json` (`taxonomy_evidence`, `primary_recognition_failure_hard_gate_line`), `main.py` **9529–9574**, `PAPER_EXPERIMENT_RESULTS.json`.

## UW granularity joinable?

- **Partially.** `score_snapshot.jsonl` = **2000** lines; blocked rows include **`components` / `signals`**. `signal_context.jsonl` = **0** lines (`UW_GRANULARITY_SMOKE_PROOF.md`). **No** new `uw_signal_context` sink added (`UW_GRANULARITY_RECOVERY_OR_RECAPTURE.md`).

## Paper experiment run — real PnL?

- **Run:** offline stats script (`PAPER_EXPERIMENT_SPEC.md`, `PAPER_EXPERIMENT_RESULTS.md`, `PAPER_EXPERIMENT_RESULTS.json`).  
- **Real / broker PnL:** **unchanged** (no orders, no engine config toggle).

## Next **one** experiment (not a list)

- **Walk-forward 5 sessions:** recompute **only** `displacement_blocked` **60m expectancy + p05** with fresh bars fetch merged from blocked windows; compare deltas to `BLOCKED_GATE_SCORECARD.json` — **verify:** new `BLOCKED_GATE_SCORECARD.json`; **rollback:** discard new evidence dir + restore prior `alpaca_bars.jsonl` from backup if needed.
