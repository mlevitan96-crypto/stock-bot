#!/usr/bin/env python3
"""
Verify TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID at runtime (Step 0 of E2E audit).
Optionally loads .env from repo root to match cron/droplet runtime.
Prints masked confirmation; exits 1 if any missing.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    # Optionally load .env so we match runtime when scripts are run from env-loaded context
    env_file = REPO / ".env"
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            pass

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")

    token_ok = bool(token and str(token).strip())
    chat_ok = bool(chat and str(chat).strip())

    print("Token present:", "YES" if token_ok else "NO")
    print("Chat ID present:", "YES" if chat_ok else "NO")

    if not token_ok or not chat_ok:
        audit = REPO / "reports" / "audit" / "TELEGRAM_ENV_MISSING.md"
        audit.parent.mkdir(parents=True, exist_ok=True)
        audit.write_text(
            "# Telegram environment missing — E2E audit blocked\n\n"
            "**Step 0 failed.** TELEGRAM_BOT_TOKEN and/or TELEGRAM_CHAT_ID were not set at runtime.\n\n"
            "- Token present: NO\n"
            "- Chat ID present: NO\n\n"
            "Set both in your environment (or in `.env` and ensure it is loaded before running governance scripts), "
            "then re-run:\n"
            "  `python scripts/verify_telegram_env.py`\n\n"
            "Once both show YES, proceed with the Alpaca E2E governance audit (Steps 1–6).\n",
            encoding="utf-8",
        )
        print(f"Wrote {audit}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
