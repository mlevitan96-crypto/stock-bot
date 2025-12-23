#!/usr/bin/env python3
"""Tested fix for dashboard.py - handles all cases"""
from pathlib import Path
import subprocess

d = Path("dashboard.py")
if not d.exists():
    print("❌ dashboard.py not found")
    exit(1)

print("Reading dashboard.py...")
try:
    content = d.read_text(encoding='utf-8')
except:
    content = d.read_bytes().decode('utf-8', errors='ignore')

lines = content.split('\n')
print(f"Total lines: {len(lines)}")

# Show the problematic area
print("\nLines around 1373-1375:")
for i in range(max(0, 1370), min(len(lines), 1380)):
    marker = ">>>" if i in [1372, 1373, 1374] else "   "
    print(f"{marker} {i+1:4d}: {repr(lines[i])}")

# Find the exact problem
# The error says: line 1373 has 'for' without body, line 1374 has 'for orders_file'
# This means line 1373 is incomplete

fixed_lines = []
i = 0
fixed = False

while i < len(lines):
    line = lines[i]
    
    # Check around line 1373-1374
    if i >= 1370 and i <= 1376:
        # Case 1: Line 1373 has incomplete 'for' statement
        if i == 1372 and 'for' in line and 'orders_file' not in line:
            print(f"\nFound incomplete 'for' at line {i+1}: {repr(line)}")
            # Replace with complete structure
            fixed_lines.append('        for orders_file in orders_files:')
            fixed_lines.append('            if orders_file.exists():')
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
            # Skip the broken lines
            i += 1
            while i < len(lines) and (not lines[i].strip() or lines[i].startswith(' ' * 8) or 'for orders_file' in lines[i]):
                if 'if last_order_ts:' in lines[i]:
                    break
                i += 1
            fixed = True
            continue
        
        # Case 2: Line 1374 has 'for orders_file' but line 1373 has incomplete 'for'
        if i == 1373 and 'for orders_file in orders_files:' in line:
            # Check previous line
            if i > 0 and 'for' in lines[i-1] and 'orders_file' not in lines[i-1]:
                print(f"\nFound broken structure: incomplete 'for' at {i}, complete at {i+1}")
                # Remove the incomplete line, keep the complete one
                fixed_lines.pop()  # Remove the incomplete line we just added
                fixed_lines.append('        for orders_file in orders_files:')
                fixed_lines.append('            if orders_file.exists():')
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
                # Skip until we hit proper code
                while i < len(lines) and lines[i].strip() and lines[i].startswith(' ' * 8):
                    if 'if last_order_ts:' in lines[i]:
                        break
                    i += 1
                fixed = True
                continue
    
    fixed_lines.append(line)
    i += 1

if fixed:
    d.write_text('\n'.join(fixed_lines))
    print("\n✓ Wrote fixed file")
else:
    print("\n⚠️  Could not auto-fix. Trying manual replacement...")
    # Last resort: find and replace the entire problematic section
    old_pattern = """        ]
        
        for orders_file in orders_files:
            if orders_file.exists():"""
    
    new_pattern = """        ]
        
        for orders_file in orders_files:
            if orders_file.exists():
                try:
                    with orders_file.open("r") as f:
                        lines = f.readlines()
                        for line in lines[-500:]:
                            try:
                                event = json.loads(line.strip())
                                event_ts = event.get("_ts", 0)
                                event_type = event.get("event", "")
                                if event_ts > (last_order_ts or 0) and event_type in ["MARKET_FILLED", "LIMIT_FILLED", "ORDER_SUBMITTED"]:
                                    last_order_ts = event_ts
                            except:
                                pass
                except:
                    pass"""
    
    if old_pattern in content:
        fixed_content = content.replace(old_pattern, new_pattern, 1)
        d.write_text(fixed_content)
        print("✓ Fixed using pattern replacement")
        fixed = True

# Test compilation
print("\nTesting compilation...")
result = subprocess.run(["python3", "-m", "py_compile", "dashboard.py"], 
                      capture_output=True, text=True)
if result.returncode == 0:
    print("✅ SUCCESS: Dashboard syntax is valid!")
    exit(0)
else:
    print(f"❌ Still has errors:\n{result.stderr}")
    # Show problematic lines
    for line in result.stderr.split('\n'):
        if 'line' in line.lower():
            print(f"  {line}")
    exit(1)
