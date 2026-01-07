#!/usr/bin/env python3
"""Comprehensive hardening audit and fixes"""

import re
from pathlib import Path

print("="*80)
print("COMPREHENSIVE HARDENING AUDIT")
print("="*80)

main_file = Path("main.py")
if not main_file.exists():
    print("main.py not found")
    exit(1)

content = main_file.read_text()
lines = content.split('\n')

issues = {
    "api_calls": [],
    "state_file_ops": [],
    "division_ops": [],
    "dict_access": [],
    "list_access": [],
    "type_conversions": [],
    "missing_validation": []
}

# 1. Find API calls without proper error handling
api_patterns = [
    r'\.api\.(list_positions|get_account|submit_order|close_position|get_bars)\(\)',
    r'self\.executor\.api\.',
    r'api\.(list_positions|get_account|submit_order)'
]

for i, line in enumerate(lines, 1):
    for pattern in api_patterns:
        if re.search(pattern, line):
            # Check if wrapped in try/except
            context_start = max(0, i-15)
            context_end = min(len(lines), i+5)
            context = '\n'.join(lines[context_start:context_end])
            if 'try:' not in context or 'except' not in context:
                issues["api_calls"].append(f"Line {i}: {line.strip()}")

# 2. Find division operations (potential divide by zero)
for i, line in enumerate(lines, 1):
    if '/' in line and '//' not in line:  # Regular division, not floor division
        # Skip comments and strings
        if '#' in line or '"' in line[:line.find('/')] or "'" in line[:line.find('/')]:
            continue
        # Check if denominator is validated
        if 'if.*>' in line or 'if.*!=' in line:
            continue
        issues["division_ops"].append(f"Line {i}: {line.strip()}")

# 3. Find unsafe dict/list access
for i, line in enumerate(lines, 1):
    # Dict access without .get()
    if re.search(r'\w+\[\s*["\']\w+["\']\s*\]', line) and '.get(' not in line:
        if '=' not in line or '[' in line.split('=')[0]:  # Not assignment
            issues["dict_access"].append(f"Line {i}: {line.strip()}")
    
    # List access without length check
    if re.search(r'\w+\[\d+\]', line):
        if 'len(' not in '\n'.join(lines[max(0, i-5):i]):
            issues["list_access"].append(f"Line {i}: {line.strip()}")

# 4. Find type conversions without validation
for i, line in enumerate(lines, 1):
    if re.search(r'(float|int)\([^)]+\)', line):
        # Check if value is validated first
        if 'try:' not in '\n'.join(lines[max(0, i-5):i]):
            issues["type_conversions"].append(f"Line {i}: {line.strip()}")

# 5. Find state file operations
state_file_patterns = [
    r'\.read_text\(\)',
    r'\.write_text\(\)',
    r'json\.loads?\(',
    r'json\.dumps?\(',
    r'load_metadata',
    r'atomic_write'
]

for i, line in enumerate(lines, 1):
    for pattern in state_file_patterns:
        if re.search(pattern, line):
            context = '\n'.join(lines[max(0, i-10):i+5])
            if 'try:' not in context or 'except' not in context:
                issues["state_file_ops"].append(f"Line {i}: {line.strip()}")

print("\n[1] API CALLS WITHOUT ERROR HANDLING")
print("-" * 80)
for issue in issues["api_calls"][:20]:
    print(f"  {issue}")

print(f"\n[2] DIVISION OPERATIONS (Potential Divide by Zero)")
print("-" * 80)
for issue in issues["division_ops"][:20]:
    print(f"  {issue}")

print(f"\n[3] UNSAFE DICT/LIST ACCESS")
print("-" * 80)
for issue in issues["dict_access"][:20]:
    print(f"  {issue}")
for issue in issues["list_access"][:20]:
    print(f"  {issue}")

print(f"\n[4] TYPE CONVERSIONS WITHOUT VALIDATION")
print("-" * 80)
for issue in issues["type_conversions"][:20]:
    print(f"  {issue}")

print(f"\n[5] STATE FILE OPERATIONS WITHOUT ERROR HANDLING")
print("-" * 80)
for issue in issues["state_file_ops"][:20]:
    print(f"  {issue}")

print("\n" + "="*80)
print(f"TOTAL ISSUES FOUND: {sum(len(v) for v in issues.values())}")
print("="*80)
