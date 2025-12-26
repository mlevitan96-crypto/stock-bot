#!/usr/bin/env python3
"""
Comprehensive Investigation: Why No Positions and Nothing Happening
This script runs on the droplet to diagnose the issue.
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

def run_command(cmd):
    """Run command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1

def check_processes():
    """Check if bot processes are running."""
    print("=" * 60)
    print("1. CHECKING PROCESSES")
    print("=" * 60)
    
    stdout, stderr, code = run_command("ps aux | grep -E 'main.py|dashboard.py|deploy_supervisor|uw_flow' | grep -v grep")
    processes = []
    for line in stdout.split('\n'):
        if line.strip():
            parts = line.split()
            if len(parts) >= 11:
                processes.append({
                    "pid": parts[1],
                    "cpu": parts[2],
                    "mem": parts[3],
                    "command": ' '.join(parts[10:])
                })
    
    print(f"Found {len(processes)} processes:")
    for p in processes:
        print(f"  PID {p['pid']}: {p['command'][:80]}")
    
    return processes

def check_positions():
    """Check current positions."""
    print("\n" + "=" * 60)
    print("2. CHECKING POSITIONS")
    print("=" * 60)
    
    pos_file = Path("state/positions.json")
    if not pos_file.exists():
        print("  [ERROR] positions.json does not exist")
        return {}
    
    try:
        with open(pos_file) as f:
            positions = json.load(f)
        
        open_positions = [p for p in positions.values() if p.get("status") == "open"]
        closed_positions = [p for p in positions.values() if p.get("status") == "closed"]
        
        print(f"  Total positions in file: {len(positions)}")
        print(f"  Open positions: {len(open_positions)}")
        print(f"  Closed positions: {len(closed_positions)}")
        
        if open_positions:
            print("\n  Open positions:")
            for symbol, pos in positions.items():
                if pos.get("status") == "open":
                    print(f"    {symbol}: {pos.get('quantity', 0)} shares @ ${pos.get('entry_price', 0):.2f}")
        else:
            print("  [WARNING] No open positions found")
        
        return positions
    except Exception as e:
        print(f"  [ERROR] Failed to read positions: {e}")
        return {}

def check_blocked_trades():
    """Check blocked trades."""
    print("\n" + "=" * 60)
    print("3. CHECKING BLOCKED TRADES")
    print("=" * 60)
    
    blocked_file = Path("state/blocked_trades.jsonl")
    if not blocked_file.exists():
        print("  [INFO] blocked_trades.jsonl does not exist (no blocks yet)")
        return []
    
    try:
        blocked = []
        with open(blocked_file) as f:
            for line in f:
                if line.strip():
                    try:
                        blocked.append(json.loads(line))
                    except:
                        pass
        
        # Count by reason
        reasons = defaultdict(int)
        for block in blocked[-50:]:  # Last 50
            reason = block.get("reason", "unknown")
            reasons[reason] += 1
        
        print(f"  Total blocked trades (last 50): {len(blocked[-50:])}")
        print("  Block reasons:")
        for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
            print(f"    {reason}: {count}")
        
        return blocked[-50:]
    except Exception as e:
        print(f"  [ERROR] Failed to read blocked trades: {e}")
        return []

def check_signals():
    """Check recent signals."""
    print("\n" + "=" * 60)
    print("4. CHECKING RECENT SIGNALS")
    print("=" * 60)
    
    signals_file = Path("logs/signals.jsonl")
    if not signals_file.exists():
        print("  [ERROR] signals.jsonl does not exist")
        return []
    
    try:
        signals = []
        with open(signals_file) as f:
            for line in f:
                if line.strip():
                    try:
                        signals.append(json.loads(line))
                    except:
                        pass
        
        recent = signals[-20:] if len(signals) > 20 else signals
        print(f"  Total signals in log: {len(signals)}")
        print(f"  Recent signals (last 20): {len(recent)}")
        
        if recent:
            print("\n  Recent signals:")
            for sig in recent[-10:]:
                symbol = sig.get("symbol", "unknown")
                score = sig.get("composite_score", 0)
                timestamp = sig.get("timestamp", "unknown")
                print(f"    {symbol}: score={score:.2f} at {timestamp}")
        else:
            print("  [WARNING] No recent signals found")
        
        return recent
    except Exception as e:
        print(f"  [ERROR] Failed to read signals: {e}")
        return []

