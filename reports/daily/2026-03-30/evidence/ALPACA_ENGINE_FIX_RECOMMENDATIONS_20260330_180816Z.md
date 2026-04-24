# ALPACA ENGINE — FIX RECOMMENDATIONS (advisory)

- UTC `20260330_180816Z`

1. **Metadata backfill** — ensure `entry_score`, `entry_reason`, and `v2` snapshot blocks are populated on open fills for decay/v2-exit parity.
2. **Stale windows** — review `TIME_EXIT_MINUTES`, `STALE_TRADE_EXIT_MINUTES`, `TIME_EXIT_DAYS_STALE` vs observed holding periods.
3. **Trailing stop** — review `TRAILING_STOP_PCT`, profit-acceleration at 30m, and MIXED-regime 1.0% tightening.
4. **Profit / stop rationalization** — align `profit_targets_v2` / `stops_v2` advisory levels with engine decimal targets (0.75% / -1% default).
5. **Structural exit** — validate `structural_intelligence` recommendations vs live book.
6. **v2 exit score** — audit weights via tuning; threshold 0.80 is the promotion line in code.
7. **Position cap policy** — reconcile `MAX_CONCURRENT_POSITIONS` with live slot usage and displacement eligibility.
8. **Peak equity** — verify `state/peak_equity.json` initialization after restarts for drawdown/risk gates.
