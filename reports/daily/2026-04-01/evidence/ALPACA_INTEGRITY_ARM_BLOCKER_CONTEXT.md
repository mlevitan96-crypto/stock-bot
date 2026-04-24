# ALPACA_INTEGRITY_ARM_BLOCKER_CONTEXT

- **ET date (folder):** `2026-04-01`
- **git HEAD:** `27e4f8bcc9dd2450aa8eb802ee78529de1cf69d2`
- **UTC now:** `2026-04-01 16:58:09 UTC`

## systemctl status stock-bot

```
● stock-bot.service - Algorithmic Trading Bot
     Loaded: loaded (/etc/systemd/system/stock-bot.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/stock-bot.service.d
             └─override.conf, paper-overlay.conf, truth.conf
     Active: active (running) since Tue 2026-03-31 21:11:35 UTC; 19h ago
   Main PID: 1807948 (systemd_start.s)
      Tasks: 32 (limit: 9483)
     Memory: 897.3M (peak: 915.8M)
        CPU: 1h 8min 25.172s
     CGroup: /system.slice/stock-bot.service
             ├─1807948 /bin/bash /root/stock-bot/systemd_start.sh
             ├─1807950 /root/stock-bot/venv/bin/python deploy_supervisor.py
             ├─1807960 /root/stock-bot/venv/bin/python -u dashboard.py
             ├─1808026 /root/stock-bot/venv/bin/python -u main.py
             └─1808043 /root/stock-bot/venv/bin/python heartbeat_keeper.py

Apr 01 16:58:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1807950]: [trading-bot] 2026-04-01 16:58:06,206 [CACHE-ENRICH] WARNING: Trade rejected: V buy 1 - portfolio_exposure_exceeds_limit_31.09%_max_30.00%
Apr 01 16:58:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1807950]: [trading-bot] DEBUG V: submit_entry completed - res=False, order_type=trade_guard_blocked, entry_status=portfolio_exposure_exceeds_limit_31.09%_max_30.00%, filled_qty=0
Apr 01 16:58:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1807950]: [trading-bot] DEBUG V: submit_entry returned None - order submission failed (order_type=trade_guard_blocked, entry_status=portfolio_exposure_exceeds_limit_31.09%_max_30.00%)
Apr 01 16:58:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1807950]: [trading-bot] DEBUG BAC: Processing cluster - direction=bullish, initial_score=4.61, source=composite_v3
Apr 01 16:58:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1807950]: [trading-bot] 2026-04-01 16:58:06,274 [CACHE-ENRICH] WARNING: sleep 3 seconds and retrying https://paper-api.alpaca.markets/v2/positions 3 more time(s)...
Apr 01 16:58:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1807950]: [trading-bot] DEBUG MA: Processing cluster - direction=bullish, initial_score=4.59, source=composite_v3
Apr 01 16:58:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1807950]: [trading-bot] DEBUG MA: expectancy=0.4079, should_trade=True, reason=expectancy_passed
Apr 01 16:58:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1807950]: [trading-bot] DEBUG MA: PASSED expectancy gate, checking other gates...
Apr 01 16:58:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1807950]: [trading-bot] DEBUG MA: PASSED ALL GATES! Calling submit_entry...
Apr 01 16:58:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1807950]: [trading-bot] DEBUG MA: Side determined: buy, qty=1, ref_price=497.565

```

## systemctl status alpaca-telegram-integrity.timer

```
● alpaca-telegram-integrity.timer - Every 10 minutes — Alpaca Telegram integrity cycle
     Loaded: loaded (/etc/systemd/system/alpaca-telegram-integrity.timer; enabled; preset: enabled)
     Active: active (waiting) since Mon 2026-03-30 17:04:29 UTC; 1 day 23h ago
    Trigger: Wed 2026-04-01 16:59:50 UTC; 1min 40s left
   Triggers: ● alpaca-telegram-integrity.service

Notice: journal has been rotated since unit was started, output may be incomplete.

```

## systemctl status alpaca-telegram-integrity.service

