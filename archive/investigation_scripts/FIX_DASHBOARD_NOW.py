#!/usr/bin/env python3
"""Fix dashboard.py syntax error - direct fix"""
from pathlib import Path
import subprocess

dashboard = Path("dashboard.py")
if not dashboard.exists():
    print("❌ dashboard.py not found")
    exit(1)

print("Reading dashboard.py...")
content = dashboard.read_text()

# The error is on line 1374-1375: "expected an indented block after 'if' statement"
# The fix: ensure the 'if orders_file.exists():' has a proper body

# Find and replace the problematic pattern
# Pattern 1: If there's a missing body after 'if orders_file.exists():'
pattern1 = r'(\s+for orders_file in orders_files:\s+if orders_file\.exists\(\):\s*\n\s*)(if last_order_ts:)'

# Pattern 2: If the try block is missing
pattern2 = r'(\s+if orders_file\.exists\(\):\s*\n)(\s+if last_order_ts:)'

# Try to fix by ensuring the complete structure exists
fixed_content = content

# Check if the structure is broken
if 'for orders_file in orders_files:' in content:
    # Find the section
    lines = content.split('\n')
    for i in range(len(lines)):
        if 'for orders_file in orders_files:' in lines[i]:
            # Check next few lines
            if i+1 < len(lines) and 'if orders_file.exists():' in lines[i+1]:
                # Check if line i+2 has proper content
                if i+2 >= len(lines) or (lines[i+2].strip() and not lines[i+2].startswith(' ' * 16)):
                    # The body is missing - insert it
                    print(f"Found broken structure at line {i+1}")
                    new_lines = lines[:i+2]  # Up to 'if orders_file.exists():'
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
                    # Find where to continue (skip any duplicate lines)
                    j = i + 2
                    while j < len(lines) and (not lines[j].strip() or lines[j].startswith(' ' * 12)):
                        j += 1
                    new_lines.extend(lines[j:])
                    fixed_content = '\n'.join(new_lines)
                    print("✓ Fixed structure")
                    break

# Write fixed content
dashboard.write_text(fixed_content)

# Test compilation
print("\nTesting compilation...")
result = subprocess.run(["python3", "-m", "py_compile", "dashboard.py"], 
                      capture_output=True, text=True)
if result.returncode == 0:
    print("✅ SUCCESS: Dashboard syntax fixed!")
else:
    print(f"❌ Still has errors:\n{result.stderr}")
    # Try one more time with a complete rewrite of the function
    print("\nTrying complete function rewrite...")
    # This is a last resort - rewrite the entire api_health_status function
    import re
    func_pattern = r'@app\.route\("/api/health_status".*?def api_health_status\(\):.*?try:.*?return jsonify\(\{.*?\}\), 200\s+except Exception as e:.*?return jsonify\(\{"error": str\(e\)\}\), 500'
    
    # For now, just exit with error so user knows
    exit(1)
