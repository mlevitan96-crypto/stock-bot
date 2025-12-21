#!/usr/bin/env python3
"""Check if trades are closing and being logged"""
import json
from pathlib import Path
from datetime import datetime

print("=" * 60)
print("TRADE CLOSING CHECK")
print("=" * 60)
print()

# Check exit logs
exit_log = Path("logs/exit.jsonl")
if exit_log.exists():
    with open(exit_log, 'r', encoding='utf-8') as f:
        lines = [l for l in f if l.strip()]
        print(f"[OK] Exit log exists: {len(lines)} exit events")
        if lines:
            # Show last 5 exits
            print("\nLast 5 exits:")
            for line in lines[-5:]:
                try:
                    rec = json.loads(line)
                    symbol = rec.get('symbol', 'UNKNOWN')
                    reason = rec.get('reason', 'unknown')
                    ts = rec.get('ts', '')
                    print(f"  {symbol}: {reason} ({ts})")
                except:
                    pass
else:
    print("[WARNING] No exit log found (logs/exit.jsonl)")

print()

# Check attribution logs
attr_log = Path("logs/attribution.jsonl")
if attr_log.exists():
    with open(attr_log, 'r', encoding='utf-8') as f:
        lines = [l for l in f if l.strip()]
        print(f"[OK] Attribution log exists: {len(lines)} closed trades")
        if lines:
            # Show last 5 trades
            print("\nLast 5 closed trades:")
            for line in lines[-5:]:
                try:
                    rec = json.loads(line)
                    if rec.get('type') == 'attribution':
                        symbol = rec.get('symbol', 'UNKNOWN')
                        pnl_pct = rec.get('pnl_pct', 0)
                        pnl_usd = rec.get('pnl_usd', 0)
                        ts = rec.get('ts', '')
                        print(f"  {symbol}: P&L={pnl_pct:.2f}% (${pnl_usd:.2f}) - {ts}")
                except:
                    pass
else:
    print("[WARNING] No attribution log found (logs/attribution.jsonl)")
    print("  This means either:")
    print("    1. No trades have closed yet")
    print("    2. log_exit_attribution() is not being called")

print()
