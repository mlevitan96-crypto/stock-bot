# Block 3H — First Profitability Iteration (Implemented)

**Status:** Implemented. Ready for deployment and 30d comparison.

---

## What was done

1. **DEFAULT_SIGNAL_WEIGHTS_3H** added in `src/signals/raw_signal_engine.py`:
   - trend_signal: 0.05 → **0.055**
   - momentum_signal: 0.04 → **0.045**
   - reversal_signal: 0.015 → **0.012**
   - mean_reversion_signal: 0.015 → **0.012**
   - (volatility, regime, sector, breakout unchanged)

2. **Regime-adjusted weights** now use 3H as base: `compute_regime_adjusted_weights()` and `get_weighted_signal_delta_3D()` default to `DEFAULT_SIGNAL_WEIGHTS_3H`. So live scoring uses slightly more trend/momentum and slightly less reversal/mean_reversion (conservative tweak for MIXED/unknown regime).

3. **Backtest script** supports shorter windows: `--start-date`, `--end-date`, `--days N` for faster iteration (e.g. `--days 7` on droplet with `BACKTEST_DAYS=7`).

4. **Droplet shell script** passes `BACKTEST_DAYS` when set: `BACKTEST_DAYS=7 bash board/eod/run_30d_backtest_on_droplet.sh` runs a 7-day window (fewer events, faster injection run).

---

## How to see P&L impact

The 30d backtest **replays historical logs** (attribution.jsonl, blocked_trades.jsonl). Changing weights does **not** change which trades are in those logs. So:

- **To compare P&L with 3H:** Run the **bot** (paper or live) with 3H code for **30 days** so new attribution and blocks are written. Then run the backtest script on that new 30d of logs. Compare `total_pnl_usd` and `win_rate_pct` to the current baseline (-$162.15, 15.16%).

- **Faster check (optional):** Use a 7-day window: set `BACKTEST_DAYS=7` when running the droplet backtest to get signal-edge data faster (smaller sample).

---

## Verifiable next steps (in order)

| Done | Step |
|------|------|
| ✓ | Implement Block 3H (conservative weight tweaks). |
| ✓ | Add --days / BACKTEST_DAYS for shorter-window backtest. |
| — | Get one 3g run **with injection** (full or 7-day) so we have per-signal edge; then refine 3H weights from that report if needed. |
| — | Deploy 3H; run bot 30 days; run backtest on new logs; compare P&L to baseline. |

All tests (validation.scenarios.test_raw_signal_engine) pass with 3H.
