# SRE scheduler proof

**Generated (UTC):** 2026-03-05T18:01:31.382440+00:00

## Scheduler type

cron

## Interval

Every 10 minutes

## Last run timestamp

2026-03-05T18:01:27.738858+00:00

## Deployed commit (at install time)

f1bf02b64996

## Cron line

```
*/10 * * * * cd /root/stock-bot && /root/stock-bot/venv/bin/python scripts/sre/run_sre_anomaly_scan.py --base-dir . >> logs/sre_anomaly_scan.log 2>&1
```
