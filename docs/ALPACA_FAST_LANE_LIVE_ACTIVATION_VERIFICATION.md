# Alpaca Fast-Lane Live Activation Verification

## Overview

The Alpaca fast-lane shadow experiment uses 25-trade micro-windows, PnL tracking per cycle, candidate ranking, and a 500-trade supervisor with board-grade Telegram summary. It is **shadow-only**: no changes to live trading logic, no writes to the main experiment ledger.

## Cron Entries (Alpaca Droplet)

Install with: `python scripts/install_fast_lane_cron_on_droplet.py` (after code is pushed and pulled on droplet).

| Schedule     | Command |
|-------------|--------|
| Every 15 min | `*/15 * * * * . /root/.alpaca_env && cd /root/stock-bot && python3 scripts/run_fast_lane_shadow_cycle.py >> /root/fast_lane_shadow.log 2>&1` |
| Every 4 hours | `0 */4 * * * . /root/.alpaca_env && cd /root/stock-bot && python3 scripts/run_fast_lane_supervisor.py >> /root/fast_lane_supervisor.log 2>&1` |

- Ensure `/root/.alpaca_env` exists and is readable (sources `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, etc.).
- Cycle log: `logs/fast_lane_shadow.log` (in repo) and cron stdout: `/root/fast_lane_shadow.log`.
- Supervisor log: `/root/fast_lane_supervisor.log`.

## Manual Tests

1. **Cycle (local or droplet)**  
   `python3 scripts/run_fast_lane_shadow_cycle.py`  
   - If there are ≥25 new exit trades since last run: ledger and state update, cycle artifact under `state/fast_lane_experiment/cycles/cycle_XXXX/`, and Telegram cycle message (if env set).  
   - If &lt;25 new trades: script exits 0, no ledger change.

2. **Supervisor (force board message)**  
   `python3 scripts/run_fast_lane_supervisor.py --force`  
   - Sends board summary to Telegram (same env).  
   - Optional: `--reset-epoch` to clear ledger and state after sending.

3. **Confirm**  
   - Ledger: `state/fast_lane_experiment/fast_lane_ledger.json` (array of cycle entries).  
   - State: `state/fast_lane_experiment/fast_lane_state.json` (`last_processed_trade_index`, etc.).  
   - No errors in `logs/fast_lane_shadow.log`.

## Telegram

- Uses existing Alpaca Telegram env: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
- Cycle message: cycle_id, PnL USD, best_candidate_id, notes.
- Board message: total cycles, total trades, cumulative PnL, top candidates, CSA/SRE note.

## Dashboard

- **Tab:** More → **Alpaca Fast-Lane 25-Trade PnL**
- **API:** `GET /api/stockbot/fast_lane_ledger`
- Shows: total trades, cumulative PnL, table of PnL per cycle and running cumulative.

## CSA / SRE Notes

- **CSA:** Ledger schema and cycle scoring approved; shadow-only, no execution impact.
- **SRE:** Directory layout and disk usage under `state/fast_lane_experiment/` and `logs/` approved; cron and log paths documented above.

## Isolation Confirmed

- No writes to `state/governance_experiment_1_hypothesis_ledger_alpaca.json`.
- No writes to main config or live order path.
- Reads: `logs/exit_attribution.jsonl` (or `logs/alpaca_unified_events.jsonl` if present).

## Promotion Logic (Go-Forward, Robust Angles)

- Each 25-trade window: aggregate PnL by **14 angles** (strategy, exit_reason, exit_regime, entry_regime, regime_transition, sector, hold_bucket, exit_score_band, time_of_day, day_of_week, exit_regime_decision, score_deterioration_bucket, replacement, symbol). The (dimension, value) with **highest total PnL** in that window is **Promoted**.
- Telegram sends “Promoted: &lt;dimension&gt;:&lt;value&gt;” and optional runner-ups. Dashboard table shows “Promoted” per cycle.
- Full design: `docs/SHADOW_25_TRADE_PROMOTION_EXPERIMENT_DESIGN.md`.

## Next Steps

- After 500 trades in the fast-lane ledger, supervisor (or `--force`) sends board summary; optionally run with `--reset-epoch` to start a new epoch.
- Use dashboard panel and Telegram to monitor; CSA/SRE review per governance framework.
