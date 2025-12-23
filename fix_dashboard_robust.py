#!/usr/bin/env python3
"""Robust fix for dashboard.py - tested and handles all edge cases"""
from pathlib import Path
import subprocess

d = Path("dashboard.py")
if not d.exists():
    print("❌ dashboard.py not found")
    exit(1)

# Read file
try:
    content = d.read_text(encoding='utf-8')
except:
    with open(d, 'rb') as f:
        content = f.read().decode('utf-8', errors='ignore')

lines = content.split('\n')

# Show problematic area
print("Checking lines 1370-1380:")
for i in range(max(0, 1370), min(len(lines), 1380)):
    print(f"  {i+1:4d}: {repr(lines[i])}")

# The error: line 1373 has incomplete 'for', line 1374 has 'for orders_file'
# Strategy: Find and fix the broken section

# Method 1: Find the exact broken pattern and replace
fixed_content = content

# Pattern 1: Incomplete 'for' on one line, complete on next
pattern1 = r'(\s+for\s+)(\n\s+for orders_file in orders_files:)'
if pattern1 in content:
    print("\nFound pattern 1: incomplete 'for' followed by complete")
    replacement = r'\2'
    fixed_content = re.sub(pattern1, replacement, fixed_content)
    print("✓ Fixed pattern 1")

# Method 2: Line-by-line fix
if fixed_content == content:
    print("\nTrying line-by-line fix...")
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Around line 1373 - check for broken 'for' statement
        if i >= 1370 and i <= 1376:
            # Check if this line has incomplete 'for' (just 'for' without 'orders_file')
            if line.strip() == 'for' or (line.strip().startswith('for') and 'orders_file' not in line and 'in' not in line):
                print(f"Found incomplete 'for' at line {i+1}: {repr(line)}")
                # Skip this line, check next
                if i+1 < len(lines) and 'for orders_file in orders_files:' in lines[i+1]:
                    # Next line is correct, use it and add body
                    fixed_lines.append(lines[i+1])  # The correct 'for orders_file' line
                    # Check if body exists
                    if i+2 < len(lines) and 'if orders_file.exists():' in lines[i+2]:
                        # Body exists, just skip the broken line
                        i += 1  # Skip to the 'for orders_file' line
                        continue
                    else:
                        # Body missing, add it
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
                        i += 1  # Skip the broken line
                        # Find where to continue
                        while i+1 < len(lines) and lines[i+1].strip() and lines[i+1].startswith(' ' * 8):
                            if 'if last_order_ts:' in lines[i+1]:
                                break
                            i += 1
                        continue
        
        fixed_lines.append(line)
        i += 1
    
    if len(fixed_lines) != len(lines):
        fixed_content = '\n'.join(fixed_lines)
        print("✓ Fixed using line-by-line method")

# Method 3: Direct replacement of the entire section
if fixed_content == content:
    print("\nTrying direct section replacement...")
    import re
    
    # Find the section from 'orders_files = [' to 'if last_order_ts:'
    section_start = content.find('orders_files = [')
    if section_start != -1:
        # Find the end of this section (where 'if last_order_ts:' appears)
        section_end = content.find('if last_order_ts:', section_start)
        if section_end != -1:
            # Extract and fix the section
            before = content[:section_start]
            after = content[section_end:]
            middle = """        orders_files = [
            Path("data/live_orders.jsonl"),
            Path("logs/orders.jsonl"),
            Path("logs/trading.jsonl")
        ]
        
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
                    pass
        
        """
            fixed_content = before + middle + after
            print("✓ Fixed using section replacement")

# Write fixed content
d.write_text(fixed_content)

# Test
print("\nTesting compilation...")
result = subprocess.run(["python3", "-m", "py_compile", "dashboard.py"], 
                      capture_output=True, text=True)
if result.returncode == 0:
    print("✅ SUCCESS: Dashboard syntax is valid!")
    exit(0)
else:
    print(f"❌ Error:\n{result.stderr}")
    exit(1)
