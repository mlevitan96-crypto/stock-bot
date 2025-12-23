#!/usr/bin/env python3
"""Fix dashboard.py - tested and verified"""
from pathlib import Path
import subprocess

dashboard = Path("dashboard.py")
if not dashboard.exists():
    print("❌ dashboard.py not found")
    exit(1)

print("Reading dashboard.py...")
content = dashboard.read_text()
lines = content.split('\n')

print(f"Total lines: {len(lines)}")

# Find the problematic section
fixed = False
for i in range(len(lines)):
    if i < 1370 or i > 1395:
        continue
    
    line = lines[i]
    
    # Look for "if orders_file.exists():" that might be missing body
    if 'if orders_file.exists():' in line:
        print(f"Found 'if orders_file.exists():' at line {i+1}")
        # Check next line
        if i+1 < len(lines):
            next_line = lines[i+1]
            # If next line is empty or doesn't start with proper indentation, it's broken
            if not next_line.strip():
                print(f"❌ Line {i+2} is empty - missing body!")
                # Insert the missing try block
                new_lines = lines[:i+1]  # Up to and including 'if orders_file.exists():'
                new_lines.append('                try:')
                new_lines.append('                    with orders_file.open("r") as f:')
                new_lines.append('                        lines = f.readlines()')
                new_lines.append('                        for line in lines[-500:]:')
                new_lines.append('                            try:')
                new_lines.append('                                event = json.loads(line.strip())')
                new_lines.append('                                event_ts = event.get("_ts", 0)')
                new_lines.append('                                event_type = event.get("event", "")')
                new_lines.append('                                if event_ts > (last_order_ts or 0) and event_type in ["MARKET_FILLED", "LIMIT_FILLED", "ORDER_SUBMITTED"]:')
                new_lines.append('                                    last_order_ts = event_ts')
                new_lines.append('                            except:')
                new_lines.append('                                pass')
                new_lines.append('                except:')
                new_lines.append('                    pass')
                # Skip the empty line and continue
                new_lines.extend(lines[i+2:])
                lines = new_lines
                fixed = True
                print("✓ Fixed by inserting missing body")
                break
            elif not next_line.startswith(' ' * 16):  # Should be indented 16 spaces
                print(f"❌ Line {i+2} not properly indented: {repr(next_line)}")
                # Insert the missing try block
                new_lines = lines[:i+1]
                new_lines.append('                try:')
                new_lines.append('                    with orders_file.open("r") as f:')
                new_lines.append('                        lines = f.readlines()')
                new_lines.append('                        for line in lines[-500:]:')
                new_lines.append('                            try:')
                new_lines.append('                                event = json.loads(line.strip())')
                new_lines.append('                                event_ts = event.get("_ts", 0)')
                new_lines.append('                                event_type = event.get("event", "")')
                new_lines.append('                                if event_ts > (last_order_ts or 0) and event_type in ["MARKET_FILLED", "LIMIT_FILLED", "ORDER_SUBMITTED"]:')
                new_lines.append('                                    last_order_ts = event_ts')
                new_lines.append('                            except:')
                new_lines.append('                                pass')
                new_lines.append('                except:')
                new_lines.append('                    pass')
                # Find where to continue - skip lines that are part of broken structure
                j = i + 1
                while j < len(lines) and lines[j].strip() and lines[j].startswith(' ' * 12):
                    j += 1
                new_lines.extend(lines[j:])
                lines = new_lines
                fixed = True
                print("✓ Fixed by inserting missing body")
                break

if fixed:
    dashboard.write_text('\n'.join(lines))
    print("✓ Wrote fixed file")
else:
    print("⚠️  Could not auto-detect issue, trying compilation test...")

# Test compilation
print("\nTesting compilation...")
result = subprocess.run(["python3", "-m", "py_compile", "dashboard.py"], 
                      capture_output=True, text=True)
if result.returncode == 0:
    print("✅ SUCCESS: Dashboard syntax is valid!")
    exit(0)
else:
    print(f"❌ Still has errors:\n{result.stderr}")
    # Show the problematic lines
    error_lines = result.stderr.split('\n')
    for err_line in error_lines:
        if 'line' in err_line.lower():
            print(f"  {err_line}")
    exit(1)
