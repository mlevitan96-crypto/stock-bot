#!/usr/bin/env python3
"""
Wheel premium + trade-count milestones over ``logs/telemetry.jsonl`` (strategy_id=wheel).

Telegram thresholds (deduped): **10, 50, 150, 250** wheel events with finite ``premium`` > 0.
Each message includes cumulative **premium collected (USD)** and optional **NAV** from
``state/alpaca_account_snapshot.json`` when present.

Env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID — same as other watchers.
State: data/.wheel_premium_milestone_state.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
os.chdir(REPO)

try:
    from dotenv import load_dotenv

    load_dotenv(REPO / ".env")
except Exception:
    pass

from config.registry import LogFiles  # noqa: E402

STATE_PATH = REPO / "data" / ".wheel_premium_milestone_state.json"
ALPACA_SNAPSHOT = REPO / "state" / "alpaca_account_snapshot.json"
MILESTONES = (10, 50, 150, 250)


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def _nav_usd() -> Optional[float]:
    snap = _read_json(ALPACA_SNAPSHOT, {})
    if not isinstance(snap, dict):
        return None
    for k in ("equity", "portfolio_value", "last_equity"):
        v = snap.get(k)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
    return None


def _scan_telemetry(path: Path) -> Tuple[int, float, Set[str]]:
    """Return (count_with_premium, sum_premium_usd, dedupe_keys)."""
    if not path.exists():
        return 0, 0.0, set()
    count = 0
    total = 0.0
    seen: Set[str] = set()
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("strategy_id") != "wheel":
                continue
            prem = row.get("premium")
            if prem is None:
                continue
            try:
                pv = float(prem)
            except (TypeError, ValueError):
                continue
            if not (pv > 0 and pv == pv):
                continue
            key = str(row.get("order_id") or row.get("timestamp") or "") + str(row.get("symbol") or "")
            if key in seen:
                continue
            seen.add(key)
            count += 1
            total += pv
    return count, total, seen


def _send(msg: str) -> bool:
    try:
        from scripts.alpaca_telegram import send_governance_telegram

        return bool(send_governance_telegram(msg, script_name="wheel_premium_milestone_watcher"))
    except Exception:
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        chat = os.environ.get("TELEGRAM_CHAT_ID")
        if not token or not chat:
            print(msg, flush=True)
            return False
        import urllib.request

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        body = json.dumps({"chat_id": chat, "text": msg}).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=20).read()
        return True


def main() -> int:
    st: Dict[str, Any] = _read_json(STATE_PATH, {"fired": [], "last_count": 0, "last_premium_sum": 0.0})
    fired = set(st.get("fired") or [])
    path = LogFiles.TELEMETRY
    count, prem_sum, _ = _scan_telemetry(path)
    nav = _nav_usd()
    nav_s = f"{nav:,.2f}" if nav is not None else "n/a"
    for m in MILESTONES:
        key = f"wheel_premium_events_{m}"
        if count >= m and key not in fired:
            msg = (
                f"🎡 [Wheel] Milestone **{m}** wheel premium events (deduped fills in telemetry).\n"
                f"Cumulative premium collected (approx): **${prem_sum:,.2f}** USD.\n"
                f"Account NAV snapshot (equity): **{nav_s}** USD."
            )
            if _send(msg):
                fired.add(key)
    st["fired"] = sorted(fired)
    st["last_count"] = count
    st["last_premium_sum"] = prem_sum
    _write_json(STATE_PATH, st)
    print(json.dumps({"wheel_premium_events": count, "premium_sum_usd": prem_sum, "nav": nav}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
