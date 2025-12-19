#!/usr/bin/env python3
"""
Diagnose why clusters generate but no orders are placed
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone

LOGS_DIR = Path("logs")
STATE_DIR = Path("state")

print("=" * 80)
print("WHY NO ORDERS? - CLUSTER TO ORDER ANALYSIS")
print("=" * 80)
print()

# 1. Check recent clusters
print("1. RECENT CLUSTERS")
print("-" * 80)
run_file = LOGS_DIR / "run.jsonl"
if run_file.exists():
    now = time.time()
    lines = run_file.read_text().splitlines()
    if lines:
        last_run = json.loads(lines[-1])
        clusters = last_run.get("clusters", 0)
        orders = last_run.get("orders", 0)
        print(f"Last cycle: {clusters} clusters → {orders} orders")
        print(f"  Conversion rate: {(orders/clusters*100) if clusters > 0 else 0:.1f}%")
        if clusters > 0 and orders == 0:
            print("  ❌ CRITICAL: Clusters generated but NO orders placed")
    else:
        print("No cycles found")
print()

# 2. Check gate logs (why clusters are blocked)
print("2. GATE BLOCKS (Why clusters aren't becoming orders)")
print("-" * 80)
gate_file = LOGS_DIR / "gate.jsonl"
if gate_file.exists():
    now = time.time()
    cutoff_1h = now - 3600
    
    blocks_1h = {}
    for line in gate_file.read_text().splitlines()[-100:]:
        try:
            event = json.loads(line.strip())
            if event.get("_ts", 0) > cutoff_1h:
                reason = event.get("msg", "unknown")
                symbol = event.get("symbol", "unknown")
                if reason not in blocks_1h:
                    blocks_1h[reason] = []
                blocks_1h[reason].append(symbol)
        except:
            pass
    
    if blocks_1h:
        print(f"Blocks in last hour: {sum(len(v) for v in blocks_1h.values())}")
        for reason, symbols in sorted(blocks_1h.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  {reason}: {len(symbols)} times")
            if len(symbols) <= 5:
                print(f"    Symbols: {', '.join(symbols)}")
    else:
        print("No gate blocks in last hour")
else:
    print("Gate log does not exist")
print()

# 3. Check blocked trades
print("3. BLOCKED TRADES")
print("-" * 80)
blocked_file = STATE_DIR / "blocked_trades.jsonl"
if blocked_file.exists():
    now = time.time()
    cutoff_1h = now - 3600
    
    blocks_1h = {}
    for line in blocked_file.read_text().splitlines()[-50:]:
        try:
            event = json.loads(line.strip())
            if event.get("_ts", 0) > cutoff_1h:
                reason = event.get("reason", "unknown")
                symbol = event.get("symbol", "unknown")
                score = event.get("score", 0)
                if reason not in blocks_1h:
                    blocks_1h[reason] = []
                blocks_1h[reason].append((symbol, score))
        except:
            pass
    
    if blocks_1h:
        print(f"Trades blocked in last hour: {sum(len(v) for v in blocks_1h.values())}")
        for reason, items in sorted(blocks_1h.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  {reason}: {len(items)} times")
            if len(items) <= 3:
                for symbol, score in items:
                    print(f"    {symbol}: score={score:.2f}")
    else:
        print("No blocked trades in last hour")
else:
    print("Blocked trades file does not exist")
print()

# 4. Check decisions (what the bot decided)
print("4. RECENT DECISIONS")
print("-" * 80)
decisions_file = LOGS_DIR / "decisions.jsonl"
if decisions_file.exists():
    now = time.time()
    cutoff_1h = now - 3600
    
    decisions_1h = []
    for line in decisions_file.read_text().splitlines()[-50:]:
        try:
            event = json.loads(line.strip())
            if event.get("_ts", 0) > cutoff_1h:
                decisions_1h.append(event)
        except:
            pass
    
    print(f"Decisions in last hour: {len(decisions_1h)}")
    if decisions_1h:
        for d in decisions_1h[-5:]:
            symbol = d.get("symbol", "unknown")
            action = d.get("action", "unknown")
            score = d.get("score", 0)
            print(f"  {symbol}: {action} (score: {score:.2f})")
    else:
        print("  ⚠️  No decisions in last hour")
else:
    print("Decisions log does not exist")
print()

# 5. Check execution logs
print("5. EXECUTION LOGS")
print("-" * 80)
execution_file = LOGS_DIR / "execution.jsonl"
if execution_file.exists():
    now = time.time()
    cutoff_1h = now - 3600
    
    executions_1h = []
    for line in execution_file.read_text().splitlines()[-50:]:
        try:
            event = json.loads(line.strip())
            if event.get("_ts", 0) > cutoff_1h:
                executions_1h.append(event)
        except:
            pass
    
    print(f"Executions in last hour: {len(executions_1h)}")
    if executions_1h:
        for e in executions_1h[-5:]:
            symbol = e.get("symbol", "unknown")
            action = e.get("action", "unknown")
            print(f"  {symbol}: {action}")
    else:
        print("  ⚠️  No executions in last hour")
else:
    print("Execution log does not exist")
print()

# 6. Check if at max positions
print("6. POSITION STATUS")
print("-" * 80)
try:
    import os
    import alpaca_trade_api as tradeapi
    key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY", "")
    secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET", "")
    base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    
    if key and secret:
        api = tradeapi.REST(key, secret, base_url)
        positions = api.list_positions()
        print(f"Current positions: {len(positions)}")
        
        # Check max positions config
        try:
            from main import Config
            max_pos = Config.MAX_CONCURRENT_POSITIONS
            print(f"Max positions: {max_pos}")
            if len(positions) >= max_pos:
                print(f"  ❌ AT MAX POSITIONS ({len(positions)}/{max_pos}) - blocking new entries")
            else:
                print(f"  ✅ Below max ({len(positions)}/{max_pos}) - can add positions")
        except:
            print("  ⚠️  Could not check max positions config")
    else:
        print("⚠️  Alpaca credentials not available")
except Exception as e:
    print(f"⚠️  Could not check positions: {e}")
print()

# 7. Check recent composite scores
print("7. COMPOSITE SCORES")
print("-" * 80)
composite_file = LOGS_DIR / "composite_filter.jsonl"
if composite_file.exists():
    now = time.time()
    cutoff_1h = now - 3600
    
    scores_1h = []
    for line in composite_file.read_text().splitlines()[-50:]:
        try:
            event = json.loads(line.strip())
            if event.get("_ts", 0) > cutoff_1h:
                score = event.get("score", 0)
                symbol = event.get("symbol", "unknown")
                passed = event.get("passed", False)
                scores_1h.append((symbol, score, passed))
        except:
            pass
    
    if scores_1h:
        print(f"Composite scores in last hour: {len(scores_1h)}")
        passed = [s for s in scores_1h if s[2]]
        failed = [s for s in scores_1h if not s[2]]
        print(f"  Passed: {len(passed)}, Failed: {len(failed)}")
        if passed:
            print("  Top passed scores:")
            for symbol, score, _ in sorted(passed, key=lambda x: x[1], reverse=True)[:5]:
                print(f"    {symbol}: {score:.2f}")
    else:
        print("No composite scores in last hour")
else:
    print("Composite filter log does not exist")
print()

print("=" * 80)
print("DIAGNOSIS COMPLETE")
print("=" * 80)
print()
print("KEY FINDINGS:")
print("  - If clusters > 0 but orders = 0: Something is blocking ALL orders")
print("  - Check gate logs for block reasons")
print("  - Check if at max positions")
print("  - Check composite scores (are they passing thresholds?)")
print()
