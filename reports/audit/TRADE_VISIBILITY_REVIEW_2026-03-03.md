# Trade Visibility Review

**Window:** since 2026-03-01 21:45 UTC
**Generated:** 2026-03-03 21:45 UTC

## 1. Executed trades (closed) in window

| Metric | Value |
|--------|-------|
| Trades closed | 0 |
| Wins | 0 |
| Losses | 0 |
| Win rate | 0.0% |
| Total P&L (USD) | $0.00 |

## 2. 100-trade baseline (direction replay)

Direction replay runs after we have **>=100 telemetry-backed trades** in `logs/exit_attribution.jsonl` 
(records with `direction_intel_embed.intel_snapshot_entry`). State: `state/direction_readiness.json`.

| Metric | Value |
|--------|-------|
| Exit attribution records (total) | 36 |
| Telemetry-backed (have intel snapshot at entry) | 0 |
| Progress to 100 | 0/100 |
| % telemetry | 0.0% |
| Ready for replay (>=100 & >=90%) | False |

## 3. Recent closed trades (sample)

No closed trades in window.

---

## Note: Run on droplet for live counts

This report was generated **locally**. For visibility into trades executed on the live/paper bot (yesterday and today), run the review on the droplet:

```bash
python scripts/run_trade_visibility_review_on_droplet.py
```

Or SSH to the droplet and run:

```bash
cd /root/stock-bot && python3 scripts/trade_visibility_review.py --since-hours 48 --out reports/audit/TRADE_VISIBILITY_REVIEW_droplet.md
```

- **Executed trades** come from `logs/attribution.jsonl` (closed only; excludes `open_` trade_id).
- **100-trade baseline**: direction replay requires >=100 records in `logs/exit_attribution.jsonl` that have `direction_intel_embed.intel_snapshot_entry` (telemetry at entry), and >=90% of exit_attribution records must be telemetry-backed. State is in `state/direction_readiness.json`.
- **Entries/exits/sizing**: the script summarizes by symbol, close reason, and qty (from context) for the chosen window.
