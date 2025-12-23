#!/usr/bin/env python3
"""
Comprehensive System Check
Checks ALL system components to identify why bot isn't working
"""

import json
import time
import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

def check_bot_process():
    """Check if bot process is actually running"""
    print("=" * 80)
    print("BOT PROCESS CHECK")
    print("=" * 80)
    
    # Check multiple ways
    methods = {
        "pgrep python.*main.py": subprocess.run(["pgrep", "-f", "python.*main.py"], capture_output=True),
        "pgrep main.py": subprocess.run(["pgrep", "-f", "main.py"], capture_output=True),
        "ps aux": subprocess.run(["ps", "aux"], capture_output=True, text=True)
    }
    
    found = False
    for method, result in methods.items():
        if method == "ps aux":
            if "main.py" in result.stdout:
                found = True
                print(f"\n✓ Bot process found via {method}")
                # Extract relevant lines
                for line in result.stdout.split('\n'):
                    if "main.py" in line and "grep" not in line:
                        print(f"  {line[:100]}")
                break
        else:
            if result.returncode == 0 and result.stdout:
                pids = result.stdout.decode().strip().split('\n')
                if pids and pids[0]:
                    found = True
                    print(f"\n✓ Bot process found via {method}")
                    print(f"  PID: {pids[0]}")
                    break
    
    if not found:
        print("\n❌ Bot process NOT FOUND")
        print("  Bot is not running!")
        return False
    
    # Check if health endpoint responds
    try:
        import requests
        resp = requests.get("http://localhost:8081/health", timeout=2)
        if resp.status_code == 200:
            print("  ✓ Health endpoint responding")
            data = resp.json()
            print(f"  Status: {data.get('status', 'unknown')}")
            print(f"  Last heartbeat: {data.get('last_heartbeat_age_sec', 'unknown')}s ago")
            print(f"  Iter count: {data.get('iter_count', 0)}")
        else:
            print(f"  ⚠️  Health endpoint returned {resp.status_code}")
    except Exception as e:
        print(f"  ⚠️  Health endpoint not responding: {e}")
    
    return True

