# RED_TEAM_REPORT — Off-Leash Alpaca Hunt

**Generated (UTC):** `2026-04-16T00:21:13Z`  
**Root:** `/root/stock-bot`  
**Schema:** `off_leash_alpaca_hunt_v1`  

## 1. Executive threats (machine-readable summary)

```json
{
  "json_decode_errors_total": 0,
  "journal_error_hits": 2327,
  "journal_warn_hits": 584,
  "journal_429_hits": 4
}
```

## 2. journalctl — stock-bot.service

```
{
  "unit": "stock-bot.service",
  "lines_requested": 8000,
  "ok": true,
  "stderr": "",
  "patterns": {},
  "exit_code": 0,
  "char_len": 1405800,
  "pattern_counts": {
    "ERROR": 2327,
    "ghost": 1742,
    "WARN": 584,
    "CRITICAL": 47,
    "SIP": 1,
    "429": 4
  },
  "pattern_samples": {
    "ERROR": [
      "Apr 15 22:12:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[797896]: [trading-bot] ERROR EXITS: Failed to close AMZN (attempt 1/3): close_position_api_once returned None",
      "Apr 15 22:12:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[797896]: [trading-bot] ERROR EXITS: Failed to close AMZN (attempt 2/3): close_position_api_once returned None",
      "Apr 15 22:12:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[797896]: [trading-bot] ERROR EXITS: Failed to close AMZN (attempt 3/3): close_position_api_once returned None",
      "Apr 15 22:12:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[797896]: [trading-bot] ERROR EXITS: All 3 attempts to close AMZN failed"
    ],
    "ghost": [
      "Apr 15 22:12:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[797896]: [trading-bot] ERROR EXITS: Failed to close AMZN (attempt 1/3): close_position_api_once returned None",
      "Apr 15 22:12:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[797896]: [trading-bot] ERROR EXITS: Failed to close AMZN (attempt 2/3): close_position_api_once returned None",
      "Apr 15 22:12:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[797896]: [trading-bot] ERROR EXITS: Failed to close AMZN (attempt 3/3): close_position_api_once returned None",
      "Apr 15 22:12:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[797896]: [trading-bot] ERROR EXITS: Failed to close MS (attempt 1/3): close_position_api_once returned None"
    ],
    "WARN": [
      "Apr 15 22:12:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[797896]: [trading-bot] WARNING EXITS: AMZN could not be verified as closed after 3 attempts - keeping in tracking for retry",
      "Apr 15 22:12:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[797896]: [trading-bot] WARNING EXITS: MS could not be verified as closed after 3 attempts - keeping in tracking for retry",
      "Apr 15 22:12:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[797896]: [trading-bot] WARNING EXITS: WMT could not be verified as closed after 3 attempts - keeping in tracking for retry",
      "Apr 15 22:12:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[797896]: [trading-bot] WARNING EXITS: BAC could not be verified as closed after 3 attempts - keeping in tracking for retry"
    ],
    "CRITICAL": [
      "Apr 15 22:16:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[797896]: [trading-bot] CRITICAL: Exit checker evaluate_exits() completed",
      "Apr 15 22:17:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[797896]: [trading-bot] CRITICAL: Exit checker calling evaluate_exits()",
      "Apr 15 22:22:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[797896]: [trading-bot] CRITICAL: Exit checker evaluate_exits() completed",
      "Apr 15 22:23:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[797896]: [trading-bot] CRITICAL: Exit checker calling evaluate_exits()"
    ],
    "SIP": [
      "Apr 15 23:00:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] 2026-04-15 23:00:22,402 [CACHE-ENRICH] INFO: signal_open_position: evaluated COP -> 3.6450"
    ],
    "429": [
      "Apr 15 23:28:59 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] 2026-04-15 23:28:59,429 [CACHE-ENRICH] INFO: signal_open_position: evaluated COIN -> 3.8900",
      "Apr 15 23:40:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] 2026-04-15 23:40:27,429 [CACHE-ENRICH] INFO: signal_open_position: evaluated SLB -> 3.2810",
      "Apr 15 23:49:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] 2026-04-15 23:49:53,429 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals",
      "Apr 15 23:49:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] 2026-04-15 23:49:53,429 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols"
    ]
  },
  "tail_preview": "lpaca systemd_start.sh[803396]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)\nApr 16 00:20:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] ERROR EXITS: Failed to close AMZN (attempt 3/3): close_position_api_once returned None\nApr 16 00:20:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] ERROR EXITS: All 3 attempts to close AMZN failed\nApr 16 00:20:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] WARNING EXITS: AMZN could not be verified as closed after 3 attempts - keeping in tracking for retry\nApr 16 00:20:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] DEBUG EXITS: Closing MS (decision_px=184.57, entry=192.12, hold=292.9min)\nApr 16 00:20:50 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] ERROR EXITS: Failed to close MS (attempt 1/3): close_position_api_once returned None\nApr 16 00:20:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] ERROR EXITS: Failed to close MS (attempt 2/3): close_position_api_once returned None\nApr 16 00:20:59 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] ERROR EXITS: Failed to close MS (attempt 3/3): close_position_api_once returned None\nApr 16 00:20:59 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] ERROR EXITS: All 3 attempts to close MS failed\nApr 16 00:20:59 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] WARNING EXITS: MS could not be verified as closed after 3 attempts - keeping in tracking for retry\nApr 16 00:20:59 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] DEBUG EXITS: Closing WMT (decision_px=124.96, entry=124.88, hold=273.4min)\nApr 16 00:21:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] ERROR EXITS: Failed to close WMT (attempt 1/3): close_position_api_once returned None\nApr 16 00:21:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] 2026-04-16 00:21:03,213 [CACHE-ENRICH] INFO: Starting cache enrichment cycle\nApr 16 00:21:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] 2026-04-16 00:21:03,518 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals\nApr 16 00:21:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] 2026-04-16 00:21:03,519 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols\nApr 16 00:21:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] ERROR EXITS: Failed to close WMT (attempt 2/3): close_position_api_once returned None\nApr 16 00:21:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] ERROR EXITS: Failed to close WMT (attempt 3/3): close_position_api_once returned None\nApr 16 00:21:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] ERROR EXITS: All 3 attempts to close WMT failed\nApr 16 00:21:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] WARNING EXITS: WMT could not be verified as closed after 3 attempts - keeping in tracking for retry\nApr 16 00:21:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] DEBUG EXITS: Closing BAC (decision_px=54.33, entry=54.19, hold=273.3min)\nApr 16 00:21:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).\nApr 16 00:21:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [heartbeat-keeper]   result[\"_dt\"] = datetime.utcnow().isoformat()\nApr 16 00:21:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[803396]: [trading-bot] ERROR EXITS: Failed to close BAC (attempt 1/3): close_position_api_once returned None\n"
}
```

