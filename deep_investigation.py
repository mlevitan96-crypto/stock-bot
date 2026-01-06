#!/usr/bin/env python3
"""Deep investigation of why cycles aren't running"""

import json
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, '/root/stock-bot')

print("=" * 80)
print("DEEP INVESTIGATION - WHY NO CYCLES")
print("=" * 80)

# 1. Check if run_once can be called manually
print("\n1. TESTING RUN_ONCE MANUALLY:")
try:
    print("   Importing main...")
    from main import run_once, is_market_open_now
    print("   Import: SUCCESS")
    
    print("\n   Testing market check...")
    try:
        market_open = is_market_open_now()
        print(f"   Market open: {market_open}")
    except Exception as e:
        print(f"   Market check ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n   Attempting to call run_once()...")
    try:
        start = time.time()
        result = run_once()
        elapsed = time.time() - start
        print(f"   run_once() completed in {elapsed:.1f}s")
        print(f"   Result: clusters={result.get('clusters', 0)}, orders={result.get('orders', 0)}")
        if 'error' in result:
            print(f"   ERROR in result: {result.get('error')}")
    except Exception as e:
        print(f"   run_once() FAILED: {e}")
        import traceback
        traceback.print_exc()
except Exception as e:
    print(f"   Import FAILED: {e}")
    import traceback
    traceback.print_exc()

# 2. Check worker loop directly
print("\n2. CHECKING WORKER LOOP:")
try:
    from main import watchdog
    if watchdog:
        print(f"   Watchdog exists: YES")
        print(f"   Thread alive: {watchdog.thread.is_alive() if watchdog.thread else 'NO THREAD'}")
        print(f"   Running: {watchdog.state.running}")
        print(f"   Iter count: {watchdog.state.iter_count}")
        print(f"   Fail count: {watchdog.state.fail_count}")
    else:
        print("   Watchdog: NOT FOUND")
except Exception as e:
    print(f"   Error checking watchdog: {e}")

# 3. Check recent system logs for patterns
print("\n3. ANALYZING RECENT LOGS:")
sys_file = Path("logs/system.jsonl")
if sys_file.exists():
    with open(sys_file) as f:
        lines = f.readlines()
        recent = [json.loads(l) for l in lines[-500:] if l.strip()]
        
        worker_starts = [e for e in recent if 'worker' in e.get('msg', '').lower() and 'start' in e.get('msg', '').lower()]
        iter_starts = [e for e in recent if 'iter_start' in e.get('msg', '').lower()]
        iter_ends = [e for e in recent if 'iter_end' in e.get('msg', '').lower()]
        run_events = [e for e in recent if 'run_once' in str(e).lower() or 'run' in e.get('msg', '').lower()]
        errors = [e for e in recent if 'error' in str(e).lower() or 'exception' in str(e).lower()]
        
        print(f"   Worker starts: {len(worker_starts)}")
        if worker_starts:
            print(f"     Latest: {worker_starts[-1].get('ts', 'N/A')[:19]}")
        
        print(f"   Iter starts: {len(iter_starts)}")
        if iter_starts:
            print(f"     Latest: {iter_starts[-1].get('ts', 'N/A')[:19]} (iter {iter_starts[-1].get('iter', '?')})")
        
        print(f"   Iter ends: {len(iter_ends)}")
        if iter_ends:
            print(f"     Latest: {iter_ends[-1].get('ts', 'N/A')[:19]} (iter {iter_ends[-1].get('iter', '?')})")
        
        print(f"   Run events: {len(run_events)}")
        if run_events:
            print(f"     Latest: {run_events[-1].get('ts', 'N/A')[:19]}")
        
        print(f"   Errors: {len(errors)}")
        if errors:
            print(f"     Latest 5 errors:")
            for e in errors[-5:]:
                msg = e.get('msg', '') or e.get('event', '')
                err = e.get('error', '')
                print(f"       {e.get('ts', 'N/A')[:19]}: {msg} - {err[:150]}")

# 4. Check run.jsonl vs heartbeat
print("\n4. TIMING ANALYSIS:")
run_file = Path("logs/run.jsonl")
hb_file = Path("state/bot_heartbeat.json")

if run_file.exists() and hb_file.exists():
    with open(run_file) as f:
        run_lines = f.readlines()
        if run_lines:
            latest_run = json.loads(run_lines[-1])
            run_ts = latest_run.get("ts", "")
    
    hb = json.load(open(hb_file))
    hb_ts = hb.get("last_heartbeat_dt", "")
    iter_count = hb.get("iter_count", 0)
    
    print(f"   Latest run.jsonl: {run_ts[:19]}")
    print(f"   Latest heartbeat: {hb_ts}")
    print(f"   Iter count: {iter_count}")
    
    if run_ts:
        try:
            run_dt = datetime.fromisoformat(run_ts.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            age = (now - run_dt.replace(tzinfo=timezone.utc)).total_seconds() / 60
            print(f"   Age of last cycle: {age:.1f} minutes")
            print(f"   Expected cycles since: {int(age)} (should be ~{int(age)} cycles in {age:.1f} min)")
        except:
            pass

print("\n" + "=" * 80)