def check_market_status():
    """Check if market is open."""
    print("\n" + "=" * 60)
    print("5. CHECKING MARKET STATUS")
    print("=" * 60)
    
    stdout, stderr, code = run_command("cd ~/stock-bot && python3 -c \"from datetime import datetime; import pytz; now = datetime.now(pytz.timezone('America/New_York')); print(f'Current NY time: {now.strftime(\\\"%Y-%m-%d %H:%M:%S %Z\\\")}'); print(f'Is market hours: {9 <= now.hour < 16}'); print(f'Is weekday: {now.weekday() < 5}')\"")
    print(stdout)
    
    return stdout

def check_logs():
    """Check recent logs for errors."""
    print("\n" + "=" * 60)
    print("6. CHECKING RECENT LOGS FOR ERRORS")
    print("=" * 60)
    
    log_files = [
        "logs/trading.log",
        "logs/run.jsonl",
        "logs/orders.jsonl"
    ]
    
    errors = []
    for log_file in log_files:
        log_path = Path(log_file)
        if log_path.exists():
            print(f"\n  Checking {log_file}:")
            try:
                with open(log_path) as f:
                    lines = f.readlines()
                    recent_lines = lines[-50:] if len(lines) > 50 else lines
                    
                    error_lines = [l for l in recent_lines if 'error' in l.lower() or 'exception' in l.lower() or 'failed' in l.lower()]
                    if error_lines:
                        print(f"    Found {len(error_lines)} error lines:")
                        for line in error_lines[-5:]:
                            print(f"      {line.strip()[:100]}")
                        errors.extend(error_lines)
                    else:
                        print(f"    No errors in last {len(recent_lines)} lines")
            except Exception as e:
                print(f"    [ERROR] Failed to read: {e}")
        else:
            print(f"  [INFO] {log_file} does not exist")
    
    return errors

def check_uw_api():
    """Check UW API status."""
    print("\n" + "=" * 60)
    print("7. CHECKING UW API STATUS")
    print("=" * 60)
    
    stdout, stderr, code = run_command("cd ~/stock-bot && python3 -c \"import requests; from config.registry import ConfigFiles; import json; config = json.load(open(ConfigFiles.UW_API_CONFIG)); api_key = config.get('api_key'); print(f'API key configured: {bool(api_key)}'); print(f'API key length: {len(api_key) if api_key else 0}')\"")
    print(stdout)
    if stderr:
        print(f"  [ERROR] {stderr}")

def check_gates():
    """Check gate status."""
    print("\n" + "=" * 60)
    print("8. CHECKING GATE STATUS")
    print("=" * 60)
    
    stdout, stderr, code = run_command("cd ~/stock-bot && python3 -c \"from pathlib import Path; import json; gate_file = Path('state/gate_status.json'); print(f'Gate status file exists: {gate_file.exists()}'); data = json.load(open(gate_file)) if gate_file.exists() else {}; print(f'Gate status: {json.dumps(data, indent=2)}')\"")
    print(stdout)
    if stderr:
        print(f"  [ERROR] {stderr}")

def main():
    """Run comprehensive investigation."""
    print("=" * 60)
    print("COMPREHENSIVE INVESTIGATION: NO POSITIONS / NOTHING HAPPENING")
    print("=" * 60)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "processes": check_processes(),
        "positions": check_positions(),
        "blocked_trades": check_blocked_trades(),
        "signals": check_signals(),
        "market_status": check_market_status(),
        "log_errors": check_logs(),
        "uw_api": check_uw_api(),
        "gates": check_gates()
    }
    
    print("\n" + "=" * 60)
    print("INVESTIGATION SUMMARY")
    print("=" * 60)
    
    # Summary
    process_count = len(results["processes"])
    open_positions = len([p for p in results["positions"].values() if p.get("status") == "open"]) if results["positions"] else 0
    recent_signals = len(results["signals"])
    error_count = len(results["log_errors"])
    
    print(f"Processes running: {process_count}")
    print(f"Open positions: {open_positions}")
    print(f"Recent signals: {recent_signals}")
    print(f"Errors in logs: {error_count}")
    
    # Save results
    output_file = Path("investigate_no_positions.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: {output_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()

