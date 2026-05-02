#!/usr/bin/env python3
"""
Wheel broker reconciliation + HUD sink refresh.

Run every 15 minutes (systemd timer): promotes CSP→assigned when broker shows stock without
short put; detects state/broker drift; writes ``state/wheel_dashboard_sink.json``.
Exit 0 on success (suitable for OnFailure= logging only).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
try:
    os.chdir(ROOT)
except Exception:
    pass


def main() -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except Exception:
        pass
    for env_path in (Path("/root/stock-bot/.env"), ROOT / ".env"):
        try:
            from dotenv import load_dotenv

            if env_path.exists():
                load_dotenv(env_path, override=False)
        except Exception:
            pass

    key = os.getenv("ALPACA_KEY") or os.getenv("APCA_API_KEY_ID")
    secret = os.getenv("ALPACA_SECRET") or os.getenv("APCA_API_SECRET_KEY")
    base = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    if not key or not secret:
        print("wheel_broker_reconcile: missing Alpaca credentials", flush=True)
        return 1

    try:
        import alpaca_trade_api as tradeapi  # type: ignore

        api = tradeapi.REST(str(key), str(secret), str(base), api_version="v2")
    except Exception as e:
        print(f"wheel_broker_reconcile: REST init failed: {e}", flush=True)
        return 1

    import strategies.wheel_strategy as ws
    from src.wheel_manager import (
        detect_wheel_broker_drift,
        reconcile_assignments_from_broker,
        refresh_wheel_dashboard_sink,
    )

    st = ws._load_wheel_state()
    reconcile_assignments_from_broker(api, st)
    drift = detect_wheel_broker_drift(api, ws._load_wheel_state())
    refresh_wheel_dashboard_sink(api, drift_alerts=drift)
    print("wheel_broker_reconcile: ok", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
