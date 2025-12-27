#!/usr/bin/env python3
"""Complete fix - handles try/except structure correctly"""
from pathlib import Path
import subprocess
import re

d = Path("dashboard.py")
content = d.read_text()
lines = content.split('\n')

print("Analyzing file structure...")

# Find the problematic section
start_marker = 'orders_files = ['
end_marker = 'if last_order_ts:'

start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if start_marker in line and start_idx is None:
        start_idx = i
    if start_idx is not None and end_marker in line and i > start_idx + 5:
        # Find the line AFTER 'if last_order_ts:' - it should be the assignment
        if i + 1 < len(lines):
            # Check if next line is the assignment
            if 'last_order_age_sec' in lines[i + 1]:
                end_idx = i + 2  # Include the assignment line
            else:
                end_idx = i + 1
        else:
            end_idx = i + 1
        break

if start_idx is None or end_idx is None:
    print("❌ Could not find section markers")
    exit(1)

print(f"Found section: lines {start_idx+1} to {end_idx+1}")

# Check what comes after to ensure we don't break structure
print(f"\nLines around replacement area:")
for i in range(max(0, start_idx-2), min(len(lines), end_idx+5)):
    marker = ">>>" if start_idx <= i < end_idx else "   "
    print(f"{marker} {i+1:4d}: {repr(lines[i])}")

# Build correct replacement
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
    '            last_order_age_sec = time.time() - last_order_ts'
]

# Replace
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
    
    # If there's still an error, show context
    error_match = re.search(r'line (\d+)', result.stderr)
    if error_match:
        error_line = int(error_match.group(1))
        print(f"\nContext around error line {error_line}:")
        for i in range(max(0, error_line-5), min(len(new_lines), error_line+5)):
            marker = ">>>" if i == error_line - 1 else "   "
            print(f"{marker} {i+1:4d}: {repr(new_lines[i])}")
    
    exit(1)
