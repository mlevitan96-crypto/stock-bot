#!/usr/bin/env python3
"""Fix dashboard.py - removes duplicate 'for' statement"""
from pathlib import Path
import subprocess

d = Path("dashboard.py")
content = d.read_text()
lines = content.split('\n')

print("Lines 1370-1380:")
for i in range(1370, min(1380, len(lines))):
    print(f"  {i+1}: {repr(lines[i])}")

# The problem: Line 1373 AND 1374 both have 'for orders_file in orders_files:'
# Remove the duplicate on line 1374

fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Check if this is line 1373 (index 1372) with 'for orders_file'
    if i == 1372 and 'for orders_file in orders_files:' in line:
        print(f"\nFound 'for orders_file' at line {i+1}")
        fixed_lines.append(line)  # Keep this one
        i += 1
        # Check if next line is a duplicate
        if i < len(lines) and 'for orders_file in orders_files:' in lines[i]:
            print(f"Removing duplicate 'for orders_file' at line {i+1}")
            i += 1  # Skip the duplicate
            continue
    
    fixed_lines.append(line)
    i += 1

# Write fixed file
d.write_text('\n'.join(fixed_lines))

# Test
print("\nTesting compilation...")
result = subprocess.run(["python3", "-m", "py_compile", "dashboard.py"], capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Dashboard syntax fixed!")
    exit(0)
else:
    print(f"❌ Error:\n{result.stderr}")
    exit(1)
