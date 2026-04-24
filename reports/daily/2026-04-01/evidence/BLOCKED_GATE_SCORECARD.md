# BLOCKED_GATE_SCORECARD

- **Single biggest BAD_GATE by `pnl_60m_opportunity_cost`:** `displacement_blocked` — **6859.3297** USD (sum of max(pnl,0) at 60m, Variant A, n=5705)
- **Single biggest GOOD_GATE (gate_class==GOOD_GATE) by `pnl_60m_loss_prevented`:** `max_new_positions_per_cycle` — **-151.3238** USD (sum of min(pnl,0) at 60m, Variant A, n=180)
- **Note:** `displacement_blocked` simultaneously ranks high on opportunity_cost and loss_prevented (bimodal counterfactual distribution); heuristic `gate_class` for that row is **BAD_GATE** in `BLOCKED_GATE_SCORECARD.json`.

See `BLOCKED_GATE_SCORECARD.json` for full per-reason table.
