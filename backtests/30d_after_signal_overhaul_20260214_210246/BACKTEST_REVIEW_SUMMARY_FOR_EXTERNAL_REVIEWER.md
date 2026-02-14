# 30-Day Backtest After Signal-Quality Overhaul — Summary for External Reviewer

**Run date:** 2026-02-14 (UTC)  
**Environment:** Production droplet (paper trading); replay from attribution, exit_attribution, and blocked_trades logs.  
**Code:** Post–signal-quality overhaul (EMA smoothing, persistence, longevity, trend confirmation, volatility filter; applied before UW and survivorship in entry scoring).

---

## Window and scope

- **Window:** 2026-01-15 to 2026-02-14 (30 days).
- **Data source:** Droplet logs (attribution.jsonl, exit_attribution.jsonl, state/blocked_trades.jsonl).
- **Config:** Paper mode; exit regimes, UW, survivorship, constraints, correlation sizing, and wheel strategy enabled.

---

## Aggregate results

| Metric | Value |
|--------|--------|
| **Trades (executed)** | 2,243 |
| **Exits (recorded)** | 2,815 |
| **Blocks (blocked trade attempts)** | 2,000 |
| **Total P&L (USD)** | -$162.15 |
| **Winning trades** | 340 |
| **Losing trades** | 650 |
| **Win rate (%)** | 15.16 |

---

## Exit regime mix

- **Normal:** 1,728 exits  
- **Fire sale:** 1,087 exits  

Exit reasons are predominantly **signal_decay** (with and without flow_reversal and stale_alpha_cutoff); a smaller share are trail_stop and stale_alpha_cutoff-only.

---

## Block reasons (why trades did not execute)

| Reason | Count |
|--------|--------|
| max_new_positions_per_cycle | 1,041 |
| max_positions_reached | 282 |
| expectancy_blocked:score_floor_breach | 357 |
| displacement_blocked | 214 |
| symbol_on_cooldown | 63 |
| order_validation_failed | 43 |

Capacity (max positions / max new per cycle) and score-floor/expectancy blocks are the main limiters; displacement and cooldowns are secondary.

---

## Artifacts on GitHub

- **Repo:** stock-bot (main branch).  
- **Path:** `backtests/30d_after_signal_overhaul_20260214_210246/`  
- **Files committed:**  
  - `backtest_summary.json` — full summary (config, counts, exit_reason_counts, exit_regime_counts, block_reason_counts).  
  - `backtest_pnl_curve.json` — cumulative P&L by trade index and dates.  
- **Note:** `backtest_trades.jsonl`, `backtest_exits.jsonl`, and `backtest_blocks.jsonl` are generated on the droplet but not in the repo (gitignore of `*.jsonl`). Summary and PnL curve contain the aggregated metrics above.

---

## Context for reviewer

This run reflects the system **after** the signal-quality overhaul: entry scoring now applies smoothing (EMA), persistence (2 consecutive positive signals), longevity (average of recent smoothed signals), trend confirmation, and a volatility filter (ATR threshold) **before** UW and survivorship adjustments. The backtest replays the same historical log data as the prior intelligence-overhaul run; it does not re-run the live trading engine. Use it to assess exit/block mix and P&L with signal-quality logic in place, not as a forward-looking guarantee.
