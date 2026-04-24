#!/usr/bin/env python3
"""Check where TELEGRAM_* env vars live on droplet: venv, systemd, .env, .alpaca_env."""
from droplet_client import DropletClient

c = DropletClient()

print("=== 1) Systemd unit files (stock-bot, alpaca, deploy) ===")
out, _, _ = c._execute("systemctl list-unit-files 2>/dev/null | grep -iE 'stock|alpaca|deploy|bot' || true")
print(out or "(none)")

print("\n=== 2) Main stock-bot service unit (if any) ===")
out2, _, _ = c._execute("cat /etc/systemd/system/stock-bot.service 2>/dev/null || cat /lib/systemd/system/stock-bot.service 2>/dev/null || echo 'No stock-bot.service found'")
print(out2 or "")

print("\n=== 3) EnvironmentFile / Environment in stock-bot*.service ===")
out3, _, _ = c._execute("grep -l stock /etc/systemd/system/*.service 2>/dev/null; for f in /etc/systemd/system/stock*.service /etc/systemd/system/*stock*.service 2>/dev/null; do [ -f \"$f\" ] && echo \"--- $f ---\" && grep -E 'Environment|EnvironmentFile' \"$f\" 2>/dev/null; done")
print(out3 or "(no matches)")

print("\n=== 4) Project .env has TELEGRAM? (names only, no values) ===")
out4, _, _ = c._execute_with_cd("grep -E '^TELEGRAM_' .env 2>/dev/null | sed 's/=.*/=***/' || echo '.env missing or no TELEGRAM lines'")
print(out4.strip() if out4 else "(empty)")
if not (out4 and "TELEGRAM" in out4):
    print("  -> .env is what systemd loads for stock-bot.service; add TELEGRAM_* there if bot should have them.")

print("\n=== 5) /root/.alpaca_env has TELEGRAM? (names only) ===")
out5, _, _ = c._execute("grep -E '^export TELEGRAM_' /root/.alpaca_env 2>/dev/null | sed 's/=.*/=***/' || echo 'File missing or no TELEGRAM lines'")
print(out5 or "")

print("\n=== 6) Venv activate / env (if venv exists) ===")
out6a, _, _ = c._execute_with_cd("test -d venv && echo 'venv exists' || test -d .venv && echo '.venv exists' || echo 'No venv dir'")
print(out6a or "")
out6b, _, _ = c._execute_with_cd("grep -E 'TELEGRAM' venv/bin/activate 2>/dev/null || grep -E 'TELEGRAM' .venv/bin/activate 2>/dev/null || echo 'No TELEGRAM in venv activate'")
print("TELEGRAM in venv activate:", "yes" if out6b and "TELEGRAM" in (out6b or "") else "no")

print("\n=== 7) Where process gets env (e.g. deploy_supervisor or main) ===")
out7, _, _ = c._execute("ps aux | grep -E 'deploy_supervisor|main.py|dashboard.py' | grep -v grep | head -5")
print(out7 or "(no matching processes)")
