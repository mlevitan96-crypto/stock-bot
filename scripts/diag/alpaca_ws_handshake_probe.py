#!/usr/bin/env python3
"""
~10s Alpaca market-data WebSocket handshake probe (connected + auth response).

Uses canonical credentials from config.registry.get_alpaca_trading_credentials.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

HANDSHAKE_TIMEOUT_SEC = 10.0


async def _run(*, feed: str) -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv(REPO / ".env")
    except Exception:
        pass
    from config.registry import get_alpaca_trading_credentials
    from src.alpaca.stream_feed import alpaca_trading_environment, stream_data_ws_url

    try:
        import websockets
    except ImportError:
        print("ERROR: pip install websockets")
        return 2

    key, secret, base = get_alpaca_trading_credentials()
    if not key or not secret:
        print("ERROR: missing Alpaca credentials after canonical resolve")
        return 2

    env_label = alpaca_trading_environment(base)
    paper_fb = env_label == "paper" or (env_label == "unknown" and "paper-api" in base.lower())
    url = stream_data_ws_url(trading_base_url=base, feed=feed, paper=paper_fb)
    print("--- Credential audit (no secrets) ---")
    print(f"  trading_environment={env_label!r}")
    print(f"  key_id_prefix={key[:8]}…" if len(key) >= 8 else f"  key_id_prefix={key!r}")
    print(f"  ws_url={url!r}")
    print()

    async def inner() -> tuple[bool, str]:
        async with websockets.connect(
            url,
            ping_interval=20,
            ping_timeout=20,
            close_timeout=5,
            max_size=2**23,
        ) as ws:
            raw0 = await asyncio.wait_for(ws.recv(), timeout=HANDSHAKE_TIMEOUT_SEC)
            await ws.send(json.dumps({"action": "auth", "key": key, "secret": secret}))
            raw1 = await asyncio.wait_for(ws.recv(), timeout=HANDSHAKE_TIMEOUT_SEC)
            ok = False
            try:
                data = json.loads(raw1)
                items = data if isinstance(data, list) else [data]
                for o in items:
                    if isinstance(o, dict) and o.get("T") == "success":
                        if "authenticated" in str(o.get("msg", "")).lower():
                            ok = True
            except json.JSONDecodeError:
                pass
            return ok, raw1

    try:
        authed, raw1 = await inner()
    except Exception as e:
        print(f"--- Handshake result: EXCEPTION ---")
        print(f"  {type(e).__name__}: {e}")
        return 1

    print("--- Handshake result ---")
    print(f"  authenticated={authed}")
    print(f"  auth_response={raw1[:500]!r}")
    return 0 if authed else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feed", default="iex", choices=("sip", "iex"), help="Feed path to probe")
    args = ap.parse_args()
    return asyncio.run(_run(feed=args.feed))


if __name__ == "__main__":
    raise SystemExit(main())
