# PROFIT_V2_FINAL_VERDICT

## Recovery vs re-capture

- **UW / scoring granularity:** **RECOVERED** from existing **`score_snapshot.jsonl`** (+ UW cache shards / audit markdowns). **`signal_context.jsonl` remains empty** (smoke test failed).  
- **Minute bars:** **RE-CAPTURED** into **`artifacts/market_data/alpaca_bars.jsonl`** (49 symbols, ~8.2 MB) via read-only Data API.

## Primary profit engine (this tail, descriptive)

- **LONG** directional bucket shows **positive** sum PnL and positive expectancy in `ALPACA_DIRECTIONAL_PNL_ANALYSIS.md`.

## Primary profit destroyer (this tail, descriptive)

- **SHORT** bucket shows **negative** sum PnL and negative expectancy in the same memo.

## Should shorts be disabled or gated?

- **Not on this evidence alone.** Recommendation: **shadow-gate or size-cap** shorts with explicit min-n per regime and **rollback** flag — see action rank 1 in `PROFIT_V2_ACTION_PLAN.json`.

## Exit timing change most supported

- **None for immediate execution.** Horizon stats are **small** and mixed: early horizons slightly **below** realized on average; **+60m** slightly **above** (`PROFIT_V2_EXIT_TIMING_COUNTERFACTUALS.md`). Treat as **hypothesis** for **paper/shadow** scenario replay only.

## First shadow experiment (one lever)

- **SHORT exposure shadow cap** (or regime-conditional SHORT off) with **30d** comparison to baseline — **verification:** shadow ledger + same telemetry sinks; **rollback:** disable shadow flag (no broker gate).

## Proof live trading was not impacted

- **No** `systemctl restart stock-bot` for Profit V2.  
- **No** changes to order logic or strategy parameters in this mission.  
- Workloads: **SFTP audit scripts**, **one-off Python** bars fetch + JSON generation using `.env` credentials **without** placing orders.  
- `systemctl status` during capture showed **active (running)** supervisor + `main.py` unchanged by this workflow.

## Adversarial reviews

- `BOARD_CSA_PROFIT_V2_VERDICT.md`  
- `BOARD_SRE_PROFIT_V2_VERDICT.md`  
- `BOARD_QUANT_PROFIT_V2_VERDICT.md`
