#!/usr/bin/env python3
"""Complete fix for dashboard.py - removes duplicate and fixes indentation"""
from pathlib import Path
import subprocess

d = Path("dashboard.py")
content = d.read_text()
lines = content.split('\n')

print("Lines 1370-1395:")
for i in range(1370, min(1395, len(lines))):
    print(f"  {i+1}: {repr(lines[i])}")

# Fix: Remove duplicate 'for orders_file' and ensure proper structure
fixed_lines = []
i = 0
found_for = False

while i < len(lines):
    line = lines[i]
    
    # Check for duplicate 'for orders_file'
    if 'for orders_file in orders_files:' in line:
        if found_for:
            print(f"\nRemoving duplicate 'for orders_file' at line {i+1}")
            i += 1
            continue
        found_for = True
    
    fixed_lines.append(line)
    i += 1

# Write fixed content
d.write_text('\n'.join(fixed_lines))

# Test compilation
print("\nTesting compilation...")
result = subprocess.run(["python3", "-m", "py_compile", "dashboard.py"], 
                      capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Dashboard syntax fixed!")
    exit(0)
else:
    print(f"❌ Error:\n{result.stderr}")
    # If there's still an error, try to fix indentation
    if "IndentationError" in result.stderr:
        print("\nFixing indentation...")
        # Re-read and fix indentation issues
        content = d.read_text()
        lines = content.split('\n')
        
        # Find the problematic 'except' around line 1391
        for i in range(1385, min(1395, len(lines))):
            if 'except:' in lines[i]:
                # Check indentation - should be 16 spaces for inner except, 12 for outer
                line = lines[i]
                stripped = line.lstrip()
                if stripped == 'except:':
                    # Check context to determine correct indentation
                    # Look backwards for matching try
                    indent = 16  # Default for inner except
                    # Check if there's a 'try:' 8 lines back with 16 space indent
                    if i >= 8 and 'try:' in lines[i-8] and lines[i-8].startswith(' ' * 16):
                        indent = 16
                    elif i >= 2 and 'try:' in lines[i-2] and lines[i-2].startswith(' ' * 12):
                        indent = 12
                    # Fix the indentation
                    lines[i] = ' ' * indent + 'except:'
                    print(f"Fixed indentation at line {i+1}")
        
        d.write_text('\n'.join(lines))
        
        # Test again
        result2 = subprocess.run(["python3", "-m", "py_compile", "dashboard.py"], 
                               capture_output=True, text=True)
        if result2.returncode == 0:
            print("✅ Fixed with indentation correction!")
            exit(0)
        else:
            print(f"❌ Still has errors:\n{result2.stderr}")
    
    exit(1)
