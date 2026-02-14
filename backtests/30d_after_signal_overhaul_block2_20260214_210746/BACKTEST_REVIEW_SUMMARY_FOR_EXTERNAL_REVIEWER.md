# 30-Day Backtest After Signal Overhaul Block 2 — External Review Summary

**Run date:** 2026-02-14 21:07:46 UTC  
**Environment:** Production droplet (paper trading replay).  
**Code:** Post–Signal Overhaul Block 2 (multi-frame validation, regime alignment, sector alignment, predictive scoring).

---

## Window

2026-01-15 → 2026-02-14 (30 days)

---

## Data sources

- attribution.jsonl  
- exit_attribution.jsonl  
- state/blocked_trades.jsonl  

---

## Aggregate results

| Metric | Value |
|--------|--------|
| Trades (executed) | 2,243 |
| Exits (recorded) | 2,815 |
| Blocks (blocked attempts) | 2,000 |
| Total P&L (USD) | -$162.15 |
| Winning trades | 340 |
| Losing trades | 650 |
| Win rate (%) | 15.16 |

---

## Intelligence layer enabled

- Exit regimes  
- UW scoring  
- Survivorship shaping  
- **Predictive signal scoring (Block 2):** multi-frame validation, regime alignment, sector momentum alignment  
- Wheel gating  
- Constraints  
- Correlation sizing  

---

## Artifacts on GitHub

- **Repo:** stock-bot (main branch).  
- **Path:** `backtests/30d_after_signal_overhaul_block2_20260214_210746/`  
- **Files committed:**  
  - backtest_summary.json  
  - backtest_pnl_curve.json  
  - BACKTEST_REVIEW_SUMMARY_FOR_EXTERNAL_REVIEWER.md  
- **Droplet only (gitignored):** backtest_trades.jsonl, backtest_exits.jsonl, backtest_blocks.jsonl  

---

## Context for reviewer

This run reflects the system **after** predictive-signal strengthening (Block 2): multi-frame validation (fast/slow signal agreement), regime alignment (BULL/BEAR vs signal direction), and sector momentum alignment. The backtest replays historical log data only; it does not re-run the live trading engine. Use it to assess exit/block mix and P&L with predictive scoring in place, not as a forward-looking guarantee.
