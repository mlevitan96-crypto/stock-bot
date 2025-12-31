#!/usr/bin/env python3
"""Wait for backtest to complete and show results"""
import time
import subprocess
import json
from pathlib import Path

report_path = Path("reports/7_day_quick_audit.json")
max_wait = 600  # 10 minutes
check_interval = 30

print(f"Waiting for backtest to complete (max {max_wait}s)...")
print("Checking every 30 seconds...")

start_time = time.time()
while time.time() - start_time < max_wait:
    # Check if process is still running
    result = subprocess.run(['pgrep', '-f', 'historical_replay_engine'], 
                          capture_output=True, text=True)
    if not result.stdout.strip():
        print("\nBacktest process completed!")
        break
    
    # Check if report exists and has data
    if report_path.exists():
        try:
            with open(report_path, 'r') as f:
                data = json.load(f)
            trades = data.get('total_trades', 0)
            if trades > 0:
                print(f"\n✅ Backtest completed with {trades} trades!")
                print(f"Win Rate: {data.get('win_rate', 0):.2f}%")
                specialist = data.get('specialist_metrics', {})
                print(f"Specialist Win Rate: {specialist.get('win_rate', 0):.2f}%")
                break
        except:
            pass
    
    elapsed = int(time.time() - start_time)
    print(f"Still running... ({elapsed}s elapsed)")
    time.sleep(check_interval)

# Final check
if report_path.exists():
    with open(report_path, 'r') as f:
        data = json.load(f)
    print(f"\nFinal Results:")
    print(f"Total Trades: {data.get('total_trades', 0)}")
    print(f"Win Rate: {data.get('win_rate', 0):.2f}%")
else:
    print("\n⚠️  Report file not found yet")
