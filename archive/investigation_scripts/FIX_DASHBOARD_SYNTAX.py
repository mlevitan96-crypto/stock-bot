#!/usr/bin/env python3
"""
Fix dashboard.py syntax error
The error is: "expected an indented block after 'if' statement on line 1374"
This script fixes the indentation/structure issue
"""

from pathlib import Path
import re

dashboard_path = Path("dashboard.py")

if not dashboard_path.exists():
    print("❌ dashboard.py not found")
    exit(1)

print("Reading dashboard.py...")
content = dashboard_path.read_text()
lines = content.split('\n')

print(f"Total lines: {len(lines)}")

# Find the problematic section (around line 1374)
# The issue is that the 'if orders_file.exists():' line needs a proper body

# Look for the pattern
problem_pattern = r'(\s+for orders_file in orders_files:\s+if orders_file\.exists\(\):)'

# Check if we can find the issue
found_issue = False
for i, line in enumerate(lines):
    if i >= 1370 and i <= 1395:  # Around the problematic area
        if 'for orders_file in orders_files:' in line:
            print(f"Found 'for orders_file' loop at line {i+1}")
            # Check next line
            if i+1 < len(lines):
                next_line = lines[i+1]
                if 'if orders_file.exists():' in next_line:
                    print(f"Found 'if orders_file.exists():' at line {i+2}")
                    # Check if the next line after that has proper indentation
                    if i+2 < len(lines):
                        after_if = lines[i+2]
                        # If the line after 'if' is empty or not properly indented, that's the problem
                        if not after_if.strip() or (after_if.strip() and not after_if.startswith(' ' * 16)):
                            print(f"❌ Problem found! Line {i+3} after 'if' is not properly indented")
                            print(f"   Line {i+3}: {repr(after_if)}")
                            found_issue = True
                            
                            # Fix it by ensuring proper structure
                            # We need to insert the try block properly
                            fixed_lines = lines[:i+2]  # Up to and including 'if orders_file.exists():'
                            
                            # Add the try block with proper indentation
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
                            
                            # Now add the rest of the lines, but skip any that are already part of the loop
                            # We need to find where the original loop body ends
                            j = i + 2
                            while j < len(lines):
                                current_line = lines[j]
                                # If we hit a line that's at the same or less indentation as the 'for' loop, we're done
                                if current_line.strip() and not current_line.startswith(' ' * 12):
                                    # This is outside the loop
                                    break
                                # Skip lines that are part of the broken structure
                                if 'try:' in current_line and current_line.startswith(' ' * 16):
                                    # This is the try we're adding, skip the original
                                    j += 1
                                    continue
                                j += 1
                            
                            # Add remaining lines
                            fixed_lines.extend(lines[j:])
                            
                            # Write the fixed content
                            fixed_content = '\n'.join(fixed_lines)
                            dashboard_path.write_text(fixed_content)
                            
                            print(f"✓ Fixed! Wrote {len(fixed_lines)} lines")
                            break

if not found_issue:
    # Try a different approach - just ensure the structure is correct by replacing the entire section
    print("Trying alternative fix method...")
    
    # Find the exact section to replace
    old_section = """        for orders_file in orders_files:
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
    
    # Check if this exact section exists
    if old_section in content:
        print("✓ Structure looks correct, checking for hidden characters...")
        # The issue might be hidden characters or encoding
        # Re-write the section to ensure clean formatting
        new_section = """        for orders_file in orders_files:
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
        
        # Replace with clean version
        fixed_content = content.replace(old_section, new_section)
        dashboard_path.write_text(fixed_content)
        print("✓ Re-wrote section with clean formatting")
    else:
        print("⚠️  Could not find exact section to fix")
        print("Testing compilation...")
        import subprocess
        result = subprocess.run(["python3", "-m", "py_compile", "dashboard.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Dashboard compiles successfully!")
        else:
            print(f"❌ Still has errors:\n{result.stderr}")

# Final test
print("\nTesting final compilation...")
import subprocess
result = subprocess.run(["python3", "-m", "py_compile", "dashboard.py"], 
                      capture_output=True, text=True)
if result.returncode == 0:
    print("✅ SUCCESS: Dashboard syntax is now valid!")
else:
    print(f"❌ Still has errors:\n{result.stderr}")
    exit(1)
