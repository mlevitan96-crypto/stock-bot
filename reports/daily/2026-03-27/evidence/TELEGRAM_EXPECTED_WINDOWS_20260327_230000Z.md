# Expected Telegram / integrity windows — Alpaca + Kraken

**TS:** `20260327_230000Z`  
**Source of truth:** `scripts/governance/telegram_failure_detector.py`

## Alpaca

| expected_send_type | expected_time_window (ET) | Runner entrypoint | Sent-state / evidence store |
|--------------------|---------------------------|-------------------|------------------------------|
| **post_close** | **Mon–Fri**, expect completion after **16:45 America/New_York** (15 min slack after **16:30** timer) | `scripts/alpaca_postclose_deepdive.py` via **`alpaca-postclose-deepdive.service`** | `reports/alpaca_daily_close_telegram.jsonl` + `journalctl -u alpaca-postclose-deepdive.service` |
| **milestone** | **Mon–Fri**, **`*/10` at minutes 0–50 during 13:00–20:59 UTC** (matches `scripts/install_cron_alpaca_notifier.py` cronline) | `scripts/notify_alpaca_trade_milestones.py` | `logs/notify_milestones.log` (freshness + error scan); dedupe in `state/alpaca_trade_notifications.json` (not re-parsed here) |

## Kraken (integrity proxy)

There is **no** checked-in Kraken daily Telegram runner (see `KRAKEN_TELEGRAM_END_TO_END_PROOF`).  
**Kraken-relevant operational output** monitored here is **direction readiness freshness** (dashboard contract: `state/direction_readiness.json`).

| expected_send_type | expected_time_window | Runner entrypoint | State store |
|--------------------|---------------------|-------------------|-------------|
| **integrity** | **Mon–Fri**, **09:00–21:59 UTC** (aligned with `install_direction_readiness_cron_on_droplet.py` `*/5 9-21`) | `scripts/governance/check_direction_readiness_and_run.py` (cron) | `state/direction_readiness.json` + `logs/direction_readiness_cron.log` |

## Pager states

`SENT` | `PASS` (integrity OK) | `SEND_FAILED` | `RUNNER_NOT_RUN` | `GATED` (staleness) | `PENDING` | `SKIPPED`

Failure paging fires for **`SEND_FAILED`**, **`RUNNER_NOT_RUN`**, and **`GATED`** (deduped by `failure_signature`).
