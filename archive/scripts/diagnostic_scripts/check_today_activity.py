#!/usr/bin/env python3
"""Check today's trading activity"""
from pathlib import Path
import json
from datetime import datetime

today_str = datetime.now().strftime("%Y-%m-%d")
print(f"Checking activity for {today_str}...\n")

# Check attribution logs
attr_file = Path("logs/attribution.jsonl")
if attr_file.exists():
    lines = attr_file.read_text().splitlines()
    today_entries = [json.loads(l) for l in lines if l.strip() and json.loads(l).get("ts", "").startswith(today_str)]
    entries = [e for e in today_entries if e.get("type") == "attribution" and "open_" in e.get("trade_id", "")]
    exits = [e for e in today_entries if e.get("type") == "attribution" and "close_" in e.get("trade_id", "")]
    
    print(f"Attribution Logs:")
    print(f"  Total today entries: {len(today_entries)}")
    print(f"  Trade entries: {len(entries)}")
    print(f"  Trade exits: {len(exits)}")
    if entries:
        print(f"\n  Recent entries:")
        for e in entries[-5:]:
            symbol = e.get("symbol", "N/A")
            score = e.get("context", {}).get("score", 0)
            ts = e.get("ts", "")[:19]
            print(f"    {ts} - {symbol} (score: {score:.2f})")
    if exits:
        print(f"\n  Recent exits:")
        for e in exits[-5:]:
            symbol = e.get("symbol", "N/A")
            pnl = e.get("pnl_usd", 0)
            ts = e.get("ts", "")[:19]
            print(f"    {ts} - {symbol} (P&L: ${pnl:.2f})")

# Check XAI logs
xai_file = Path("data/explainable_logs.jsonl")
if xai_file.exists():
    lines = xai_file.read_text().splitlines()
    today_xai = [json.loads(l) for l in lines if l.strip() and json.loads(l).get("timestamp", "").startswith(today_str)]
    xai_entries = [x for x in today_xai if x.get("type") == "trade_entry"]
    xai_exits = [x for x in today_xai if x.get("type") == "trade_exit"]
    
    print(f"\nXAI Logs:")
    print(f"  Total today: {len(today_xai)}")
    print(f"  Entries: {len(xai_entries)}")
    print(f"  Exits: {len(xai_exits)}")

print("\n✅ Activity check complete!")
