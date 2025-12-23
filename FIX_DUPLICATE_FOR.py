#!/usr/bin/env python3
"""Remove duplicate 'for orders_file' line - TESTED"""
from pathlib import Path
import subprocess

d = Path("dashboard.py")
content = d.read_text()
lines = content.split('\n')

print("Checking lines 1370-1380:")
for i in range(1370, min(1380, len(lines))):
    print(f"  {i+1}: {repr(lines[i])}")

# Find duplicate 'for orders_file' lines
fixed_lines = []
i = 0
last_was_for = False

while i < len(lines):
    line = lines[i]
    is_for = 'for orders_file in orders_files:' in line
    
    # If this is a 'for orders_file' line
    if is_for:
        if last_was_for:
            # This is a duplicate - skip it
            print(f"\nRemoving duplicate 'for orders_file' at line {i+1}")
            i += 1
            continue
        else:
            # First occurrence - keep it
            last_was_for = True
    else:
        last_was_for = False
    
    fixed_lines.append(line)
    i += 1

# Write
d.write_text('\n'.join(fixed_lines))

# Test
result = subprocess.run(["python3", "-m", "py_compile", "dashboard.py"], capture_output=True, text=True)
if result.returncode == 0:
    print("\n✅ Dashboard syntax fixed!")
    exit(0)
else:
    print(f"\n❌ Error:\n{result.stderr}")
    exit(1)
