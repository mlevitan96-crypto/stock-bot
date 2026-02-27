# Phase 1 Audit — Droplet Results

**Generated:** 2026-02-27T22:45:52.510980+00:00

## Services

- **stock-bot.service:** True
- **uw-flow-daemon.service:** True

## Env keys (masked)

SIGNAL_SCORE_BREAKDOWN_LOG, MIN_EXEC_SCORE, TRUTH_ROUTER_ENABLED, TRUTH_ROUTER_MIRROR_LEGACY, STOCKBOT_TRUTH_ROOT

## Alpaca alignment

```json
{
  "error": "snapshot_failed"
}
```

**Note:** Snapshot failed (env var or path on droplet). `scripts/alpaca_alignment_snapshot.py` now tries both `ALPACA_KEY`/`ALPACA_SECRET` and `ALPACA_API_KEY`/`ALPACA_API_SECRET`. Re-run Phase 1 after pulling to get alignment.

## Log tail (last 30 lines)

```
check: False (SIMULATE_MARKET_OPEN=False)
Feb 27 22:45:46 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[230148]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Feb 27 22:45:46 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[230148]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Feb 27 22:45:46 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[230148]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Feb 27 22:45:46 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[230148]: [trading-bot] ERROR EXITS: Failed to close PFE (attempt 3/3): close_position_api_once returned None
Feb 27 22:45:46 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[230148]: [trading-bot] ERROR EXITS: All 3 attempts to close PFE failed
Feb 27 22:45:46 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[230148]: [trading-bot] WARNING EXITS: PFE could not be verified as closed after 3 attempts - keeping in tracking for retry
Feb 27 22:45:46 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[230148]: [trading-bot] DEBUG EXITS: Closing CAT (decision_px=742.83, entry=741.89, hold=120.0min)
Feb 27 22:45:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[230148]: [trading-bot] ERROR EXITS: Failed to close CAT (attempt 1/3): close_position_api_once returned None
Feb 27 22:45:51 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[230148]: [trading-bot] ERROR EXITS: Failed to close CAT (attempt 2/3): close_position_api_once returned None
Feb 27 22:45:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[230148]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:455: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Feb 27 22:45:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[230148]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()

```
