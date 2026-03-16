"""
Alpaca governance Telegram helper — best-effort send; failures logged, never raise.

Used by Tier 1/2/3, convergence, promotion gate, and heartbeat scripts when --telegram.
Uses TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID. On failure, appends to TELEGRAM_NOTIFICATION_LOG.md.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_LOG = REPO / "TELEGRAM_NOTIFICATION_LOG.md"


def send_governance_telegram(text: str, log_path: Path | None = None, script_name: str = "governance") -> bool:
    """
    Send text via Telegram. On failure, append to log_path and return False.
    Never raises; never blocks caller.
    """
    log_path = log_path or DEFAULT_LOG
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        _append_log(log_path, script_name, "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
        return False
    try:
        import requests
    except ImportError:
        _append_log(log_path, script_name, "requests not installed")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat, "text": text}, timeout=30)
        if not r.ok:
            _append_log(log_path, script_name, f"HTTP {r.status_code} {r.text[:200]}")
            return False
        return True
    except Exception as e:
        _append_log(log_path, script_name, str(e))
        return False


def _append_log(log_path: Path, script_name: str, error: str) -> None:
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        line = f"{ts} — {script_name} — {error}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
