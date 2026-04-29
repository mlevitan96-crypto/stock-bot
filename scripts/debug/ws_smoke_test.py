#!/usr/bin/env python3
"""
One-shot Unusual Whales WebSocket handshake smoke test.

Uses ``uw_flow_ws.uw_ws_connect_config()`` (Bearer / query / both per env), connects to
``wss://api.unusualwhales.com/socket``, sends the production ``flow-alerts`` join, then
waits briefly for an ack.

Exit / stdout contract (per operator directive):
  - HTTP 401 on upgrade → ``FAIL: AUTH REJECTED``
  - Upgrade succeeds (101) and first ack matches join success → ``SUCCESS: JOIN OK``
    (ack = ``subscription_ack`` in payload / raw, or production ``[flow-alerts, {status: ok}]``)

Requires: ``websockets``, ``UW_API_KEY`` in the environment (e.g. from ``.env`` on the droplet).
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from uw_flow_ws import uw_ws_connect_config  # noqa: E402


def _join_ack_from_message(raw: str) -> bool:
    """True if this frame indicates a successful flow-alerts subscription ack."""
    low = raw.lower()
    if "subscription_ack" in low:
        return True
    try:
        msg: Any = json.loads(raw)
    except Exception:
        return False
    if isinstance(msg, list) and len(msg) >= 2:
        ch, data = msg[0], msg[1]
        if ch != "flow-alerts" or not isinstance(data, dict):
            return False
        if str(data.get("status", "")).lower() == "ok":
            return True
        if str(data.get("msg_type", "")).lower() in ("subscription_ack", "ack", "joined"):
            return True
    if isinstance(msg, dict):
        mt = str(msg.get("msg_type", "") or msg.get("type", "")).lower()
        if mt == "subscription_ack":
            return True
        if str(msg.get("status", "")).lower() == "ok" and msg.get("channel") == "flow-alerts":
            return True
    return False


async def _run() -> int:
    token = (os.getenv("UW_API_KEY") or "").strip()
    if not token:
        print("FAIL: UW_API_KEY not set", flush=True)
        return 2

    import websockets

    try:
        from websockets.exceptions import InvalidStatusCode as WSCInvalidStatus
    except Exception:  # pragma: no cover
        class WSCInvalidStatus(Exception):  # type: ignore[misc, no-redef]
            status_code: int = 0

    uri, hdr_list = uw_ws_connect_config(token)
    hdr_dict = dict(hdr_list) if hdr_list else None
    kw = dict(close_timeout=20, open_timeout=20, ping_interval=None)

    try:
        if hdr_dict:
            try:
                ctx = websockets.connect(uri, additional_headers=hdr_dict, **kw)
            except TypeError:
                ctx = websockets.connect(uri, extra_headers=hdr_dict, **kw)
        else:
            ctx = websockets.connect(uri, **kw)

        async with ctx as ws:
            # Successful ``async with`` means the server returned HTTP 101 Switching Protocols.
            await ws.send(json.dumps({"channel": "flow-alerts", "msg_type": "join"}))
            deadline = time.monotonic() + 30.0
            while time.monotonic() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=8.0)
                except asyncio.TimeoutError:
                    continue
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8", errors="replace")
                if not isinstance(raw, str):
                    continue
                if _join_ack_from_message(raw):
                    print("SUCCESS: JOIN OK", flush=True)
                    return 0
            print("FAIL: no subscription ack within timeout (upgrade succeeded)", flush=True)
            return 3

    except Exception as ex:
        # websockets: InvalidStatusCode on failed upgrade (e.g. 401)
        code = getattr(ex, "status_code", None)
        if code == 401 or (isinstance(ex, WSCInvalidStatus) and getattr(ex, "status_code", 0) == 401):
            print("FAIL: AUTH REJECTED", flush=True)
            return 1
        msg = str(ex)
        if "401" in msg and ("HTTP" in msg or "status" in msg.lower() or "InvalidStatus" in type(ex).__name__):
            print("FAIL: AUTH REJECTED", flush=True)
            return 1
        print(f"FAIL: {type(ex).__name__}: {ex}", flush=True)
        return 4


def main() -> int:
    return asyncio.run(_run())


if __name__ == "__main__":
    raise SystemExit(main())