## 3. Process memory / threads (main.py)

```json
{
  "pids": [
    "803472"
  ],
  "entries": [
    {
      "pid": "803472",
      "name": "python",
      "VmRSS": "413804 kB",
      "Threads": "16"
    }
  ],
  "note": null
}
```

## 4. SQLite probes (read-only)

```json
[]
```

## 5. JSONL corruption (tail scan)

```json
[
  {
    "path": "/root/stock-bot/logs/exit_attribution.jsonl",
    "label": "exit_attribution",
    "lines_attempted_approx": 2980,
    "json_ok": 2980,
    "json_decode_error": 0,
    "samples": []
  },
  {
    "path": "/root/stock-bot/logs/entry_snapshots.jsonl",
    "label": "entry_snapshots",
    "lines_attempted_approx": 2922,
    "json_ok": 2922,
    "json_decode_error": 0,
    "samples": []
  },
  {
    "path": "/root/stock-bot/logs/run.jsonl",
    "label": "run",
    "lines_attempted_approx": 2057,
    "json_ok": 2057,
    "json_decode_error": 0,
    "samples": []
  },
  {
    "path": "/root/stock-bot/logs/system_events.jsonl",
    "label": "system_events",
    "lines_attempted_approx": 5288,
    "json_ok": 5288,
    "json_decode_error": 0,
    "samples": []
  },
  {
    "path": "/root/stock-bot/logs/orders.jsonl",
    "label": "orders",
    "lines_attempted_approx": 4057,
    "json_ok": 4057,
    "json_decode_error": 0,
    "samples": []
  },
  {
    "path": "/root/stock-bot/logs/signal_context.jsonl",
    "label": "signal_context",
    "lines_attempted_approx": 0,
    "json_ok": 0,
    "json_decode_error": 0,
    "samples": []
  }
]
```

## 6. Keyword hunts — run.jsonl + system_events.jsonl (tails)

