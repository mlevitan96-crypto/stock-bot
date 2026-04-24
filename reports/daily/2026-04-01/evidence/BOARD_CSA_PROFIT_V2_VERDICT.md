# BOARD_CSA_PROFIT_V2_VERDICT

## Integrity preservation

- **PASS (scoped):** Mission used **read-only** log reads, separate Python processes for bars/uplift, and **no** `systemctl restart stock-bot`.  
- **Residual risk:** Alpaca API keys used from `.env` on host for **data** pull — same credential plane as trading; no orders were sent by V2 scripts.

## Causal validity

- **MEDIAN-SPLIT / bootstrap uplift** (`PROFIT_V2_SIGNAL_UW_UPLIFT.json`) is explicitly **non-causal** (same-sample, confounded by symbol/time).  
- **Horizon mark-to-market** (`PROFIT_V2_EXIT_TIMING_COUNTERFACTUALS.json`) is **not** an achievable exit policy (bar close, no slippage, no halts).  
- **Directional tail stats** favor LONG over SHORT in **this** window only — not proof of structural alpha.

## Governance risks

- **False certainty:** promoting horizon deltas or uplift scores into production gates without shadow + holdout.  
- **signal_context gap:** canonical learning file empty — governance should treat `score_snapshot` joins as **provisional** until emit path is proven (`verify_signal_context_nonempty.py`).

## Verdict

**CONDITIONAL GO** for continued **shadow-only** experiments; **NO-GO** for immediate production gate or weight changes from these artifacts alone.
