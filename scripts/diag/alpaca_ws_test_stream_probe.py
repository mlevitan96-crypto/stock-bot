#!/usr/bin/env python3
"""Probe sandbox v2/test market-data WebSocket (FAKEPACA); isolates auth vs feed entitlement."""
from __future__ import annotations

import asyncio
import inspect
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


async def main() -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv(REPO / ".env")
    except Exception:
        pass
    from config.registry import get_alpaca_trading_credentials
    from src.alpaca.stream_feed import alpaca_market_data_ws_handshake_headers

    import websockets

    k, s, _ = get_alpaca_trading_credentials()
    # Retail keys authenticate to production MD cluster (FAQ); /v2/test works outside RTH.
    url = "wss://stream.data.alpaca.markets/v2/test"
    hdrs = alpaca_market_data_ws_handshake_headers(k, s)
    opts = dict(ping_interval=20, ping_timeout=20, close_timeout=5, max_size=2**23)
    sig = inspect.signature(websockets.connect)
    if "additional_headers" in sig.parameters:
        cm = websockets.connect(url, additional_headers=hdrs, **opts)
    elif "extra_headers" in sig.parameters:
        cm = websockets.connect(url, extra_headers=hdrs, **opts)
    else:
        cm = websockets.connect(url, **opts)
    async with cm as ws:
        r0 = await asyncio.wait_for(ws.recv(), 15)
        await ws.send(json.dumps({"action": "auth", "key": k, "secret": s}))
        r1 = await asyncio.wait_for(ws.recv(), 15)
    print("recv0", r0[:300])
    print("recv1", r1[:300])
    ok = "authenticated" in r1.lower() and "success" in r1.lower()
    print("test_stream_authenticated", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
