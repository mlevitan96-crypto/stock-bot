# ALPACA_INTEGRITY_ARM_EXECUTION_TRACE

## journalctl alpaca-telegram-integrity.service (last ~400 lines / 36h)
- **journalctl rc:** 0

```
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:   },
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:   "coverage_file": "/root/stock-bot/reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_20260401_1549.md",
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:   "coverage_age_hours": 0.17,
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:   "strict": {
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     "LEARNING_STATUS": "BLOCKED",
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     "trades_seen": 60,
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     "trades_incomplete": 60
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:   },
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:   "exit_probe": {
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     "lines_scanned": 291,
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     "missing": {
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:       "symbol": 0,
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:       "exit_ts": 0,
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:       "trade_id": 0
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     }
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:   },
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:   "pager_windows": [
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     {
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:       "key": "alpaca:post_close",
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:       "state": "PENDING",
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:       "cause": "before_expect_window"
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     },
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     {
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:       "key": "alpaca:direction_readiness",
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:       "state": "PASS",
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:       "cause": "freshness_ok"
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     }
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:   ],
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:   "checkpoint_100_precheck_ok": false,
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:   "checkpoint_100_precheck_reasons": [
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     "DATA_READY not YES (or unknown)",
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     "strict LEARNING_STATUS is not ARMED (got 'BLOCKED')"
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:   ],
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:   "milestone": {
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     "session_open_utc_iso": "2026-04-01T13:30:00+00:00",
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     "session_anchor_et": "2026-04-01",
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     "unique_closed_trades": 0,
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     "realized_pnl_sum_usd": 0.0,
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     "sample_trade_keys": [],
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     "counting_basis": "integrity_armed",
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     "count_floor_utc_iso": "(not armed \u2014 waiting for green DATA_READY + coverage + strict ARMED + exit probe)",
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     "integrity_armed": false
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:   },
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:   "milestone_counting_basis": "integrity_armed",
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:   "milestone_integrity_arm": {
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     "arm_epoch_utc": null,
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     "armed_at_utc_iso": null,
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:     "session_anchor_et": "2026-04-01"
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:   },
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:   "checkpoint_100_guard_file": "/root/stock-bot/state/alpaca_100trade_sent.json",
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]:   "reasons_evaluated": []
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837751]: }
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: alpaca-telegram-integrity.service: Deactivated successfully.
Apr 01 15:59:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Finished alpaca-telegram-integrity.service - Alpaca Telegram + data integrity cycle (milestone 250, coverage, strict gate).
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: alpaca-telegram-integrity.service: Ignoring invalid environment assignment 'export TELEGRAM_BOT_TOKEN=8756383108:AAGnhPRMkbdYprVSsymA3Z0J4dD4F_M2PaE': /root/.alpaca_env
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: alpaca-telegram-integrity.service: Ignoring invalid environment assignment 'export TELEGRAM_CHAT_ID=5532204825': /root/.alpaca_env
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Starting alpaca-telegram-integrity.service - Alpaca Telegram + data integrity cycle (milestone 250, coverage, strict gate)...
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]: {
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   "root": "/root/stock-bot",
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   "utc": "2026-04-01T16:09:48.727818+00:00",
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   "self_heal": {
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     "mkdirs": [
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:       "logs",
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:       "state",
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:       "reports",
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:       "reports/daily"
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     ],
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     "postclose": "postclose_not_failed"
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   },
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   "coverage_file": "/root/stock-bot/reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_20260401_1549.md",
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   "coverage_age_hours": 0.33,
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   "strict": {
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     "LEARNING_STATUS": "BLOCKED",
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     "trades_seen": 61,
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     "trades_incomplete": 61
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   },
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   "exit_probe": {
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     "lines_scanned": 292,
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     "missing": {
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:       "symbol": 0,
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:       "exit_ts": 0,
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:       "trade_id": 0
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     }
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   },
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   "pager_windows": [
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     {
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:       "key": "alpaca:post_close",
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:       "state": "PENDING",
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:       "cause": "before_expect_window"
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     },
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     {
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:       "key": "alpaca:direction_readiness",
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:       "state": "PASS",
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:       "cause": "freshness_ok"
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     }
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   ],
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   "checkpoint_100_precheck_ok": false,
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   "checkpoint_100_precheck_reasons": [
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     "DATA_READY not YES (or unknown)",
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     "strict LEARNING_STATUS is not ARMED (got 'BLOCKED')"
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   ],
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   "milestone": {
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     "session_open_utc_iso": "2026-04-01T13:30:00+00:00",
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     "session_anchor_et": "2026-04-01",
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     "unique_closed_trades": 0,
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     "realized_pnl_sum_usd": 0.0,
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     "sample_trade_keys": [],
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     "counting_basis": "integrity_armed",
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     "count_floor_utc_iso": "(not armed \u2014 waiting for green DATA_READY + coverage + strict ARMED + exit probe)",
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     "integrity_armed": false
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   },
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   "milestone_counting_basis": "integrity_armed",
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   "milestone_integrity_arm": {
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     "arm_epoch_utc": null,
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     "armed_at_utc_iso": null,
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:     "session_anchor_et": "2026-04-01"
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   },
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   "checkpoint_100_guard_file": "/root/stock-bot/state/alpaca_100trade_sent.json",
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]:   "reasons_evaluated": []
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1837981]: }
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: alpaca-telegram-integrity.service: Deactivated successfully.
Apr 01 16:09:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Finished alpaca-telegram-integrity.service - Alpaca Telegram + data integrity cycle (milestone 250, coverage, strict gate).
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: alpaca-telegram-integrity.service: Ignoring invalid environment assignment 'export TELEGRAM_BOT_TOKEN=8756383108:AAGnhPRMkbdYprVSsymA3Z0J4dD4F_M2PaE': /root/.alpaca_env
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: alpaca-telegram-integrity.service: Ignoring invalid environment assignment 'export TELEGRAM_CHAT_ID=5532204825': /root/.alpaca_env
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Starting alpaca-telegram-integrity.service - Alpaca Telegram + data integrity cycle (milestone 250, coverage, strict gate)...
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]: {
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:   "root": "/root/stock-bot",
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:   "utc": "2026-04-01T16:19:49.425671+00:00",
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:   "self_heal": {
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:     "mkdirs": [
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:       "logs",
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:       "state",
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:       "reports",
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:       "reports/daily"
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:     ],
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:     "postclose": "postclose_not_failed"
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:   },
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:   "coverage_file": "/root/stock-bot/reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_20260401_1549.md",
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:   "coverage_age_hours": 0.5,
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:   "strict": {
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:     "LEARNING_STATUS": "BLOCKED",
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:     "trades_seen": 61,
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:     "trades_incomplete": 61
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:   },
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:   "exit_probe": {
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:     "lines_scanned": 292,
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:     "missing": {
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:       "symbol": 0,
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:       "exit_ts": 0,
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:       "trade_id": 0
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:     }
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:   },
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:   "pager_windows": [
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:     {
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:       "key": "alpaca:post_close",
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:       "state": "PENDING",
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:       "cause": "before_expect_window"
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:     },
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:     {
Apr 01 16:19:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1838249]:       "key": "alpaca:direction_readiness",
Apr 01 16
```

