# 5-Day Rolling PnL — Cron (every ~10 minutes)

**Canonical state:** `reports/state/rolling_pnl_5d.jsonl`  
**Script:** `scripts/performance/update_rolling_pnl_5d.py`  
**Log (droplet):** `logs/rolling_pnl_5d.log`

## Cron entry (droplet)

Add to crontab on the droplet (project root e.g. `/root/stock-bot`):

```cron
*/10 * * * * cd /root/stock-bot && /root/stock-bot/venv/bin/python scripts/performance/update_rolling_pnl_5d.py >> logs/rolling_pnl_5d.log 2>&1
```

- **Schedule:** Every 10 minutes.
- **Idempotent:** Append one point per run; prune points older than 5 days.
- **No backfilling:** Only current snapshot is appended.

## Verify

- Cron runs: `crontab -l | grep update_rolling_pnl_5d`
- Log grows: `tail -n 20 logs/rolling_pnl_5d.log`
- State file: `wc -l reports/state/rolling_pnl_5d.jsonl` (bounded by ~720 points for 5d at 10-min interval)

## Idempotence

Running the script twice in the same minute appends two points (same ts truncated to run time). Acceptable; pruning keeps the file bounded. For strict one-point-per-10min, ensure cron is the only invoker.
