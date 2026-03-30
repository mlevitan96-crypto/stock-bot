#!/bin/bash
# Install cron for Alpaca trade milestone notifications
# `.` not `source`: cron uses dash; venv python matches direction_readiness cron.
# DEPRECATED 2026-03-30: milestones are systemd alpaca-telegram-integrity.timer + run_alpaca_telegram_integrity_cycle.py
# Do not re-add notify_alpaca_trade_milestones.py to crontab.
echo "install_alpaca_notifier_cron.sh is deprecated — use scripts/install_alpaca_telegram_integrity_on_droplet.sh" >&2
exit 1
mkdir -p /root/stock-bot/logs
touch /root/stock-bot/logs/notify_milestones.log
crontab -l | grep notify_alpaca_trade_milestones
