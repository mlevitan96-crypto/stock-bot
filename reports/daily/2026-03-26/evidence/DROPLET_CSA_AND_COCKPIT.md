# Droplet: CSA 100-trade trigger and Profitability Cockpit

## After deploy (or start of trading day)

On the droplet, from repo root:

```bash
# Reset CSA trade count to market open today and refresh the cockpit dashboard
python scripts/reset_csa_trade_count_for_today.py
```

This will:

1. Set `reports/state/TRADE_CSA_STATE.json` to zeros (total_trade_events and last_csa_trade_count).
2. Clear `reports/state/trade_events.jsonl` so the next 100 trades trigger CSA.
3. Regenerate `reports/board/PROFITABILITY_COCKPIT.md` with current CSA status, trade counts, and next CSA threshold (100).

## When the cockpit updates

- **After every CSA 100-trade run:** `scripts/run_csa_every_100_trades.py` now runs `scripts/update_profitability_cockpit.py` when CSA finishes, so the Profitability & Learning dashboard shows the latest mission, verdict, and narrative.
- **On day reset:** `scripts/reset_csa_trade_count_for_today.py` also regenerates the cockpit.
- **Manual refresh:** Run `python scripts/update_profitability_cockpit.py` anytime you want the cockpit to reflect latest governance, SRE, or weekly ledger without waiting for the next CSA.

## Refreshing the dashboard only

If you did not reset and only want to refresh the cockpit from latest artifacts:

```bash
python scripts/update_profitability_cockpit.py
```

## Optional: periodic cockpit refresh (cron)

To keep the cockpit narrative fresh between CSA runs (e.g. after governance or SRE updates):

```bash
# Example: refresh cockpit every hour during market hours (14–21 UTC weekdays)
0 14-21 * * 1-5 cd /path/to/stock-bot && python scripts/update_profitability_cockpit.py >> logs/cockpit_refresh.log 2>&1
```

Replace `/path/to/stock-bot` with the actual repo path on the droplet.

## Confirm everything is live

- **CSA live:** `reports/audit/CSA_VERDICT_LATEST.json` exists and is recent.
- **100-trade trigger wired:** `reports/state/TRADE_CSA_STATE.json` exists; after reset, `total_trade_events` is 0 and `trades_until_next` in the cockpit is 100.
- **Dashboard:** `reports/board/PROFITABILITY_COCKPIT.md` shows CSA status, promotable items, governance/SRE health, and next actions.

## Backup CSA trigger (optional cron)

To run the backup CSA trigger every 5 minutes (in case the primary trigger in the trading engine missed a 100-trade milestone):

```bash
# Example crontab entry
*/5 * * * * cd /path/to/stock-bot && python scripts/csa_backup_trigger_every_100.py
```

Replace `/path/to/stock-bot` with the actual repo path on the droplet.
