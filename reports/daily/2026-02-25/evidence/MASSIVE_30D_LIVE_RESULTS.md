# Massive 30d Profit Review — Live Results (2026-02-25)

**Run:** `massive_30d_profit_review_20260225T011830Z`  
**Fix applied:** Backtest window now uses last N days from **today** when `--days` is passed (so it overlaps droplet attribution).

---

## Live numbers (from droplet)

| Metric | Value |
|--------|--------|
| **Window** | 2026-01-26 → 2026-02-25 (30 days) |
| **Trades (attribution)** | 2,327 |
| **Exits** | 2,000 |
| **Blocks** | 963 |
| **Total PnL (after costs)** | **-$133.09** |
| **Win rate** | **14.65%** |
| **Bar dates available** | 14 |

---

## Truth dataset

- **total_from_trades_usd:** -133.09  
- **total_from_exits_usd:** -214.97  
- **Bar coverage:** 14 days in `data/bars`

---

## Campaign (4 iterations)

All four iterations ran the same baseline 30d attribution replay (no policy variation yet):

| Rank | Iteration | TOTAL_PNL_AFTER_COSTS | Trades | Win rate |
|------|------------|------------------------|--------|----------|
| 1 | iter_0001 | -$133.09 | 2,327 | 14.65% |
| 2 | iter_0002 | -$133.09 | 2,327 | 14.65% |
| 3 | iter_0003 | -$133.09 | 2,327 | 14.65% |
| 4 | iter_0004 | -$133.09 | 2,327 | 14.65% |

Promotion payloads written to `promotion_payloads/` (PAPER_ONLY).

---

## Profit-bleed hypotheses (from review)

1. Entry selectivity too low: high-score bucket still negative after costs.  
2. Direction choice weak: long/short not aligned with realized returns.  
3. Exit timing suboptimal: winners cut early or losers linger.  
4. Sizing miscalibrated: size not proportional to edge/volatility.  
5. Costs/slippage underestimated: apparent edge disappears after execution.

---

## Artifacts (local)

- `aggregate_result.json` — ranked iterations and promotion payloads  
- `review/MASSIVE_REVIEW_SEED.json` — window, counts, PnL, hypotheses  
- `review/multi_model/board_verdict.md` — multi-persona verdict (from review step; run now has 2,327 trades)

---

## Code change that fixed 0 trades

**File:** `scripts/run_30d_backtest_droplet.py`  

When `--days` is passed, the window is now **always** “last N days from today” (UTC). Config `end_date` is no longer used in that case, so the backtest window matches current attribution on the droplet.
