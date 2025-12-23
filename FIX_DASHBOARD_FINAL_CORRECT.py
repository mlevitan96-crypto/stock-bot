#!/usr/bin/env python3
"""FINAL FIX - removes ALL duplicate/broken code"""
from pathlib import Path
import subprocess
import re

d = Path("dashboard.py")
content = d.read_text()
lines = content.split('\n')

print("Analyzing file structure...")

# Find the start of the problematic section
start_marker = 'orders_files = ['
start_idx = None

for i, line in enumerate(lines):
    if start_marker in line:
        start_idx = i
        break

if start_idx is None:
    print("❌ Could not find start marker")
    exit(1)

# Find where valid code resumes - look for the comment after the broken section
end_marker = '# Get Doctor/heartbeat from file'
end_idx = None

for i in range(start_idx + 10, len(lines)):
    if end_marker in lines[i]:
        end_idx = i
        break

if end_idx is None:
    print("❌ Could not find end marker")
    exit(1)

print(f"Found section: lines {start_idx+1} to {end_idx+1}")

# Show what we're replacing
print(f"\nLines to be replaced:")
for i in range(start_idx, min(end_idx, start_idx + 30)):
    print(f"  {i+1:4d}: {repr(lines[i])}")

# Build correct replacement - from orders_files to just before the comment
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
    '        if last_order_ts:',
    '            last_order_age_sec = time.time() - last_order_ts',
    '        '
]

# Replace - keep the comment line
new_lines = lines[:start_idx] + correct_section + lines[end_idx:]
d.write_text('\n'.join(new_lines))
print(f"\n✓ Replaced {end_idx - start_idx} lines with {len(correct_section)} correct lines")

# Test compilation
print("\nTesting compilation...")
result = subprocess.run(["python3", "-m", "py_compile", "dashboard.py"], 
                      capture_output=True, text=True)
if result.returncode == 0:
    print("✅ SUCCESS: Dashboard syntax fixed!")
    exit(0)
else:
    print(f"❌ Compilation error:\n{result.stderr}")
    
    # Show context around error
    error_match = re.search(r'line (\d+)', result.stderr)
    if error_match:
        error_line = int(error_match.group(1))
        print(f"\nContext around error line {error_line}:")
        for i in range(max(0, error_line-5), min(len(new_lines), error_line+5)):
            marker = ">>>" if i == error_line - 1 else "   "
            print(f"{marker} {i+1:4d}: {repr(new_lines[i])}")
    
    exit(1)
