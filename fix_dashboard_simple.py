#!/usr/bin/env python3
"""Simple, tested fix for dashboard.py syntax error"""
from pathlib import Path
import subprocess

d = Path("dashboard.py")
if not d.exists():
    print("❌ dashboard.py not found")
    exit(1)

content = d.read_text()
lines = content.split('\n')

# The error: line 1374 has 'if' without body, line 1375 has 'for orders_file'
# Fix: Swap them and add proper structure

fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Check if this is the problematic area (around line 1374)
    if i >= 1370 and i <= 1376:
        # Look for the broken pattern: 'if' followed by 'for orders_file'
        if 'if orders_file.exists():' in line or ('if' in line and 'orders_file' in line and 'exists' in line):
            # Check if next line has 'for orders_file'
            if i+1 < len(lines) and 'for orders_file in orders_files:' in lines[i+1]:
                print(f"Found broken structure at line {i+1}")
                # The structure is backwards - fix it
                # Line should be: 'for orders_file in orders_files:'
                fixed_lines.append('        for orders_file in orders_files:')
                i += 1  # Skip the 'if' line
                # Next should be: 'if orders_file.exists():'
                if i < len(lines) and 'for orders_file' in lines[i]:
                    fixed_lines.append('            if orders_file.exists():')
                    # Add the try block
                    fixed_lines.append('                try:')
                    fixed_lines.append('                    with orders_file.open("r") as f:')
                    fixed_lines.append('                        lines = f.readlines()')
                    fixed_lines.append('                        for line in lines[-500:]:')
                    fixed_lines.append('                            try:')
                    fixed_lines.append('                                event = json.loads(line.strip())')
                    fixed_lines.append('                                event_ts = event.get("_ts", 0)')
                    fixed_lines.append('                                event_type = event.get("event", "")')
                    fixed_lines.append('                                if event_ts > (last_order_ts or 0) and event_type in ["MARKET_FILLED", "LIMIT_FILLED", "ORDER_SUBMITTED"]:')
                    fixed_lines.append('                                    last_order_ts = event_ts')
                    fixed_lines.append('                            except:')
                    fixed_lines.append('                                pass')
                    fixed_lines.append('                except:')
                    fixed_lines.append('                    pass')
                    i += 1
                    # Skip any other broken lines until we hit proper code
                    while i < len(lines) and lines[i].strip() and (lines[i].startswith(' ' * 8) or lines[i].startswith(' ' * 12)):
                        if 'if last_order_ts:' in lines[i]:
                            break
                        i += 1
                    continue
        # Also check for 'if' without body
        elif 'if orders_file.exists():' in line:
            # Check if next line is empty or wrong
            if i+1 >= len(lines) or not lines[i+1].strip() or not lines[i+1].startswith(' ' * 16):
                print(f"Found 'if' without body at line {i+1}")
                fixed_lines.append(line)
                # Add the missing body
                fixed_lines.append('                try:')
                fixed_lines.append('                    with orders_file.open("r") as f:')
                fixed_lines.append('                        lines = f.readlines()')
                fixed_lines.append('                        for line in lines[-500:]:')
                fixed_lines.append('                            try:')
                fixed_lines.append('                                event = json.loads(line.strip())')
                fixed_lines.append('                                event_ts = event.get("_ts", 0)')
                fixed_lines.append('                                event_type = event.get("event", "")')
                fixed_lines.append('                                if event_ts > (last_order_ts or 0) and event_type in ["MARKET_FILLED", "LIMIT_FILLED", "ORDER_SUBMITTED"]:')
                fixed_lines.append('                                    last_order_ts = event_ts')
                fixed_lines.append('                            except:')
                fixed_lines.append('                                pass')
                fixed_lines.append('                except:')
                fixed_lines.append('                    pass')
                i += 1
                continue
    
    fixed_lines.append(line)
    i += 1

# Write fixed content
d.write_text('\n'.join(fixed_lines))

# Test
result = subprocess.run(["python3", "-m", "py_compile", "dashboard.py"], capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Dashboard syntax fixed!")
else:
    print(f"❌ Error: {result.stderr}")
    exit(1)
