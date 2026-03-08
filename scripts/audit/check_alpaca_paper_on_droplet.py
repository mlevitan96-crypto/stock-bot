#!/usr/bin/env python3
"""Check Alpaca paper connectivity (read-only). Exit 0 on success; print NO_CREDENTIALS/NOT_PAPER_URL/ERROR on failure. Run on droplet."""
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
try:
    from dotenv import load_dotenv
    load_dotenv(REPO / ".env")
except ImportError:
    pass
try:
    from config.registry import get_env
    base = get_env("ALPACA_BASE_URL") or get_env("APCA_API_BASE_URL") or "https://paper-api.alpaca.markets"
    key = get_env("ALPACA_KEY") or get_env("APCA_API_KEY_ID")
    secret = get_env("ALPACA_SECRET") or get_env("APCA_API_SECRET_KEY")
    if not key or not secret:
        print("NO_CREDENTIALS")
        sys.exit(1)
    if "paper" not in (base or "").lower():
        print("NOT_PAPER_URL")
        sys.exit(1)
    from alpaca_client import AlpacaClient
    c = AlpacaClient(key, secret, base)
    acc = c.api.get_account()
    clk = c.api.get_clock()
    print("ACCOUNT_OK", getattr(acc, "status", "ok"))
    print("CLOCK_OK", getattr(clk, "is_open", "ok"))
except Exception as e:
    print("ERROR", str(e))
    sys.exit(1)
