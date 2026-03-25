#!/usr/bin/env python3
"""Phase 0: count post-deploy terminal closes (run on droplet with PYTHONPATH=repo root)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DEPLOY_START = 1774458080  # 2026-03-25T17:01:20Z stock-bot restart / strict chain validation epoch


def _ts(s: str | None) -> float | None:
    if not s or not isinstance(s, str):
        return None
    try:
        t = s.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).timestamp()
    except Exception:
        return None


def main() -> None:
    now = datetime.now(timezone.utc)
    logs = ROOT / "logs"
    ex_path = logs / "exit_attribution.jsonl"
    ord_path = logs / "orders.jsonl"

    from_exit: list[tuple[str, float, str]] = []
    if ex_path.is_file():
        with ex_path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = _ts(rec.get("timestamp"))
                if ts is None or ts < DEPLOY_START:
                    continue
                ep = rec.get("exit_price")
                try:
                    ok_price = ep is not None and float(ep) > 0
                except (TypeError, ValueError):
                    ok_price = False
                if not ok_price:
                    continue
                sym = str(rec.get("symbol") or "?").upper()
                from_exit.append((sym, ts, rec.get("timestamp") or ""))

    from_orders: list[tuple[str, float, str]] = []
    if ord_path.is_file():
        with ord_path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ev = rec.get("type") or rec.get("event_type")
                act = (rec.get("action") or "").lower()
                if act != "close_position" and "close" not in act:
                    continue
                # Prefer explicit close_position
                if act != "close_position":
                    continue
                ts = _ts(rec.get("timestamp")) or _ts(rec.get("ts"))
                if ts is None or ts < DEPLOY_START:
                    continue
                sym = str(rec.get("symbol") or "?").upper()
                from_orders.append((sym, ts, str(rec.get("timestamp") or rec.get("ts") or "")))

    from_exit.sort(key=lambda x: -x[1])
    from_orders.sort(key=lambda x: -x[1])

    out = {
        "current_utc": now.isoformat(),
        "strict_epoch_start_utc": datetime.fromtimestamp(DEPLOY_START, tz=timezone.utc).isoformat(),
        "terminal_closes_since_deploy_count_exit_attribution": len(from_exit),
        "terminal_closes_since_deploy_count_orders_close_position": len(from_orders),
        "examples_exit_attribution": [{"symbol": s, "timestamp": iso} for s, _, iso in from_exit[:5]],
        "examples_orders": [{"symbol": s, "timestamp": iso} for s, _, iso in from_orders[:5]],
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