def check_worker_thread():
    """Check if worker thread is running"""
    print("\n" + "=" * 80)
    print("WORKER THREAD CHECK")
    print("=" * 80)
    
    # Check heartbeat file
    heartbeat_file = Path("state/bot_heartbeat.json")
    if heartbeat_file.exists():
        try:
            with open(heartbeat_file, 'r') as f:
                hb = json.load(f)
            last_hb = hb.get("last_heartbeat", 0)
            age = time.time() - last_hb
            print(f"\nLast heartbeat: {int(age)}s ago")
            if age > 300:
                print("  ⚠️  WARNING: Heartbeat is stale (>5 minutes)")
            else:
                print("  ✓ Heartbeat is fresh")
            print(f"  Iter count: {hb.get('iter_count', 0)}")
            print(f"  Fail count: {hb.get('fail_count', 0)}")
        except Exception as e:
            print(f"  Error reading heartbeat: {e}")
    else:
        print("\n❌ Heartbeat file not found")
        print("  Worker thread may not be running")
    
    # Check run.jsonl for recent cycles
    run_file = Path("logs/run.jsonl")
    if run_file.exists():
        try:
            with open(run_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    rec = json.loads(last_line)
                    ts = rec.get("ts", rec.get("_ts", 0))
                    age = time.time() - ts
                    print(f"\nLast run cycle: {int(age)}s ago")
                    if age > 600:
                        print("  ⚠️  WARNING: No cycles in last 10 minutes")
                    print(f"  Clusters: {rec.get('clusters', 0)}")
                    print(f"  Orders: {rec.get('orders', 0)}")
        except Exception as e:
            print(f"  Error reading run.jsonl: {e}")
    else:
        print("\n❌ run.jsonl not found")
        print("  Bot may not be logging cycles")

def check_uw_daemon():
    """Check UW daemon status"""
    print("\n" + "=" * 80)
    print("UW DAEMON CHECK")
    print("=" * 80)
    
    # Check process
    result = subprocess.run(["pgrep", "-f", "uw_flow_daemon"], capture_output=True)
    if result.returncode == 0:
        print("\n✓ UW daemon process running")
    else:
        print("\n❌ UW daemon process NOT running")
        print("  This is why endpoints are stale!")
    
    # Check cache freshness
    cache_file = Path("data/uw_flow_cache.json")
    if cache_file.exists():
        age = time.time() - cache_file.stat().st_mtime
        print(f"\nCache age: {int(age)}s ({int(age/60)} minutes)")
        if age < 300:
            print("  ✓ Cache is fresh")
        elif age < 600:
            print("  ⚠️  Cache is getting stale")
        else:
            print("  ❌ Cache is STALE - UW daemon not updating")
        
        # Check cache content
        try:
            with open(cache_file, 'r') as f:
                cache = json.load(f)
            symbols = [k for k in cache.keys() if not k.startswith("_")]
            print(f"  Symbols in cache: {len(symbols)}")
        except Exception as e:
            print(f"  Error reading cache: {e}")
    else:
        print("\n❌ Cache file not found")
        print("  UW daemon may not be running")

def check_uw_endpoints_detailed():
    """Check why UW endpoints show as stale"""
    print("\n" + "=" * 80)
    print("UW ENDPOINT STALENESS ANALYSIS")
    print("=" * 80)
    
    # Check UW daemon logs
    daemon_log = Path("logs/uw_flow_daemon.log")
    if daemon_log.exists():
        try:
            with open(daemon_log, 'r') as f:
                lines = f.readlines()
                if lines:
                    print(f"\nLast {min(10, len(lines))} lines from UW daemon log:")
                    for line in lines[-10:]:
                        print(f"  {line.rstrip()[:100]}")
        except:
            pass
    
    # Check UW error log
    error_log = Path("data/uw_error.jsonl")
    if error_log.exists():
        try:
            with open(error_log, 'r') as f:
                lines = f.readlines()
                if lines:
                    print(f"\nRecent UW errors ({len(lines[-20:])} lines):")
                    for line in lines[-5:]:
                        try:
                            rec = json.loads(line)
                            print(f"  {rec.get('error', 'unknown')[:80]}")
                        except:
                            pass
        except:
            pass
    
    # Check UW API quota
    quota_file = Path("data/uw_api_quota.jsonl")
    if quota_file.exists():
        try:
            with open(quota_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    last = json.loads(lines[-1])
                    print(f"\nUW API Quota:")
                    print(f"  Remaining: {last.get('remaining', 'unknown')}")
                    print(f"  Reset at: {last.get('reset_at', 'unknown')}")
        except:
            pass

def check_market_status():
    """Check if market is open"""
    print("\n" + "=" * 80)
    print("MARKET STATUS")
    print("=" * 80)
    
    try:
        from main import is_market_open_now
        market_open = is_market_open_now()
        print(f"\nMarket open: {market_open}")
        if not market_open:
            print("  (This is normal - bot may not execute cycles when market is closed)")
    except Exception as e:
        print(f"\nError checking market: {e}")

def check_freeze_state():
    """Check if bot is frozen"""
    print("\n" + "=" * 80)
    print("FREEZE STATE CHECK")
    print("=" * 80)
    
    freeze_file = Path("state/governor_freezes.json")
    if freeze_file.exists():
        try:
            with open(freeze_file, 'r') as f:
                freezes = json.load(f)
            print(f"\nFreeze states:")
            for key, value in freezes.items():
                status = "ACTIVE" if value else "INACTIVE"
                print(f"  {key}: {status}")
                if value:
                    print(f"    ⚠️  WARNING: {key} is ACTIVE - trading may be halted")
        except Exception as e:
            print(f"  Error reading freezes: {e}")
    else:
        print("\n✓ No freeze file found (no freezes active)")

def check_recent_activity():
    """Check all recent activity"""
    print("\n" + "=" * 80)
    print("RECENT ACTIVITY (Last 24 Hours)")
    print("=" * 80)
    
    files_to_check = {
        "Signals": Path("logs/signals.jsonl"),
        "Orders": Path("logs/orders.jsonl"),
        "Exits": Path("logs/exit.jsonl"),
        "Attribution": Path("logs/attribution.jsonl"),
        "Gate Events": Path("logs/gate.jsonl"),
        "Blocked Trades": Path("state/blocked_trades.jsonl"),
    }
    
    cutoff = time.time() - 86400
    
    for name, path in files_to_check.items():
        if path.exists():
            try:
                count = 0
                with open(path, 'r') as f:
                    for line in f:
                        try:
                            rec = json.loads(line)
                            ts = rec.get("ts", rec.get("_ts", 0))
                            # Handle both numeric and string timestamps
                            if isinstance(ts, str):
                                try:
                                    from datetime import datetime
                                    ts_dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                                    ts = ts_dt.timestamp()
                                except:
                                    continue
                            if isinstance(ts, (int, float)) and ts > cutoff:
                                count += 1
                        except:
                            pass
                print(f"\n{name}: {count} events in last 24h")
            except Exception as e:
                print(f"\n{name}: Error reading - {e}")
        else:
            print(f"\n{name}: File not found")
    
    # Suppress any daemon thread output that might cause crashes
    import sys
    sys.stdout.flush()
    sys.stderr.flush()

def main():
    try:
        print("=" * 80)
        print("COMPREHENSIVE SYSTEM CHECK")
        print("=" * 80)
        print(f"\nTime: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        
        bot_running = check_bot_process()
        check_worker_thread()
        check_uw_daemon()
        check_uw_endpoints_detailed()
        check_market_status()
        check_freeze_state()
        check_recent_activity()
        
        print("\n" + "=" * 80)
        print("SUMMARY & RECOMMENDATIONS")
        print("=" * 80)
        
        if not bot_running:
            print("\n❌ CRITICAL: Bot process is not running")
            print("  Fix: Restart bot with ./RESTART_BOT_NOW.sh")
        else:
            print("\n✓ Bot process is running")
            print("  If no cycles, check:")
            print("  1. Worker thread status (heartbeat)")
            print("  2. Freeze state")
            print("  3. Market status")
            print("  4. UW daemon status")
    except Exception as e:
        print(f"\nError in diagnostic: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean exit to avoid daemon thread issues
        import sys
        sys.stdout.flush()
        sys.stderr.flush()

if __name__ == "__main__":
    main()
