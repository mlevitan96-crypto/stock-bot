# BOARD_SRE_BLOCKED_WHY_VERDICT

Mandatory questions:

1. **Are datasets complete, stable, and reproducible?**  
   **Reproducible given frozen inputs:** `8669` blocked rows, `432` exits, `53` bar symbols, `99.8154%` full-horizon coverage (`BLOCKED_WHY_BARS_COVERAGE.json`). Re-run: `run_blocked_why_pipeline.py` + same `alpaca_bars.jsonl`.

2. **Are bars fetches rate-limited, cached, and safe?**  
   **Rate limit:** `time.sleep(0.25)` per day-request in `fetch_alpaca_bars_for_counterfactuals.py` (`_fetch_bars_day`). **Host:** default `https://data.alpaca.markets` when `ALPACA_DATA_URL` unset (see file `_data_base_url`). **Fail-closed:** empty HTTP returns `[]` for that day; script exits non-zero if zero symbols written (documented in prior Profit V2 work).

3. **Disk growth / rotation bounded?**  
   **This run:** `BLOCKED_COUNTERFACTUAL_PNL_FULL.json` is large (full per-row) — monitor `reports/daily/*/evidence/` size; `droplet_disk_cleanup.py` lists `state/blocked_trades.jsonl` as managed path (repo reference).

4. **Risk to live services (CPU, IO, timers)?**  
   **Low:** pipeline + offline stats are separate processes; **no** stock-bot restart (`PAPER_EXPERIMENT_ROLLBACK_PROOF.md`).

5. **Joins time-safe (no lookahead)?**  
   **Entry bar:** first with `t >= block_ts`. **Exit bar:** first with `t >= block_ts + H`. Uses only data **at or after** decision anchor — documented in `BLOCKED_WHY_INFERENCE_RULES.md` + `run_blocked_why_pipeline.py`.

**STOP:** **not** issued.
