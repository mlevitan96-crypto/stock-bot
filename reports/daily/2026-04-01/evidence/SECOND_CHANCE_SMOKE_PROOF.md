# SECOND_CHANCE_SMOKE_PROOF

- `logs/second_chance_displacement.jsonl` line count: **500** (non-empty: YES).
- Worker and scheduler contain **no** `submit_order` (see SECOND_CHANCE_IMPLEMENTATION.md).
- Smoke used **seeded** historical `displacement_blocked` rows + `--process-queue` (read-only broker).

## journalctl tail (30m)

```
Apr 02 00:10:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 00:10:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 00:10:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PLTR (attempt 2/3): close_position_api_once returned None
Apr 02 00:10:50 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PLTR (attempt 3/3): close_position_api_once returned None
Apr 02 00:10:50 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close PLTR failed
Apr 02 00:10:50 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: PLTR could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:10:50 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing LCID (decision_px=9.57, entry=9.61, hold=287.0min)
Apr 02 00:10:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LCID (attempt 1/3): close_position_api_once returned None
Apr 02 00:10:55 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LCID (attempt 2/3): close_position_api_once returned None
Apr 02 00:10:56 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:10:56,524 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 00:10:56 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:10:56,852 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 00:10:56 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:10:56,853 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 00:11:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LCID (attempt 3/3): close_position_api_once returned None
Apr 02 00:11:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close LCID failed
Apr 02 00:11:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: LCID could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:11:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing HOOD (decision_px=70.04, entry=70.15, hold=287.0min)
Apr 02 00:11:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HOOD (attempt 1/3): close_position_api_once returned None
Apr 02 00:11:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HOOD (attempt 2/3): close_position_api_once returned None
Apr 02 00:11:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 00:11:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 280 (iter_count=308)
Apr 02 00:11:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 309
Apr 02 00:11:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 00:11:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 00:11:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 00:11:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 00:11:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 00:11:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 00:11:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HOOD (attempt 3/3): close_position_api_once returned None
Apr 02 00:11:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close HOOD failed
Apr 02 00:11:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: HOOD could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:11:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing RIVN (decision_px=15.00, entry=15.01, hold=287.0min)
Apr 02 00:11:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close RIVN (attempt 1/3): close_position_api_once returned None
Apr 02 00:11:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 00:11:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 00:11:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close RIVN (attempt 2/3): close_position_api_once returned None
Apr 02 00:11:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close RIVN (attempt 3/3): close_position_api_once returned None
Apr 02 00:11:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close RIVN failed
Apr 02 00:11:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: RIVN could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:11:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing MRNA (decision_px=51.51, entry=50.10, hold=286.7min)
Apr 02 00:11:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MRNA (attempt 1/3): close_position_api_once returned None
Apr 02 00:11:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MRNA (attempt 2/3): close_position_api_once returned None
Apr 02 00:11:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MRNA (attempt 3/3): close_position_api_once returned None
Apr 02 00:11:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close MRNA failed
Apr 02 00:11:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: MRNA could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:11:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing MSFT (decision_px=369.87, entry=369.55, hold=286.9min)
Apr 02 00:11:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MSFT (attempt 1/3): close_position_api_once returned None
Apr 02 00:11:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MSFT (attempt 2/3): close_position_api_once returned None
Apr 02 00:11:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MSFT (attempt 3/3): close_position_api_once returned None
Apr 02 00:11:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close MSFT failed
Apr 02 00:11:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: MSFT could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:11:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing UNH (decision_px=274.55, entry=273.95, hold=286.4min)
Apr 02 00:11:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 00:11:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 00:11:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close UNH (attempt 1/3): close_position_api_once returned None
Apr 02 00:11:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close UNH (attempt 2/3): close_position_api_once returned None
Apr 02 00:11:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close UNH (attempt 3/3): close_position_api_once returned None
Apr 02 00:11:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close UNH failed
Apr 02 00:11:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: UNH could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:11:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing COP (decision_px=126.96, entry=128.33, hold=286.4min)
Apr 02 00:11:55 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close COP (attempt 1/3): close_position_api_once returned None
Apr 02 00:11:56 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:11:56,862 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 00:11:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:11:57,184 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 00:11:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:11:57,184 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 00:11:59 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close COP (attempt 2/3): close_position_api_once returned None
Apr 02 00:12:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close COP (attempt 3/3): close_position_api_once returned None
Apr 02 00:12:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close COP failed
Apr 02 00:12:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: COP could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:12:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing PFE (decision_px=28.05, entry=28.57, hold=286.4min)
Apr 02 00:12:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PF
```