## journalctl stock-bot filtered (integrity keywords, last ~120)
- **rc:** 0

```
(empty or rg missing)
```

## logs/alpaca_telegram_integrity.log (tail 80)

```
2026-04-01T03:39:18Z cycle_ok milestone_count=0
2026-04-01T03:49:18Z cycle_ok milestone_count=0
2026-04-01T03:59:18Z cycle_ok milestone_count=0
2026-04-01T04:09:19Z cycle_ok milestone_count=0
2026-04-01T04:19:19Z cycle_ok milestone_count=0
2026-04-01T04:29:20Z cycle_ok milestone_count=0
2026-04-01T04:39:20Z cycle_ok milestone_count=0
2026-04-01T04:49:20Z cycle_ok milestone_count=0
2026-04-01T04:59:21Z cycle_ok milestone_count=0
2026-04-01T05:09:21Z cycle_ok milestone_count=0
2026-04-01T05:19:21Z cycle_ok milestone_count=0
2026-04-01T05:29:22Z cycle_ok milestone_count=0
2026-04-01T05:39:22Z cycle_ok milestone_count=0
2026-04-01T05:49:23Z cycle_ok milestone_count=0
2026-04-01T05:59:23Z cycle_ok milestone_count=0
2026-04-01T06:09:24Z cycle_ok milestone_count=0
2026-04-01T06:19:24Z cycle_ok milestone_count=0
2026-04-01T06:29:24Z cycle_ok milestone_count=0
2026-04-01T06:39:25Z cycle_ok milestone_count=0
2026-04-01T06:49:25Z cycle_ok milestone_count=0
2026-04-01T06:59:26Z cycle_ok milestone_count=0
2026-04-01T07:09:26Z cycle_ok milestone_count=0
2026-04-01T07:19:27Z cycle_ok milestone_count=0
2026-04-01T07:29:27Z cycle_ok milestone_count=0
2026-04-01T07:39:27Z cycle_ok milestone_count=0
2026-04-01T07:49:28Z cycle_ok milestone_count=0
2026-04-01T07:59:28Z cycle_ok milestone_count=0
2026-04-01T08:09:28Z cycle_ok milestone_count=0
2026-04-01T08:19:29Z cycle_ok milestone_count=0
2026-04-01T08:29:29Z cycle_ok milestone_count=0
2026-04-01T08:39:30Z cycle_ok milestone_count=0
2026-04-01T08:49:30Z cycle_ok milestone_count=0
2026-04-01T08:59:31Z cycle_ok milestone_count=0
2026-04-01T09:09:31Z cycle_ok milestone_count=0
2026-04-01T09:19:32Z cycle_ok milestone_count=0
2026-04-01T09:29:32Z cycle_ok milestone_count=0
2026-04-01T09:39:32Z cycle_ok milestone_count=0
2026-04-01T09:49:33Z cycle_ok milestone_count=0
2026-04-01T09:59:33Z cycle_ok milestone_count=0
2026-04-01T10:09:33Z cycle_ok milestone_count=0
2026-04-01T10:19:34Z cycle_ok milestone_count=0
2026-04-01T10:29:34Z cycle_ok milestone_count=0
2026-04-01T10:39:35Z cycle_ok milestone_count=0
2026-04-01T10:49:35Z cycle_ok milestone_count=0
2026-04-01T10:59:35Z cycle_ok milestone_count=0
2026-04-01T11:09:36Z cycle_ok milestone_count=0
2026-04-01T11:19:36Z cycle_ok milestone_count=0
2026-04-01T11:29:37Z cycle_ok milestone_count=0
2026-04-01T11:39:37Z cycle_ok milestone_count=0
2026-04-01T11:49:38Z cycle_ok milestone_count=0
2026-04-01T11:59:38Z cycle_ok milestone_count=0
2026-04-01T12:09:38Z cycle_ok milestone_count=0
2026-04-01T12:19:39Z cycle_ok milestone_count=0
2026-04-01T12:29:39Z cycle_ok milestone_count=0
2026-04-01T12:39:40Z cycle_ok milestone_count=0
2026-04-01T12:49:40Z cycle_ok milestone_count=0
2026-04-01T12:59:40Z cycle_ok milestone_count=0
2026-04-01T13:09:41Z cycle_ok milestone_count=0
2026-04-01T13:19:41Z cycle_ok milestone_count=0
2026-04-01T13:29:42Z cycle_ok milestone_count=0
2026-04-01T13:39:42Z cycle_ok milestone_count=0
2026-04-01T13:49:48Z cycle_ok milestone_count=0
2026-04-01T13:59:43Z cycle_ok milestone_count=0
2026-04-01T14:09:43Z cycle_ok milestone_count=0
2026-04-01T14:19:44Z cycle_ok milestone_count=0
2026-04-01T14:29:44Z cycle_ok milestone_count=0
2026-04-01T14:39:45Z cycle_ok milestone_count=0
2026-04-01T14:49:51Z cycle_ok milestone_count=0
2026-04-01T14:59:46Z cycle_ok milestone_count=0
2026-04-01T15:09:46Z cycle_ok milestone_count=0
2026-04-01T15:19:47Z cycle_ok milestone_count=0
2026-04-01T15:29:47Z cycle_ok milestone_count=0
2026-04-01T15:39:47Z cycle_ok milestone_count=0
2026-04-01T15:49:54Z cycle_ok milestone_count=0
2026-04-01T15:59:48Z cycle_ok milestone_count=0
2026-04-01T16:09:48Z cycle_ok milestone_count=0
2026-04-01T16:19:49Z cycle_ok milestone_count=0
2026-04-01T16:29:49Z cycle_ok milestone_count=0
2026-04-01T16:39:50Z cycle_ok milestone_count=0
2026-04-01T16:49:57Z cycle_ok milestone_count=0

```

## Inference from `checkpoint_100_precheck`
- Current reconstructed **`cp_ok`:** **False**
- If `cp_ok` is False, `update_integrity_arm_state` does not set `arm_epoch_utc` (see `milestone.py`).
