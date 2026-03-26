# Win Finding Result — MIN_TRADES=2000 (Real Droplet Data)

## What we ran
- **Truth:** 30d droplet truth (massive_profit_review)
- **Policies:** 601 (permissive grid: entry_min 0–3.5, hold_min 0–60, long/short/both + intel-driven)
- **MIN_TRADES:** 2000

## Finding
**Only 3 policies clear 2000 trades.** All three are the same outcome:
- **policy_0001/0002/0003:** `entry_min=0.0`, `hold_min=0`, dir=long/short/both  
- **Trades:** 2327 (full truth set)  
- **Total PnL:** -133.09 (USD or USD-equivalent from pnl_pct)  
- **Win rate:** 14.65%

So with MIN_TRADES=2000, the only combination that reaches the bar is “take all trades.” The entire 30d truth set is net negative. **There is no winning combination at 2000+ trades in this dataset.**

## What “causes” up or down
- Moves are already labeled in percent-move intelligence (entry_score before +X% / -X% moves).
- The simulator does not filter by direction (long/short) per trade; it only filters by entry_score and hold_min.
- So the “cause” we can act on is **entry_score**: higher entry_score filters to trades that had stronger signal. Best *reduction in loss* at 500+ trades was entry_min=3.5, hold_min=0 (704 trades, -83.13 vs -133.09 full set).

## How to get to winning
1. **Raise the bar on entry** so the subset of trades is profitable: keep increasing entry_min (and/or hold_min) and re-run until some combination has 2000+ trades and **positive** PnL. Right now, no such combination exists in this truth.
2. **Improve the universe:** fix costs/slippage, or improve entry/exit so the full 30d population has positive expectancy; then “take all” (or a broad filter) will be winning at 2000+.
3. **Direction:** add per-trade direction/side to truth and simulator so we can test “long only” vs “short only” and see if one side is profitable at 2000+.

## Artifacts
- `aggregate_result.json` — top_n and ranked
- `candidate_policies.json` — full grid
- `CURSOR_FINAL_SUMMARY.txt` — run summary
