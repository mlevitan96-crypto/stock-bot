#!/usr/bin/env python3
"""
Unusual Whales WebSocket consumer (Sniper flow-alerts).

Protocol (from UW OpenAPI / socket docs):
  URI: wss://api.unusualwhales.com/socket?token=<API_TOKEN>
  Join: {"channel":"flow-alerts","msg_type":"join"}
  Frames: JSON array [channel_name, payload]

This module streams **market-wide** `flow-alerts` and filters to a Sniper symbol set client-side
(UW does not expose per-symbol flow-alerts channels in the public channel table).

Requires: ``websockets`` (already pinned for alpaca-trade-api).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import time
from typing import Any, Callable, Dict, Optional, Set

log = logging.getLogger(__name__)

UW_WS_URI = os.getenv("UW_WS_BASE", "wss://api.unusualwhales.com/socket")


def extract_flow_symbol(payload: Any) -> Optional[str]:
    """Best-effort underlying / issue symbol from a flow-alerts payload."""
    if not isinstance(payload, dict):
        return None
    for k in (
        "symbol",
        "underlying",
        "underlying_symbol",
        "underlyingSymbol",
        "ticker",
        "issue_symbol",
        "issue",
    ):
        v = payload.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip().upper().split()[0]
    return None


def _build_uri(api_token: str) -> str:
    from urllib.parse import quote

    tok = quote(str(api_token).strip(), safe="")
    sep = "&" if "?" in UW_WS_URI else "?"
    return f"{UW_WS_URI}{sep}token={tok}"


async def _consume_flow_alerts(
    uri: str,
    sniper: Set[str],
    on_alert: Callable[[str, Dict[str, Any]], None],
    stop: asyncio.Event,
    *,
    reconnect_min: float = 2.0,
    reconnect_max: float = 120.0,
) -> None:
    import websockets

    backoff = reconnect_min
    while not stop.is_set():
        try:
            async with websockets.connect(
                uri,
                ping_interval=20,
                ping_timeout=60,
                close_timeout=10,
                max_size=8_000_000,
            ) as ws:
                await ws.send(json.dumps({"channel": "flow-alerts", "msg_type": "join"}))
                backoff = reconnect_min
                while not stop.is_set():
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=120.0)
                    except asyncio.TimeoutError:
                        continue
                    try:
                        msg = json.loads(raw)
                    except Exception:
                        continue
                    if not isinstance(msg, list) or len(msg) < 2:
                        continue
                    ch, data = msg[0], msg[1]
                    if ch != "flow-alerts":
                        continue
                    if isinstance(data, dict) and data.get("status") == "ok" and "response" in data:
                        continue
                    sym = extract_flow_symbol(data)
                    if sym and sym in sniper and isinstance(data, dict):
                        try:
                            on_alert(sym, data)
                        except Exception as ex:
                            log.warning("uw_flow_ws on_alert failed: %s", ex)
        except asyncio.CancelledError:
            break
        except Exception as ex:
            log.warning("uw_flow_ws connection error: %s (reconnect in %.1fs)", ex, backoff)
            await asyncio.sleep(min(backoff, reconnect_max))
            backoff = min(backoff * 2, reconnect_max)


def run_ws_loop_in_thread(
    api_token: str,
    sniper: Set[str],
    on_alert: Callable[[str, Dict[str, Any]], None],
    stop_event: threading.Event,
) -> threading.Thread:
    """Start asyncio WS loop on a daemon thread. Stop via ``stop_event``."""

    def _runner() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        a_stop = asyncio.Event()

        def _bridge_stop() -> None:
            while not stop_event.is_set():
                time.sleep(0.25)
            loop.call_soon_threadsafe(a_stop.set)

        watcher = threading.Thread(target=_bridge_stop, daemon=True)
        watcher.start()
        uri = _build_uri(api_token)
        try:
            loop.run_until_complete(_consume_flow_alerts(uri, sniper, on_alert, a_stop))
        finally:
            try:
                pending = asyncio.all_tasks(loop)
                for t in pending:
                    t.cancel()
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            loop.close()

    t = threading.Thread(target=_runner, name="uw-flow-ws", daemon=True)
    t.start()
    return t
