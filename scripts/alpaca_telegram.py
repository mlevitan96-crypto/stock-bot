"""
Alpaca governance Telegram helper — best-effort send; failures logged, never raise.

Used by Tier 1/2/3, convergence, promotion gate, and heartbeat scripts when --telegram.
Uses TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID. On failure, appends to TELEGRAM_NOTIFICATION_LOG.md.

Quiet hours (default on): no HTTP and no log line outside US/Eastern send window so systemd timers
(telegram-failure-detector, alpaca-telegram-integrity) do not spam when the market is closed.
Set TELEGRAM_GOVERNANCE_RESPECT_MARKET_HOURS=0 to send 24/7 (e.g. E2E tests).
Optional: TELEGRAM_GOVERNANCE_ET_SEND_START_HOUR (default 7), TELEGRAM_GOVERNANCE_ET_SEND_END_HOUR (default 21, exclusive).
Set TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1 on the droplet to block every send_governance_telegram caller except the Alpaca integrity cycle script_name allowlist (see MEMORY_BANK § Telegram Notification Authority).
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parents[1]
DEFAULT_LOG = REPO / "TELEGRAM_NOTIFICATION_LOG.md"

# When TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1, only these script_name values may hit the API
# (Alpaca integrity cycle + its explicit test hooks). Set on droplet to lock out board/gate/post-close sends.
_INTEGRITY_ONLY_SCRIPT_NAMES = frozenset(
    {
        "alpaca_checkpoint_10",
        "alpaca_integrity_test_100trade",
        "alpaca_checkpoint_100",
        "alpaca_checkpoint_100_deferred",
        "alpaca_integrity_test_milestone",
        "alpaca_milestone_250",
        "alpaca_integrity_test_alert",
        "alpaca_data_integrity",
        "sre_maintenance",  # operator one-off: scripts/alpaca_telegram.py after-hours / maintenance pings
        "alpaca_weekly_handoff",  # Wednesday performance + Cursor prompt (CRON_TZ=America/New_York)
        # Live Whale shadow ML (main.py) — engine failure + canonical trade milestones
        "alpaca_ml_engine_failure",
        "alpaca_shadow_milestone_600",
        "alpaca_shadow_milestone_750",
        "alpaca_shadow_milestone_1000",
        # Total system lock / GUT (main.py one-shot pulse + per-entry God Tier pass)
        "vanguard_system_lock",
        "gut_god_tier_entry",
    }
)


def _env_truthy(name: str, default: str = "1") -> bool:
    v = (os.environ.get(name, default) or "").strip().lower()
    return v in ("1", "true", "yes", "on")


def should_suppress_governance_telegram_send(now_utc: Optional[datetime] = None) -> bool:
    """
    True when governance Telegram should not hit the API (weekend America/New_York, or
    local ET hour outside [start, end) on weekdays). Used by send_governance_telegram.
    """
    if not _env_truthy("TELEGRAM_GOVERNANCE_RESPECT_MARKET_HOURS", "1"):
        return False
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        return False
    now_utc = now_utc or datetime.now(timezone.utc)
    et = ZoneInfo("America/New_York")
    local = now_utc.astimezone(et)
    if local.weekday() >= 5:
        return True
    try:
        start_h = int(os.environ.get("TELEGRAM_GOVERNANCE_ET_SEND_START_HOUR", "7"))
        end_h = int(os.environ.get("TELEGRAM_GOVERNANCE_ET_SEND_END_HOUR", "21"))
    except ValueError:
        start_h, end_h = 7, 21
    start_h = max(0, min(23, start_h))
    end_h = max(0, min(24, end_h))
    if end_h <= start_h:
        end_h = min(24, start_h + 14)
    h = local.hour
    if h < start_h or h >= end_h:
        return True
    return False


def send_governance_telegram(text: str, log_path: Path | None = None, script_name: str = "governance") -> bool:
    """
    Send text via Telegram. On failure, append to log_path and return False.
    Never raises; never blocks caller.
    """
    log_path = log_path or DEFAULT_LOG
    if _env_truthy("TELEGRAM_GOVERNANCE_INTEGRITY_ONLY", "0"):
        if script_name not in _INTEGRITY_ONLY_SCRIPT_NAMES:
            _append_log(
                log_path,
                script_name,
                "send blocked: TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1 (only telemetry/alpaca_telegram_integrity senders allowed)",
            )
            return False
    if should_suppress_governance_telegram_send():
        return False
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
            hint = _http_error_hint(r.status_code)
            _append_log(log_path, script_name, f"HTTP {r.status_code} {r.text[:200]}{hint}")
            return False
        return True
    except Exception as e:
        _append_log(log_path, script_name, str(e))
        return False


def _http_error_hint(status: int) -> str:
    if status == 404:
        return " — 404 from Telegram API usually means invalid or revoked TELEGRAM_BOT_TOKEN (confirm with @BotFather)"
    if status == 401:
        return " — 401 unauthorized: bad bot token"
    if status == 403:
        return " — 403: bot blocked or TELEGRAM_CHAT_ID not allowed for this bot"
    return ""


def _append_log(log_path: Path, script_name: str, error: str) -> None:
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        line = f"{ts} — {script_name} — {error}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


if __name__ == "__main__":
    import argparse

    try:
        from dotenv import load_dotenv

        for env_path in (REPO / ".env", Path("/root/.alpaca_env")):
            try:
                load_dotenv(env_path)
            except OSError:
                pass
    except Exception:
        pass

    ap = argparse.ArgumentParser(description="Send one Telegram via governance helper (uses env credentials).")
    ap.add_argument("--message", required=True, help="Message body")
    ap.add_argument("--script-name", default="sre_heartbeat", help="Label for logs / integrity-only allowlist")
    args = ap.parse_args()
    ok = send_governance_telegram(args.message, script_name=args.script_name)
    raise SystemExit(0 if ok else 1)
