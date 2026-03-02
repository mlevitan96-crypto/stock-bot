#!/usr/bin/env python3
"""Confirm trades/orders on droplet: trade_intent entered and latest complete cycle."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from droplet_client import DropletClient

def get_root(c):
    out, _, _ = c._execute(
        "([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot",
        timeout=10,
    )
    return (out or "/root/stock-bot").strip().splitlines()[-1].strip()

with DropletClient() as c:
    root = get_root(c)
    out, _, _ = c._execute("tail -300 " + root + "/logs/run.jsonl")
    lines = [s.strip() for s in (out or "").splitlines() if s.strip()]
    entered = 0
    complete_clusters = complete_orders = None
    complete_ts = None
    for line in lines:
        try:
            rec = json.loads(line)
            if rec.get("event_type") == "trade_intent" and rec.get("decision_outcome") == "entered":
                entered += 1
            if rec.get("msg") == "complete":
                complete_clusters = rec.get("clusters")
                complete_orders = rec.get("orders")
                complete_ts = rec.get("ts")
        except Exception:
            pass
    print("Trade intents 'entered' (last 300 lines):", entered)
    print("Latest 'complete' cycle: clusters=", complete_clusters, " orders=", complete_orders, " ts=", complete_ts)
    sys.exit(0 if (entered > 0 or (complete_orders is not None and complete_orders > 0)) else 1)
