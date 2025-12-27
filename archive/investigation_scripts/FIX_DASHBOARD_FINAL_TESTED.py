#!/usr/bin/env python3
"""Complete fix - removes duplicate and fixes all indentation"""
from pathlib import Path
import subprocess

d = Path("dashboard.py")
content = d.read_text()
lines = content.split('\n')

print("Lines 1370-1395:")
for i in range(1370, min(1395, len(lines))):
    print(f"  {i+1}: {repr(lines[i])}")

# Strategy: Replace the entire problematic section with correct code
# Find the section from 'orders_files = [' to 'if last_order_ts:'

start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if 'orders_files = [' in line:
        start_idx = i
    if start_idx and 'if last_order_ts:' in line and i > start_idx + 5:
        end_idx = i
        break

if start_idx and end_idx:
    print(f"\nFound section: lines {start_idx+1} to {end_idx+1}")
    
    # Build correct section
    correct_section = [
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
        '        if last_order_ts:'
    ]
    
    # Replace the section
    new_lines = lines[:start_idx] + correct_section + lines[end_idx:]
    d.write_text('\n'.join(new_lines))
    print("✓ Replaced entire section with correct code")
else:
    # Fallback: just remove duplicate
    print("\nUsing fallback: remove duplicate only")
    fixed = []
    found_for = False
    for i, line in enumerate(lines):
        if 'for orders_file in orders_files:' in line:
            if found_for:
                print(f"Removing duplicate at line {i+1}")
                continue
            found_for = True
        fixed.append(line)
    d.write_text('\n'.join(fixed))

# Test
print("\nTesting compilation...")
result = subprocess.run(["python3", "-m", "py_compile", "dashboard.py"], 
                      capture_output=True, text=True)
if result.returncode == 0:
    print("✅ SUCCESS: Dashboard syntax fixed!")
    exit(0)
else:
    print(f"❌ Error:\n{result.stderr}")
    exit(1)
