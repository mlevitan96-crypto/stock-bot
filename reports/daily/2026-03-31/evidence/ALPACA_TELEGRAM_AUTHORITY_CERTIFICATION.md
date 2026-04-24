# ALPACA_TELEGRAM_AUTHORITY_CERTIFICATION

## Declared authority
- **Primary production sender:** `telemetry/alpaca_telegram_integrity/` (invoked by `scripts/run_alpaca_telegram_integrity_cycle.py`).
- **Transport:** `scripts/alpaca_telegram.py` `send_governance_telegram`.
- **Lockdown:** set **`TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1`** so only integrity `script_name` values reach the API (see `scripts/alpaca_telegram.py` `_INTEGRITY_ONLY_SCRIPT_NAMES`).

## Static scan: Python files touching Telegram send APIs
- **Rows:** 23

| file | match |
|------|-------|
| `scripts/alpaca_edge_2000_pipeline.py` | telegram.org bot URL |
| `scripts/alpaca_fastlane_deep_review.py` | telegram.org bot URL |
| `scripts/alpaca_postclose_deepdive.py` | send_governance_telegram |
| `scripts/alpaca_telegram.py` | send_governance_telegram |
| `scripts/audit/alpaca_250_audit_readiness_mission.py` | send_governance_telegram |
| `scripts/audit/run_alpaca_trade_count_telegram_mission.py` | sendMessage |
| `scripts/governance/telegram_failure_detector.py` | send_governance_telegram |
| `scripts/notify/send_telegram_message.py` | telegram.org bot URL |
| `scripts/notify_fast_lane_summary.py` | telegram.org bot URL |
| `scripts/notify_governance_experiment_alpaca_break.py` | telegram.org bot URL |
| `scripts/notify_governance_experiment_alpaca_complete.py` | telegram.org bot URL |
| `scripts/run_alpaca_board_review_heartbeat.py` | send_governance_telegram |
| `scripts/run_alpaca_board_review_tier1.py` | send_governance_telegram |
| `scripts/run_alpaca_board_review_tier2.py` | send_governance_telegram |
| `scripts/run_alpaca_board_review_tier3.py` | send_governance_telegram |
| `scripts/run_alpaca_convergence_check.py` | send_governance_telegram |
| `scripts/run_alpaca_daily_governance.py` | telegram.org bot URL |
| `scripts/run_alpaca_e2e_audit_on_droplet.py` | send_governance_telegram |
| `scripts/run_alpaca_e2e_governance_audit.py` | send_governance_telegram |
| `scripts/run_alpaca_promotion_gate.py` | send_governance_telegram |
| `scripts/send_csa_fastlane_verdict_telegram.py` | telegram.org bot URL |
| `scripts/send_telegram_test.py` | telegram.org bot URL |
| `telemetry/alpaca_telegram_integrity/runner_core.py` | send_governance_telegram |

## Outside `telemetry/alpaca_telegram_integrity/` (must be disabled or blocked when integrity-only)
- **Count:** 22

| file | match |
|------|-------|
| `scripts/alpaca_edge_2000_pipeline.py` | telegram.org bot URL |
| `scripts/alpaca_fastlane_deep_review.py` | telegram.org bot URL |
| `scripts/alpaca_postclose_deepdive.py` | send_governance_telegram |
| `scripts/alpaca_telegram.py` | send_governance_telegram |
| `scripts/audit/alpaca_250_audit_readiness_mission.py` | send_governance_telegram |
| `scripts/audit/run_alpaca_trade_count_telegram_mission.py` | sendMessage |
| `scripts/governance/telegram_failure_detector.py` | send_governance_telegram |
| `scripts/notify/send_telegram_message.py` | telegram.org bot URL |
| `scripts/notify_fast_lane_summary.py` | telegram.org bot URL |
| `scripts/notify_governance_experiment_alpaca_break.py` | telegram.org bot URL |
| `scripts/notify_governance_experiment_alpaca_complete.py` | telegram.org bot URL |
| `scripts/run_alpaca_board_review_heartbeat.py` | send_governance_telegram |
| `scripts/run_alpaca_board_review_tier1.py` | send_governance_telegram |
| `scripts/run_alpaca_board_review_tier2.py` | send_governance_telegram |
| `scripts/run_alpaca_board_review_tier3.py` | send_governance_telegram |
| `scripts/run_alpaca_convergence_check.py` | send_governance_telegram |
| `scripts/run_alpaca_daily_governance.py` | telegram.org bot URL |
| `scripts/run_alpaca_e2e_audit_on_droplet.py` | send_governance_telegram |
| `scripts/run_alpaca_e2e_governance_audit.py` | send_governance_telegram |
| `scripts/run_alpaca_promotion_gate.py` | send_governance_telegram |
| `scripts/send_csa_fastlane_verdict_telegram.py` | telegram.org bot URL |
| `scripts/send_telegram_test.py` | telegram.org bot URL |

## Production confirmation (manual on droplet)
- `crontab -l` — ensure no board/post-close/fast-lane Telegram jobs conflict with policy.
- `systemctl list-timers --all | grep -E 'telegram|postclose|stock-bot'`
- `.env`: `TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1` recommended for single-authority sends.
