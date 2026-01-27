#!/usr/bin/env python3
"""
Execute Comprehensive Trading Bot Audit on Droplet
===================================================
This script connects to the droplet and runs the comprehensive audit inline.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Inline audit script that can be executed directly
AUDIT_SCRIPT = '''python3 << 'AUDIT_EOF'
import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except:
        return "", "", -1

def check_process(name):
    stdout, _, code = run_cmd(f"pgrep -f '{name}'")
    pids = [p for p in stdout.split('\\n') if p.strip()]
    return {"running": len(pids) > 0, "pids": pids, "count": len(pids)}

def check_file_recent(path_str, max_min=60):
    path = Path(path_str)
    if not path.exists():
        return {"exists": False}
    try:
        mtime = path.stat().st_mtime
        age_min = (time.time() - mtime) / 60.0
        return {"exists": True, "recent": age_min <= max_min, "age_min": round(age_min, 2), "size": path.stat().st_size}
    except:
        return {"exists": True, "error": "stat failed"}

def count_jsonl(path_str, max_min=60):
    path = Path(path_str)
    if not path.exists():
        return {"exists": False, "total": 0, "recent": 0}
    try:
        now = time.time()
        total = recent = 0
        with open(path, 'r') as f:
            for line in f:
                if line.strip():
                    total += 1
                    try:
                        entry = json.loads(line)
                        ts = entry.get("ts") or entry.get("_ts")
                        if ts:
                            if isinstance(ts, (int, float)):
                                entry_time = ts
                            else:
                                from datetime import datetime
                                entry_time = datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp()
                            if (now - entry_time) / 60.0 <= max_min:
                                recent += 1
                    except:
                        pass
        return {"exists": True, "total": total, "recent": recent}
    except:
        return {"exists": True, "total": 0, "recent": 0}

results = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "processes": {},
    "files": {},
    "logs": {},
    "cache": {},
    "issues": []
}

# Check processes
print("=== PROCESSES ===")
for proc in ["deploy_supervisor.py", "uw_flow_daemon.py", "main.py", "dashboard.py"]:
    status = check_process(proc)
    results["processes"][proc] = status
    print(f"{proc}: {'RUNNING' if status['running'] else 'NOT RUNNING'} (PIDs: {status['pids']})")
    if not status['running']:
        results["issues"].append(f"Process not running: {proc}")

# Check files
print("\\n=== FILES ===")
for name, path in [("uw_cache", "data/uw_flow_cache.json"), ("position_metadata", "state/position_metadata.json"), ("bot_heartbeat", "state/bot_heartbeat.json")]:
    status = check_file_recent(path)
    results["files"][name] = status
    if status.get("exists"):
        age = status.get("age_min", "?")
        print(f"{name}: EXISTS (age: {age} min)")
        if not status.get("recent", False):
            results["issues"].append(f"File stale: {name}")
    else:
        print(f"{name}: MISSING")
        results["issues"].append(f"File missing: {name}")

# Check logs
print("\\n=== LOGS ===")
for name, path in [("attribution", "logs/attribution.jsonl"), ("run", "logs/run.jsonl"), ("orders", "logs/orders.jsonl"), ("exit", "logs/exit.jsonl"), ("gate", "logs/gate.jsonl")]:
    status = count_jsonl(path)
    results["logs"][name] = status
    if status.get("exists"):
        print(f"{name}: {status['total']} total, {status['recent']} recent")
        if status['recent'] == 0 and status['total'] > 0:
            results["issues"].append(f"Log has no recent entries: {name}")
    else:
        print(f"{name}: MISSING")
        results["issues"].append(f"Log missing: {name}")

# Check cache
print("\\n=== CACHE ===")
cache_path = Path("data/uw_flow_cache.json")
if cache_path.exists():
    try:
        with open(cache_path, 'r') as f:
            cache = json.load(f)
        symbols = [k for k in cache.keys() if not k.startswith("_")]
        results["cache"] = {"exists": True, "symbol_count": len(symbols)}
        print(f"Cache: {len(symbols)} symbols")
        if len(symbols) == 0:
            results["issues"].append("Cache has no symbols")
    except Exception as e:
        results["cache"] = {"exists": True, "error": str(e)}
        results["issues"].append(f"Cache error: {e}")
else:
    results["cache"] = {"exists": False}
    results["issues"].append("Cache missing")

# Check recent trades
print("\\n=== RECENT TRADES ===")
attr_path = Path("logs/attribution.jsonl")
if attr_path.exists():
    try:
        now = time.time()
        recent = []
        with open(attr_path, 'r') as f:
            lines = f.readlines()
            for line in lines[-50:]:
                try:
                    entry = json.loads(line.strip())
                    ts = entry.get("ts")
                    if ts:
                        if isinstance(ts, str):
                            entry_time = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                        else:
                            entry_time = ts
                        age_min = (now - entry_time) / 60.0
                        if age_min <= 120:
                            recent.append({"symbol": entry.get("symbol"), "age_min": round(age_min, 1), "pnl": entry.get("pnl_pct")})
                except:
                    pass
        print(f"Recent trades (last 2h): {len(recent)}")
        for t in recent[:5]:
            print(f"  {t['symbol']}: {t['age_min']:.1f} min ago, P&L: {t.get('pnl', 'N/A')}%")
        results["recent_trades"] = recent
    except Exception as e:
        print(f"Error checking trades: {e}")

print("\\n=== SUMMARY ===")
print(f"Issues: {len(results['issues'])}")
for issue in results['issues']:
    print(f"  - {issue}")

# Output JSON
print("\\n=== JSON RESULTS ===")
print(json.dumps(results, indent=2))
AUDIT_EOF
'''

def main():
    """Execute audit on droplet"""
    print("=" * 80)
    print("EXECUTING COMPREHENSIVE TRADING BOT AUDIT ON DROPLET")
    print("=" * 80)
    print()
    
    try:
        from droplet_client import DropletClient
        
        client = DropletClient()
        
        print("Connecting to droplet...")
        print("Running comprehensive audit...")
        print()
        
        stdout, stderr, exit_code = client._execute_with_cd(
            AUDIT_SCRIPT,
            timeout=120
        )
        
        print("=" * 80)
        print("AUDIT OUTPUT")
        print("=" * 80)
        print(stdout)
        if stderr:
            print("\nSTDERR:")
            print(stderr)
        
        # Try to extract JSON results
        if stdout:
            lines = stdout.split('\n')
            json_start = None
            for i, line in enumerate(lines):
                if '=== JSON RESULTS ===' in line:
                    json_start = i + 1
                    break
            
            if json_start:
                json_lines = lines[json_start:]
                json_text = '\n'.join(json_lines)
                try:
                    results = json.loads(json_text)
                    
                    # Save locally
                    local_path = Path("reports/droplet_audit_results.json")
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(local_path, 'w') as f:
                        json.dump(results, f, indent=2)
                    
                    print("\n" + "=" * 80)
                    print("AUDIT RESULTS SUMMARY")
                    print("=" * 80)
                    print(f"Timestamp: {results.get('timestamp')}")
                    print(f"Total Issues: {len(results.get('issues', []))}")
                    
                    if results.get("processes"):
                        print("\nProcess Status:")
                        for proc, status in results["processes"].items():
                            status_str = "[RUNNING]" if status.get("running") else "[NOT RUNNING]"
                            pids = status.get("pids", [])
                            pid_str = f" (PIDs: {', '.join(pids)})" if pids else ""
                            print(f"  {status_str} {proc}{pid_str}")
                    
                    if results.get("cache"):
                        cache = results["cache"]
                        if cache.get("exists"):
                            print(f"\nCache: {cache.get('symbol_count', 0)} symbols")
                        else:
                            print("\nCache: MISSING")
                    
                    if results.get("logs"):
                        print("\nLog Files:")
                        for name, status in results["logs"].items():
                            if status.get("exists"):
                                print(f"  {name}: {status.get('total', 0)} total, {status.get('recent', 0)} recent")
                            else:
                                print(f"  {name}: MISSING")
                    
                    if results.get("recent_trades"):
                        trades = results["recent_trades"]
                        print(f"\nRecent Trades (last 2h): {len(trades)}")
                        for trade in trades[:10]:
                            print(f"  {trade.get('symbol')}: {trade.get('age_min')} min ago, P&L: {trade.get('pnl', 'N/A')}%")
                    
                    if results.get("issues"):
                        print("\nIssues Found:")
                        for i, issue in enumerate(results["issues"], 1):
                            print(f"  {i}. {issue}")
                    
                    print(f"\nFull results saved to: {local_path}")
                    
                except json.JSONDecodeError as e:
                    print(f"\nCould not parse JSON results: {e}")
                    print("Raw JSON text:")
                    print(json_text[:500])
        
        client.close()
        
        return exit_code
        
    except ImportError:
        print("ERROR: droplet_client not available")
        print("Please install required dependencies or configure SSH access")
        return 1
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