```
○ alpaca-telegram-integrity.service - Alpaca Telegram + data integrity cycle (milestone 250, coverage, strict gate)
     Loaded: loaded (/etc/systemd/system/alpaca-telegram-integrity.service; disabled; preset: enabled)
     Active: inactive (dead) since Wed 2026-04-01 16:49:57 UTC; 8min ago
TriggeredBy: ● alpaca-telegram-integrity.timer
    Process: 1839629 ExecStart=/root/stock-bot/venv/bin/python3 /root/stock-bot/scripts/run_alpaca_telegram_integrity_cycle.py (code=exited, status=0/SUCCESS)
   Main PID: 1839629 (code=exited, status=0/SUCCESS)
        CPU: 7.144s

Apr 01 16:49:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1839629]:     "arm_epoch_utc": null,
Apr 01 16:49:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1839629]:     "armed_at_utc_iso": null,
Apr 01 16:49:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1839629]:     "session_anchor_et": "2026-04-01"
Apr 01 16:49:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1839629]:   },
Apr 01 16:49:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1839629]:   "checkpoint_100_guard_file": "/root/stock-bot/state/alpaca_100trade_sent.json",
Apr 01 16:49:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1839629]:   "reasons_evaluated": []
Apr 01 16:49:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1839629]: }
Apr 01 16:49:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: alpaca-telegram-integrity.service: Deactivated successfully.
Apr 01 16:49:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Finished alpaca-telegram-integrity.service - Alpaca Telegram + data integrity cycle (milestone 250, coverage, strict gate).
Apr 01 16:49:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: alpaca-telegram-integrity.service: Consumed 7.144s CPU time.

```

## ls -lah state/ (first 200 lines)

