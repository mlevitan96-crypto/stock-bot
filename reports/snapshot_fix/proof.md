# Snapshot fix — proof (droplet)

**Note:** Fix commit is `0060af4` (Fix: ensure score snapshot emission). If droplet shows older commit, run `git pull --rebase origin main` again in repo root. Market was closed during this run — snapshot hook only runs during scoring cycles (market open); confirm again in the morning.

## Deploy
- Commit at capture: `e5edde4035a9` (verify with `git rev-parse HEAD` after pull)

## Commands run
- `git pull --rebase origin main`
- `tmux new-session -d -s stock_bot_paper_run 'cd /root/stock-bot && SCORE_SNAPSHOT_DEBUG=1 LOG_LEVEL=INFO python3 main.py'`
- Wait ~90s then capture pane, wc -l, head -1

## tmux capture-pane (stock_bot_paper_run, last 200 lines)
```
[CONFIG] Loaded theme_risk.json: ENABLE_THEME_RISK=True, MAX_THEME_NOTIONAL_USD=
$150,000
2026-02-18 23:49:07,818 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
[MOCK-SIGNAL] Mock signal injection loop started (every 15 minutes)
[MAIN] Mock signal injection loop started
DEBUG: Worker loop STARTED (thread 136687847454400)
DEBUG: SIMULATE_MARKET_OPEN=False, stop_evt.is_set()=False
DEBUG: Worker loop iteration 1 (iter_count=0)
DEBUG WORKER: Starting iteration 1
DEBUG WORKER: About to check market status...
======================================================================
  STARTUP CONTRACT CHECK
======================================================================
DEBUG WORKER: is_market_open_now() returned: False
DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
✅ Composite scoring smoke test passed (score: 2.111)
✅ V2 components present in scoring output
DEBUG WORKER: After market check, market_open=False, about to check if block...
DEBUG: Market is CLOSED - skipping trading
/root/stock-bot/main.py:11527: DeprecationWarning: datetime.datetime.utcnow() is
 deprecated and scheduled for removal in a future version. Use timezone-aware ob
jects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  day = datetime.utcnow().strftime("%Y-%m-%d")
✅ Live cache smoke test passed (PFE: 8.000)

----------------------------------------------------------------------
⚠️   Warnings (1):
   Contract validator not available: No module named 'internal_contract_validato
r'

======================================================================
  ✅ STARTUP CHECK PASSED - READY TO TRADE
======================================================================
/root/stock-bot/main.py:13306: DeprecationWarning: datetime.datetime.utcnow() is
 deprecated and scheduled for removal in a future version. Use timezone-aware ob
jects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  reconcile_event["_dt"] = datetime.utcnow().isoformat() + "Z"
CRITICAL: Exit checker thread STARTED
CRITICAL: Exit checker thread started
Starting Flask server on port 8080...
 * Serving Flask app 'main'
 * Debug mode: off
2026-02-18 23:49:09,113 [CACHE-ENRICH] INFO: WARNING: This is a development serv
er. Do not use it in a production deployment. Use a production WSGI server inste
ad.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8080
 * Running on http://104.236.102.57:8080
2026-02-18 23:49:09,126 [CACHE-ENRICH] INFO: Press CTRL+C to quit
2026-02-18 23:49:10,805 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with
 computed signals
2026-02-18 23:49:10,806 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbo
ls
/root/stock-bot/main.py:11664: DeprecationWarning: datetime.datetime.utcnow() is
 deprecated and scheduled for removal in a future version. Use timezone-aware ob
jects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  "last_heartbeat_dt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
/root/stock-bot/main.py:11668: DeprecationWarning: datetime.datetime.utcnow() is
 deprecated and scheduled for removal in a future version. Use timezone-aware ob
jects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  "last_attempt_dt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
DEBUG: Heartbeat file OK: state/bot_heartbeat.json (iter 0)
DEBUG: Worker sleeping for 1.1s (target=5.0s, elapsed=3.9s)
DEBUG: Worker woke up, stop_evt.is_set()=False
DEBUG: Worker loop iteration 2 (iter_count=0)
DEBUG WORKER: Starting iteration 1
DEBUG WORKER: About to check market status...
DEBUG WORKER: is_market_open_now() returned: False
DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
DEBUG WORKER: After market check, market_open=False, about to check if block...
DEBUG: Market is CLOSED - skipping trading
DEBUG: Worker sleeping for 59.7s (target=60.0s, elapsed=0.3s)
[CONFIG] Loaded theme_risk.json: ENABLE_THEME_RISK=True, MAX_THEME_NOTIONAL_USD=
$150,000
2026-02-18 23:50:07,819 [CACHE-ENRICH] INFO: Starting self-healing cycle
2026-02-18 23:50:08,286 [CACHE-ENRICH] INFO: No issues detected - system healthy
✅ DIAGNOSTIC: Alpaca API connected - Buying Power: $99,322.96, Equity: $49,661.
48
CRITICAL: Exit checker calling evaluate_exits()
/root/stock-bot/main.py:6175: DeprecationWarning: datetime.datetime.utcnow() is
deprecated and scheduled for removal in a future version. Use timezone-aware obj
ects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  now = datetime.utcnow()
CRITICAL: Exit checker evaluate_exits() completed
2026-02-18 23:50:10,824 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
2026-02-18 23:50:11,294 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with
 computed signals
2026-02-18 23:50:11,294 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbo
ls
DEBUG: Worker woke up, stop_evt.is_set()=False
DEBUG: Worker loop iteration 3 (iter_count=1)
DEBUG WORKER: Starting iteration 2
DEBUG WORKER: About to check market status...
DEBUG WORKER: is_market_open_now() returned: False
DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
DEBUG WORKER: After market check, market_open=False, about to check if block...
DEBUG: Market is CLOSED - skipping trading
DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
```

## logs/score_snapshot.jsonl
```
# wc -l
0 logs/score_snapshot.jsonl

# ls -la
file missing

# head -1

```

## Result
- snapshot_count: **0**
- composite_score in first record: (see head -1 above)
- Hook + write success logs: (see capture-pane for SCORE_SNAPSHOT_DEBUG lines)
- **PASS** if snapshot_count > 0 and composite_score present; **PENDING** if market closed (0 clusters).