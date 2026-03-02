# UW Score-Kill Fix Verification (2026-03-02)

## Confirmation: UW_MISSING_INPUT_MODE=passthrough on droplet

- **Phase 2** (orchestrator): `.env` in project directory was updated to include `UW_MISSING_INPUT_MODE=passthrough`. Command output confirmed:
  ```
  --- .env UW_MISSING_INPUT_MODE ---
  UW_MISSING_INPUT_MODE=passthrough
  ```
- The live/paper process (`main.py`) loads `.env` via `load_dotenv(_REPO_ROOT / ".env")` at startup (see `main.py` ~302). After **Phase 4** (restart stock-bot and uw-flow-daemon), the running process therefore has `UW_MISSING_INPUT_MODE=passthrough` in its environment.
- **Trace script note:** The trace run during Phase 5 reported `UW_MISSING_INPUT_MODE: reject` because the trace script did not load `.env` before reading the env var. The trace script has been updated to call `load_dotenv(REPO / ".env")` before reporting env, so future runs of `python scripts/run_live_trading_trace_via_droplet.py` will show `passthrough` when `.env` is set.

---

## Confirmation: apply_uw_to_score preserves composite scores under passthrough

- **Code** (`board/eod/live_entry_adjustments.py`):
  - `UW_MISSING_INPUT_MODE` is read from the environment (line 24).
  - When `UW_MISSING_INPUT_MODE == "passthrough"`, the function returns `(composite_score, details)` immediately (lines 191–196), without applying UW quality reject or penalty, so the composite score (2.7–4.x) is preserved into the expectancy gate.

---

## Snippets from run_live_trading_trace_via_droplet.py (passthrough)

- Trace output after trace script was updated to load `.env`:
  ```
  --- Env ---
    TRADING_MODE: PAPER
    PAPER_TRADING: true
    UW_MISSING_INPUT_MODE: passthrough  (use passthrough so composite score is preserved for expectancy gate)
  ```
- **Confirmed:** `UW_MISSING_INPUT_MODE=passthrough` is active on the droplet (trace run from local via `python scripts/run_live_trading_trace_via_droplet.py`).

---

## Latest logs/run.jsonl (at verification time)

At the time of orchestration (post-restart), the last line of `logs/run.jsonl` was:

```json
{"ts": "2026-03-02T18:50:34.369991+00:00", "_ts": 1772477434, "msg": "complete", "clusters": 51, "orders": 0, "market_open": true, "engine_status": "ok", "errors_this_cycle": [], "metrics": {"clusters": 51, "orders": 0, ...}, "strategy_id": "equity"}
```

- **clusters:** 51  
- **orders:** 0 (this line is from *before* the restart; the next cycle(s) after the fix should be able to place orders when candidates pass composite + expectancy).

After at least one full cycle with the new code and `.env`:

- Run: `tail -1 logs/run.jsonl` on the droplet (or re-run the trace).
- Confirm: `"clusters" >= 1` and, when symbols pass both gates, `"orders" >= 1`.

---

## state/blocked_trades.jsonl (no more score=0.172 kills)

At verification time, the last three blocked_trades still showed `score=0.172` (e.g. MSFT, AMZN, BA). Those entries may be from cycles that ran before the restart or before the new .env was fully in effect. With passthrough now confirmed in the trace:

- New blocked_trades (if any) should no longer show every candidate with `score=0.172` and `score_floor_breach`.
- Scores at the expectancy gate should be the original composite scores (2.7–4.x), not 0.172.

Trace also showed: cache fresh (0/53 stale), composite pass 14/15 symbols with score >= 2.7 → clusters should be produced; with passthrough, the next cycle(s) can pass the expectancy gate and place orders.

To confirm after a cycle or two:

- Inspect: `state/blocked_trades.jsonl` (e.g. `tail -5`).
- Check that recent entries either have `score` in the 2.7–4.x range or are blocked for reasons other than `score_floor_breach` with score 0.172.

---

## Summary

| Item | Status |
|------|--------|
| UW_MISSING_INPUT_MODE=passthrough in droplet .env | Set in project_dir (and optionally get_root) by orchestrator |
| apply_uw_to_score preserves composite under passthrough | Implemented in `board/eod/live_entry_adjustments.py` |
| Deploy (fetch + reset, pytest, restart) | Completed via orchestrator |
| stock-bot + uw-flow-daemon restart | Completed |
| Trace script shows passthrough | Confirmed: trace reports `UW_MISSING_INPUT_MODE: passthrough` |
| run.jsonl orders > 0 | To be confirmed after next cycle(s) with new code + .env |
| blocked_trades no longer all 0.172 | To be confirmed after next cycle(s) |

No other configs or levers were changed; only UW passthrough, deploy, restart, and verification steps were performed.