```
total 56M
drwxr-xr-x  5 root root 4.0K Apr  1 16:58 .
drwxr-xr-x 47 root root  48K Mar 31 21:11 ..
-rw-r--r--  1 root root  137 Apr  1 16:49 alpaca_100trade_sent.json
-rw-r--r--  1 root root   87 Apr  1 16:49 alpaca_milestone_250_state.json
-rw-r--r--  1 root root   93 Apr  1 16:49 alpaca_milestone_integrity_arm.json
-rw-r--r--  1 root root 6.9K Apr  1 16:57 alpaca_positions.json
-rw-r--r--  1 root root  520 Apr  1 16:49 alpaca_telegram_integrity_cycle.json
-rw-r--r--  1 root root  119 Mar 30 17:36 bayes_profiles.json
-rw-r--r--  1 root root  44M Apr  1 16:58 blocked_trades.jsonl
-rw-r--r--  1 root root  938 Apr  1 16:57 bot_heartbeat.json
-rw-r--r--  1 root root 3.9M Apr  1 00:12 causal_analysis_state.json
-rw-r--r--  1 root root  130 Mar 30 17:36 champions.json
-rw-r--r--  1 root root   93 Mar 30 17:36 correlation_snapshot.json
-rw-r--r--  1 root root   98 Apr  1 13:30 daily_start_equity.json
-rw-r--r--  1 root root   64 Mar 30 17:36 degraded_mode.json
-rw-r--r--  1 root root  222 Apr  1 16:39 direction_readiness.json
-rw-r--r--  1 root root  110 Mar 31 16:38 direction_replay_status.json
-rw-r--r--  1 root root  699 Mar 30 17:36 eod_rolling_windows_2026-03-30.json
-rw-r--r--  1 root root 9.5K Mar 31 19:55 execution_failures.jsonl
-rw-r--r--  1 root root 6.4K Apr  1 16:57 executor_state.json
-rw-r--r--  1 root root   42 Apr  1 16:57 fail_counter.json
-rw-r--r--  1 root root 4.2K Apr  1 02:00 failure_point_monitor.json
-rw-r--r--  1 root root 8.2K Apr  1 00:12 gate_pattern_learning.json
-rw-r--r--  1 root root  402 Mar 30 18:26 governor_freezes.json
-rw-r--r--  1 root root 4.8K Apr  1 13:03 healing_history.jsonl
-rw-r--r--  1 root root 1.7K Apr  1 16:57 health.json
drwxr-xr-x  2 root root 4.0K Mar 30 17:30 heartbeats
-rw-r--r--  1 root root 9.0K Apr  1 16:57 internal_positions.json
-rw-r--r--  1 root root  119 Mar 31 16:38 last_droplet_analysis.json
-rw-r--r--  1 root root 5.7K Apr  1 16:57 last_scores.json
-rw-r--r--  1 root root  750 Apr  1 00:12 learning_processing_state.json
-rw-r--r--  1 root root  150 Mar 31 20:46 learning_scheduler_state.json
drwxr-xr-x  3 root root 4.0K Mar 30 20:43 legacy
-rw-r--r--  1 root root  202 Apr  1 16:56 logic_stagnation_state.json
-rw-r--r--  1 root root  107 Mar 30 17:43 macro_gate_state.json
-rw-r--r--  1 root root  588 Apr  1 16:57 market_context_v2.json
-rw-------  1 root root  453 Mar 31 19:57 peak_equity.json
-rw-r--r--  1 root root  523 Apr  1 16:48 pending_fill_scores.json
-rw-r--r--  1 root root 6.3M Apr  1 16:57 portfolio_state.jsonl
-rw-r--r--  1 root root 1.2M Apr  1 16:48 position_intel_snapshots.json
-rw-r--r--  1 root root  93K Apr  1 16:57 position_metadata.json
-rw-r--r--  1 root root  12K Mar 30 18:26 position_metadata.pre_liquidation.20260330_182621Z.json
-rw-r--r--  1 root root  86K Mar 30 18:31 position_metadata.pre_liquidation.20260330_183111Z.json
-rw-r--r--  1 root root  11K Mar 30 18:32 position_metadata.pre_liquidation.20260330_183223Z.json
-rw-r--r--  1 root root  220 Mar 31 04:27 postclose_watermark.json
-rw-r--r--  1 root root  122 Apr  1 16:30 regime_detector_state.json
-rw-r--r--  1 root root  625 Apr  1 16:57 regime_posture_state.json
-rw-r--r--  1 root root 4.8K Mar 30 17:43 score_telemetry.json
-rw-r--r--  1 root root  30K Apr  1 16:57 sector_tide_state.json
-rw-r--r--  1 root root  133 Apr  1 15:56 self_healing_threshold.json
-rw-r--r--  1 root root 3.6K Mar 30 17:36 signal_correlation_cache.json
-rw-r--r--  1 root root  134 Apr  1 16:58 signal_funnel_state.json
-rw-r--r--  1 root root  26K Apr  1 16:58 signal_history.jsonl
-rw-r--r--  1 root root  102 Apr  1 00:12 signal_pattern_learning.json
-rw-r--r--  1 root root  17K Apr  1 16:57 signal_strength_cache.json
-rw-r--r--  1 root root   63 Mar 30 17:36 signal_survivorship_2026-03-30.json
-rw-r--r--  1 root root 200K Apr  1 02:00 signal_weights.json
-rw-r--r--  1 root root  30K Apr  1 16:56 smart_poller.json
-rw-r--r--  1 root root  269 Apr  1 16:57 sre_metrics.json
-rw-r--r--  1 root root  124 Mar 30 17:36 survivorship_adjustments.json
-rw-r--r--  1 root root 9.1K Apr  1 13:30 symbol_risk_features.json
-rw-r--r--  1 root root  309 Mar 30 17:36 system_stage.json
-rw-r--r--  1 root root 7.8K Apr  1 16:48 trading_state.json
-rw-r--r--  1 root root 4.7K Apr  1 00:12 uw_blocked_learning.json
drwxr-xr-x  2 root root  68K Apr  1 16:56 uw_cache
-rw-r--r--  1 root root   96 Mar 30 17:36 uw_flow_daemon.lock
-rw-r--r--  1 root root  45K Mar 30 17:31 uw_openapi_catalog.json
-rw-r--r--  1 root root  474 Apr  1 16:56 uw_usage_state.json
-rw-r--r--  1 root root  985 Mar 31 21:11 v2_metrics.json
-rw-r--r--  1 root root   97 Mar 31 21:11 v2_promoted.json

```
