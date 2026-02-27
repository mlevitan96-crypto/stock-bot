# Paper restart proof (2026-02-18)

## After restart (no overlay)

### tmux ls
```
clawdbot: 1 windows (created Thu Jan 29 23:28:35 2026)
stock_bot_paper_run: 1 windows (created Wed Feb 18 18:58:46 2026)
trading: 1 windows (created Sat Dec 13 20:52:28 2025)
```

### tmux capture-pane (stock_bot_paper_run)
```
[CONFIG] Loaded theme_risk.json: ENABLE_THEME_RISK=True, MAX_THEME_NOTIONAL_USD=
$150,000
2026-02-18 18:58:50,475 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
[MOCK-SIGNAL] Mock signal injection loop started (every 15 minutes)
[MAIN] Mock signal injection loop started
DEBUG: Worker loop STARTED (thread 127351773058752)
DEBUG: SIMULATE_MARKET_OPEN=False, stop_evt.is_set()=False
DEBUG: Worker loop iteration 1 (iter_count=0)
DEBUG WORKER: Starting iteration 1
DEBUG WORKER: About to check market status...
======================================================================
  STARTUP CONTRACT CHECK
======================================================================
✅ Composite scoring smoke test passed (score: 2.111)
✅ V2 components present in scoring output
```

### state/live_paper_run_state.json
```
{
  "status": "live_paper_run_started",
  "timestamp": 1771441129,
  "details": {
    "trading_mode": "paper",
    "process": "python3 main.py",
    "session": "stock_bot_paper_run",
    "governed_tuning_config": ""
  }
}
```

- No GOVERNED_TUNING_CONFIG in tmux command
- governed_tuning_config empty in state