```json
[
  {
    "path": "/root/stock-bot/logs/run.jsonl",
    "hits": {
      "rate_limit": 86,
      "sip_stream": 0,
      "pdt": 0,
      "wash": 0,
      "order_none": 555,
      "polygon": 0,
      "alpaca_api": 0
    },
    "samples": {
      "rate_limit": [
        "{\"ts\": \"2026-04-15T18:27:34.998374+00:00\", \"msg\": \"complete\", \"clusters\": 52, \"orders\": 0, \"metrics\": {\"total_pnl\": 80.89, \"trades\": 502, \"win_rate\": 0.2410358565737052, \"market_regime\": \"mixed\", \"composite_enabled\": true, \"risk_metrics\": {\"current_equity\": 47162.32, \"peak_equity\": 47164.19, \"daily_pnl\": 73.01000000000204, \"drawdown_pct\": 0.003964872501791336, \"daily_loss_limit\": 2200, \"drawdown_l",
        "{\"ts\": \"2026-04-15T18:27:34.998525+00:00\", \"_ts\": 1776277654, \"msg\": \"complete\", \"clusters\": 52, \"orders\": 0, \"metrics\": {\"total_pnl\": 80.89, \"trades\": 502, \"win_rate\": 0.2410358565737052, \"market_regime\": \"mixed\", \"composite_enabled\": true, \"risk_metrics\": {\"current_equity\": 47162.32, \"peak_equity\": 47164.19, \"daily_pnl\": 73.01000000000204, \"drawdown_pct\": 0.003964872501791336, \"daily_loss_limit\"",
        "{\"ts\": \"2026-04-15T18:27:43.635092+00:00\", \"_ts\": 1776277663, \"msg\": \"complete\", \"clusters\": 52, \"orders\": 0, \"market_open\": true, \"engine_status\": \"ok\", \"errors_this_cycle\": [], \"metrics\": {\"clusters\": 52, \"orders\": 0, \"equity_orders\": 0, \"total_pnl\": 80.89, \"trades\": 502, \"win_rate\": 0.2410358565737052, \"market_regime\": \"mixed\", \"composite_enabled\": true, \"risk_metrics\": {\"current_equity\": 47162"
      ],
      "order_none": [
        "{\"ts\": \"2026-04-15T18:34:37.227479+00:00\", \"event_type\": \"canonical_trade_id_resolved\", \"symbol\": \"AMD\", \"canonical_trade_id_intent\": \"BLOCKED|AMD|e39896af-cfd6-44a9-b4d8-15049063118a\", \"canonical_trade_id_fill\": \"AMD|LONG|1776276242\", \"decision_event_id\": \"e39896af-cfd6-44a9-b4d8-15049063118a\", \"symbol_normalized\": \"AMD\", \"time_bucket_id\": \"300s|1776277800\", \"close_truth_chain_reason\": \"close_pos",
        "{\"ts\": \"2026-04-15T18:34:37.228268+00:00\", \"event_type\": \"canonical_trade_id_resolved\", \"symbol\": \"AMD\", \"canonical_trade_id_intent\": \"AMD|LONG|1776276242\", \"canonical_trade_id_fill\": \"AMD|SHORT|1776276242\", \"decision_event_id\": \"e39896af-cfd6-44a9-b4d8-15049063118a\", \"symbol_normalized\": \"AMD\", \"time_bucket_id\": \"300s|1776277800\", \"close_truth_chain_reason\": \"close_position_api_once\", \"strategy_i",
        "{\"ts\": \"2026-04-15T18:34:37.228351+00:00\", \"event_type\": \"entry_decision_made\", \"entry_intent_synthetic\": false, \"entry_intent_source\": \"live_runtime\", \"entry_intent_status\": \"OK\", \"entry_intent_error\": null, \"symbol\": \"AMD\", \"side\": \"buy\", \"canonical_trade_id\": \"AMD|LONG|1776276242\", \"trade_id\": \"open_AMD_2026-04-15T18:04:02.265353+00:00\", \"trade_key\": \"AMD|LONG|1776276242\", \"decision_event_id\": "
      ]
    }
  },
  {
    "path": "/root/stock-bot/logs/system_events.jsonl",
    "hits": {
      "rate_limit": 56,
      "sip_stream": 0,
      "pdt": 0,
      "wash": 0,
      "order_none": 3775,
      "polygon": 0,
      "alpaca_api": 1840
    },
    "samples": {
      "order_none": [
        "{\"timestamp\": \"2026-04-15T23:37:07.067589+00:00\", \"subsystem\": \"exit\", \"event_type\": \"close_position_not_verified\", \"severity\": \"INFO\", \"details\": {\"symbol\": \"COP\", \"attempts\": 3}, \"symbol\": \"COP\"}",
        "{\"timestamp\": \"2026-04-15T23:37:07.086606+00:00\", \"subsystem\": \"exit\", \"event_type\": \"exception\", \"severity\": \"ERROR\", \"details\": {\"function\": \"close_position_api_once\", \"attempt\": 1, \"max_attempts\": 3, \"error\": \"insufficient qty available for order (requested: 46, available: 0)\", \"traceback\": \"Traceback (most recent call last):\\n  File \\\"/root/stock-bot/utils/system_events.py\\\", line 166, in _wra",
        "{\"timestamp\": \"2026-04-15T23:37:07.601769+00:00\", \"subsystem\": \"exit\", \"event_type\": \"exception\", \"severity\": \"ERROR\", \"details\": {\"function\": \"close_position_api_once\", \"attempt\": 2, \"max_attempts\": 3, \"error\": \"insufficient qty available for order (requested: 46, available: 0)\", \"traceback\": \"Traceback (most recent call last):\\n  File \\\"/root/stock-bot/utils/system_events.py\\\", line 166, in _wra"
      ],
      "alpaca_api": [
        "{\"timestamp\": \"2026-04-15T23:37:07.086606+00:00\", \"subsystem\": \"exit\", \"event_type\": \"exception\", \"severity\": \"ERROR\", \"details\": {\"function\": \"close_position_api_once\", \"attempt\": 1, \"max_attempts\": 3, \"error\": \"insufficient qty available for order (requested: 46, available: 0)\", \"traceback\": \"Traceback (most recent call last):\\n  File \\\"/root/stock-bot/utils/system_events.py\\\", line 166, in _wra",
        "{\"timestamp\": \"2026-04-15T23:37:07.601769+00:00\", \"subsystem\": \"exit\", \"event_type\": \"exception\", \"severity\": \"ERROR\", \"details\": {\"function\": \"close_position_api_once\", \"attempt\": 2, \"max_attempts\": 3, \"error\": \"insufficient qty available for order (requested: 46, available: 0)\", \"traceback\": \"Traceback (most recent call last):\\n  File \\\"/root/stock-bot/utils/system_events.py\\\", line 166, in _wra",
        "{\"timestamp\": \"2026-04-15T23:37:08.619776+00:00\", \"subsystem\": \"exit\", \"event_type\": \"exception\", \"severity\": \"CRITICAL\", \"details\": {\"function\": \"close_position_api_once\", \"attempt\": 3, \"max_attempts\": 3, \"error\": \"insufficient qty available for order (requested: 46, available: 0)\", \"traceback\": \"Traceback (most recent call last):\\n  File \\\"/root/stock-bot/utils/system_events.py\\\", line 166, in _"
      ],
      "rate_limit": [
        "{\"timestamp\": \"2026-04-15T23:39:18.591429+00:00\", \"subsystem\": \"exit\", \"event_type\": \"exception\", \"severity\": \"ERROR\", \"details\": {\"function\": \"close_position_api_once\", \"attempt\": 1, \"max_attempts\": 3, \"error\": \"insufficient qty available for order (requested: 1, available: 0)\", \"traceback\": \"Traceback (most recent call last):\\n  File \\\"/root/stock-bot/utils/system_events.py\\\", line 166, in _wrap",
        "{\"timestamp\": \"2026-04-15T23:40:02.184499+00:00\", \"subsystem\": \"uw\", \"event_type\": \"uw_rate_limit_block\", \"severity\": \"WARN\", \"details\": {\"reason\": \"daily_cap\", \"endpoint\": \"/api/option-trades/flow-alerts\", \"params\": {\"symbol\": \"SPY\", \"limit\": 10}, \"wait_s\": null}}",
        "{\"timestamp\": \"2026-04-15T23:40:02.184676+00:00\", \"subsystem\": \"uw_health_probe\", \"event_type\": \"uw_api_schema_or_transport_failure\", \"severity\": \"ERROR\", \"details\": {\"reason\": \"http_non_success\", \"endpoint\": \"/api/option-trades/flow-alerts\", \"http_status\": 429}, \"symbol\": \"SPY\"}"
      ]
    }
  }
]
```

## 7. Board triage prompts (unconstrained)

- Any non-zero `json_decode_error` in canonical logs is telemetry integrity debt: treat as P0 until explained.
- Journal `ghost` / `close_position` samples: execution path may be losing broker confirmation while UI still shows risk.
- 429 / rate_limit clusters: external API budget or retry storm; correlate with UW and Alpaca REST.
- PDT / wash hits in logs: compliance surfacing; verify operator visibility and block reason propagation.
- SIP / stream / CRITICAL_DATA_STALE: market-data contract breach; session-edge entries are NO-GO per governance.

---
*End of automated hunt. Human red team: correlate timestamps across journal + run.jsonl + exit_attribution.*
