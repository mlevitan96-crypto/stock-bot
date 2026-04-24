# BLOCKED_WHY_DIAGNOSIS

## Top 10 BW clusters (block_reason, count) — winners at +60m Variant A

- `displacement_blocked`: 3256
- `max_positions_reached`: 1102
- `order_validation_failed`: 303
- `expectancy_blocked:score_floor_breach`: 120
- `max_new_positions_per_cycle`: 84

## Top 10 AL clusters (exit reason, count) — negative realized pnl

- `signal_decay(0.70)`: 11
- `signal_decay(0.93)`: 9
- `signal_decay(0.88)`: 9
- `signal_decay(0.65)+flow_reversal`: 9
- `signal_decay(0.64)`: 8
- `signal_decay(0.63)`: 8
- `signal_decay(0.92)`: 7
- `signal_decay(0.69)`: 7
- `signal_decay(0.84)`: 6
- `signal_decay(0.94)`: 6

## Primary recognition failure

Primary recognition failure is **OVERRIDE_CONFLICT**: the **displacement** policy blocks challengers (`displacement_blocked`) even when ex-post 60m Variant-A counterfactual PnL is positive for many rows, evidenced by **`main.py`** (~9529–9574), **`BLOCKED_GATE_SCORECARD.json`**, and **`BLOCKED_COUNTERFACTUAL_PNL_FULL.json`**.

---

Primary recognition failure is **OVERRIDE_CONFLICT**: displacement capacity policy denies `policy_allowed` so challengers are blocked while minute-bar counterfactuals show positive 60m Variant-A PnL for 3256/5705 covered `displacement_blocked` rows, evidenced by `BLOCKED_WHY_DIAGNOSIS.json`, `BLOCKED_GATE_SCORECARD.json`, `PAPER_EXPERIMENT_RESULTS.json`, and `main.py` lines 9529–9574.
