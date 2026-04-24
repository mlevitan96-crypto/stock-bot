#!/usr/bin/env python3
"""
Sync TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from current environment into
/root/stock-bot/.env so systemd (stock-bot.service) has them.

Run on droplet with venv activated so env is populated:
  source /root/stock-bot/venv/bin/activate && python3 scripts/sync_telegram_to_dotenv.py

Does not print or log secret values.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ENV_FILE = REPO / ".env"


def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        print("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in current environment. Activate venv or source .alpaca_env first.")
        return 1

    lines: list[str] = []
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("TELEGRAM_"):
                    continue
                lines.append(line)

    lines.append(f"TELEGRAM_BOT_TOKEN={token}\n")
    lines.append(f"TELEGRAM_CHAT_ID={chat_id}\n")
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Synced TELEGRAM_* from current env to .env (systemd will use after restart).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
