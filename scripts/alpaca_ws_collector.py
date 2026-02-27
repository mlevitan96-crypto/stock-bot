#!/usr/bin/env python3
"""
Alpaca WebSocket collector: subscribe to real-time bars (and/or trades), aggregate into 1m bars,
write into data/bars/ used by the pipeline. Supplement to fetch-based bars; prefer freshest when both exist.
Append-only heartbeat: reports/data_integrity/alpaca_ws_health.jsonl (connected, last_msg_ts, last_bar_ts, symbols_count, errors).
Run on droplet (e.g. as a service). No strategy logic.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
BARS_DIR = REPO / "data" / "bars"
HEALTH_JSONL = REPO / "reports" / "data_integrity" / "alpaca_ws_health.jsonl"

try:
    import websocket
except ImportError:
    websocket = None  # type: ignore


def _log_health(connected: bool, last_msg_ts: float, last_bar_ts: float, symbols_count: int, errors: list[str]) -> None:
    try:
        HEALTH_JSONL.parent.mkdir(parents=True, exist_ok=True)
        rec = {
            "ts": time.time(),
            "connected": connected,
            "last_msg_ts": last_msg_ts,
            "last_bar_ts": last_bar_ts,
            "symbols_count": symbols_count,
            "errors": errors[:10],
        }
        with HEALTH_JSONL.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception:
        pass


def _parse_bar_timestamp(t_str: str) -> tuple[str, datetime] | None:
    """Return (date_str YYYY-MM-DD, dt) or None."""
    try:
        s = (t_str or "").replace("Z", "+00:00")
        if "T" in s:
            dt = datetime.fromisoformat(s[:26].replace("Z", "+00:00"))
        else:
            dt = datetime.fromtimestamp(float(t_str), tz=timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%d"), dt
    except Exception:
        return None


def _merge_bar_into_file(symbol: str, date_str: str, bar: dict) -> None:
    """Append or merge one bar into data/bars/<date>/<symbol>_1Min.json. Bars list has {t, o, h, l, c, v}."""
    path = BARS_DIR / date_str / f"{symbol}_1Min.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict] = []
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            existing = data.get("bars", data) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        except Exception:
            pass
    if not isinstance(existing, list):
        existing = []
    t_key = bar.get("t") or bar.get("timestamp")
    existing = [b for b in existing if (b.get("t") or b.get("timestamp")) != t_key]
    existing.append(bar)
    existing.sort(key=lambda b: (b.get("t") or b.get("timestamp") or ""))
    payload = {"symbol": symbol, "date": date_str, "timeframe": "1Min", "bars": existing}
    try:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        pass


def run_collector(symbols: list[str], heartbeat_interval_s: float = 30.0) -> None:
    if not symbols:
        symbols = ["SPY", "QQQ"]
    key = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
    secret = os.getenv("ALPACA_API_SECRET") or os.getenv("APCA_API_SECRET_KEY")
    if not key or not secret:
        _log_health(False, 0.0, 0.0, 0, ["ALPACA_API_KEY/ALPACA_API_SECRET not set"])
        return

    last_msg_ts = [0.0]
    last_bar_ts = [0.0]
    errors: list[str] = []
    connected = [False]

    def on_message(ws: object, message: str) -> None:
        last_msg_ts[0] = time.time()
        try:
            raw = json.loads(message) if isinstance(message, str) else message
            if isinstance(raw, list):
                for item in raw:
                    _handle_message_item(item)
            else:
                _handle_message_item(raw)
        except Exception as e:
            errors.append(str(e)[:200])

    def _handle_message_item(item: dict) -> None:
        t = item.get("T") or item.get("t")
        if t == "b":  # bar
            symbol = item.get("S") or ""
            ts = item.get("t") or ""
            parsed = _parse_bar_timestamp(ts)
            if parsed and symbol:
                date_str, _ = parsed
                bar = {
                    "t": ts,
                    "o": float(item.get("o", 0)),
                    "h": float(item.get("h", 0)),
                    "l": float(item.get("l", 0)),
                    "c": float(item.get("c", 0)),
                    "v": int(item.get("v", 0)),
                }
                _merge_bar_into_file(symbol, date_str, bar)
                last_bar_ts[0] = time.time()

    def on_error(ws: object, err: Exception) -> None:
        errors.append(str(err)[:200])

    def on_close(ws: object, close_status_code: int, close_msg: str) -> None:
        connected[0] = False

    def on_open(ws: object) -> None:
        connected[0] = True
        ws.send(json.dumps({"action": "auth", "key": key, "secret": secret}))
        time.sleep(0.5)
        ws.send(json.dumps({"action": "subscribe", "bars": symbols}))

    if websocket is None:
        _log_health(False, 0.0, 0.0, len(symbols), ["websocket-client not installed; pip install websocket-client"])
        print("Install websocket-client to run the collector.", file=sys.stderr)
        return

    url = "wss://stream.data.alpaca.markets/v2/iex"
    ws = websocket.WebSocketApp(
        url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
    )
    def heartbeat_loop() -> None:
        while True:
            time.sleep(heartbeat_interval_s)
            _log_health(connected[0], last_msg_ts[0], last_bar_ts[0], len(symbols), errors[-5:] if errors else [])

    def ws_loop() -> None:
        while True:
            try:
                ws.run_forever(ping_interval=20, ping_timeout=10)
            except Exception as e:
                errors.append(str(e)[:200])
            connected[0] = False
            time.sleep(5)

    th_heartbeat = threading.Thread(target=heartbeat_loop, daemon=True)
    th_ws = threading.Thread(target=ws_loop, daemon=True)
    th_heartbeat.start()
    th_ws.start()
    try:
        while th_ws.is_alive():
            th_ws.join(timeout=1.0)
    except KeyboardInterrupt:
        _log_health(False, last_msg_ts[0], last_bar_ts[0], len(symbols), errors[-5:] if errors else [])


def main() -> int:
    sym_str = os.getenv("ALPACA_WS_SYMBOLS", "SPY,QQQ")
    symbols = [s.strip() for s in sym_str.split(",") if s.strip()]
    run_collector(symbols)
    return 0


if __name__ == "__main__":
    sys.exit(main())
