#!/usr/bin/env python3
"""Send a one-off SRE maintenance Telegram (bypasses ET quiet hours). Droplet: source .env first or use dotenv."""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.chdir(REPO)

try:
    from dotenv import load_dotenv

    load_dotenv(REPO / ".env")
except Exception:
    pass

os.environ.setdefault("TELEGRAM_GOVERNANCE_RESPECT_MARKET_HOURS", "0")

import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "alpaca_telegram", REPO / "scripts" / "alpaca_telegram.py"
)
assert _spec and _spec.loader
_tg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tg)
send_governance_telegram = _tg.send_governance_telegram


def main() -> int:
    msg = (
        "SYSTEM MAINTENANCE: Memory Bank updated. Score Floor locked at 1.6. Ready for Market Open."
    )
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
    ok = send_governance_telegram(msg, script_name="sre_maintenance")
    print("sent" if ok else "failed")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
