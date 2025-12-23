#!/usr/bin/env python3
"""WORKING fix - replaces section correctly including line after if"""
from pathlib import Path
import subprocess

d = Path("dashboard.py")
lines = d.read_text().split('\n')

# Find section boundaries
start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if 'orders_files = [' in line:
        start_idx = i
    if start_idx and 'if last_order_ts:' in line and i > start_idx + 5:
        # Include the line AFTER 'if last_order_ts:' too
        end_idx = i + 1
        break

if start_idx and end_idx:
    print(f"Replacing lines {start_idx+1} to {end_idx+1}")
    
    # CORRECT section - includes line after 'if last_order_ts:'
    correct = [
        '        orders_files = [',
        '            Path("data/live_orders.jsonl"),',
        '            Path("logs/orders.jsonl"),',
        '            Path("logs/trading.jsonl")',
        '        ]',
        '        ',
        '        for orders_file in orders_files:',
        '            if orders_file.exists():',
        '                try:',
        '                    with orders_file.open("r") as f:',
        '                        lines = f.readlines()',
        '                        for line in lines[-500:]:',
        '                            try:',
        '                                event = json.loads(line.strip())',
        '                                event_ts = event.get("_ts", 0)',
        '                                event_type = event.get("event", "")',
        '                                if event_ts > (last_order_ts or 0) and event_type in ["MARKET_FILLED", "LIMIT_FILLED", "ORDER_SUBMITTED"]:',
        '                                    last_order_ts = event_ts',
        '                            except:',
        '                                pass',
        '                except:',
        '                    pass',
        '        ',
        '        if last_order_ts:',
        '            last_order_age_sec = time.time() - last_order_ts'
    ]
    
    new_lines = lines[:start_idx] + correct + lines[end_idx:]
    d.write_text('\n'.join(new_lines))
    print("✓ Replaced")
else:
    print("❌ Could not find section")
    exit(1)

# Test
result = subprocess.run(["python3", "-m", "py_compile", "dashboard.py"], capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Fixed!")
    exit(0)
else:
    print(f"❌ Error:\n{result.stderr}")
    exit(1)
