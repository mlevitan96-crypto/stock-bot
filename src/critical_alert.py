#!/usr/bin/env python3
"""
Critical SRE pager: Telegram for wheel / Alpaca hard failures only.

- Credentials: ``TELEGRAM_BOT_TOKEN`` and ``TELEGRAM_CHAT_ID`` (same as governance Telegram; load via .env / process env).
- Spam control: per-``dedupe_key`` cooldown (default ``CRITICAL_ALERT_COOLDOWN_SEC`` = 600s); persisted in ``state/critical_alert_dedupe.json``.
- Delivery: ``scripts.alpaca_telegram.send_governance_telegram`` with ``script_name=alpaca_wheel_critical`` (integrity-only allowlist).

Optional: ``CRITICAL_ALERT_BYPASS_MARKET_HOURS=1`` posts via Telegram HTTP even when governance quiet-hours would suppress (SRE: broker API dead overnight).
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parents[1]
_DEDUPE_PATH = REPO / "state" / "critical_alert_dedupe.json"
_SCRIPT_NAME = "alpaca_wheel_critical"


def _cooldown_seconds() -> int:
    try:
        return max(60, int(os.environ.get("CRITICAL_ALERT_COOLDOWN_SEC", "600")))
    except (TypeError, ValueError):
        return 600


def _alerts_enabled() -> bool:
    v = (os.environ.get("CRITICAL_ALERTS_ENABLED", "1") or "").strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    return bool(token and chat)


def _load_dedupe() -> Dict[str, Any]:
    try:
        if _DEDUPE_PATH.is_file():
            raw = _DEDUPE_PATH.read_text(encoding="utf-8")
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
    except Exception as e:
        log.debug("critical_alert dedupe read: %s", e)
    return {}


def _save_dedupe(data: Dict[str, Any]) -> None:
    try:
        _DEDUPE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _DEDUPE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(_DEDUPE_PATH)
    except Exception as e:
        log.warning("critical_alert dedupe write failed: %s", e)


def _should_send(dedupe_key: str, cooldown: int) -> bool:
    now = time.time()
    data = _load_dedupe()
    last = data.get(dedupe_key)
    try:
        last_f = float(last) if last is not None else 0.0
    except (TypeError, ValueError):
        last_f = 0.0
    if now - last_f < float(cooldown):
        log.debug("critical_alert suppressed (cooldown) key=%s", dedupe_key)
        return False
    data[dedupe_key] = now
    # Prune entries older than 7 days to keep file small
    cutoff = now - 86400.0 * 7.0
    pruned = {k: v for k, v in data.items() if isinstance(v, (int, float)) and float(v) >= cutoff}
    pruned[dedupe_key] = now
    _save_dedupe(pruned)
    return True


def _send_telegram_direct(text: str) -> bool:
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if not token or not chat:
        return False
    try:
        import requests
    except ImportError:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat, "text": text}, timeout=30)
        return bool(r.ok)
    except Exception as e:
        log.warning("critical_alert direct Telegram failed: %s", e)
        return False


def send_critical_wheel_alert(
    title: str,
    detail: str,
    *,
    dedupe_key: str,
    cooldown_seconds: Optional[int] = None,
) -> bool:
    """
    Send one critical Telegram for wheel/SRE events (fail-closed broker, state heal, etc.).

    Returns True if a send was attempted and succeeded; False if suppressed, disabled, or failed.
    """
    if not _alerts_enabled():
        log.debug("critical_alert disabled or missing Telegram env")
        return False
    cd = int(cooldown_seconds) if cooldown_seconds is not None else _cooldown_seconds()
    if not _should_send(dedupe_key, cd):
        return False
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    body = f"CRITICAL — {title}\n{ts}\n\n{detail}"[:3900]
    bypass = (os.environ.get("CRITICAL_ALERT_BYPASS_MARKET_HOURS", "0") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if bypass:
        ok = _send_telegram_direct(body)
        if ok:
            log.warning("critical_alert sent (bypass hours) key=%s", dedupe_key)
        return ok
    try:
        from scripts.alpaca_telegram import send_governance_telegram

        ok = send_governance_telegram(body, script_name=_SCRIPT_NAME)
        if ok:
            log.warning("critical_alert sent key=%s", dedupe_key)
        return bool(ok)
    except Exception as e:
        log.warning("critical_alert send failed: %s", e)
        return False
