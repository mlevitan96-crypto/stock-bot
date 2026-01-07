#!/usr/bin/env python3
"""Audit code for failure points and harden critical sections"""

import ast
import sys
from pathlib import Path

print("="*80)
print("CODE HARDENING AUDIT")
print("="*80)

# Check main.py for potential failure points
main_file = Path("main.py")
if main_file.exists():
    content = main_file.read_text()
    
    issues = []
    
    # Check for bare except clauses (dangerous - catches everything)
    bare_except_count = content.count("except:\n") + content.count("except :\n")
    if bare_except_count > 0:
        issues.append(f"Found {bare_except_count} bare 'except:' clauses - should specify exception types")
    
    # Check for uninitialized variables in critical paths
    # Check portfolio delta calculation
    if "net_delta_pct" in content and "open_positions" in content:
        # Check if open_positions is always initialized
        if "open_positions = []" not in content:
            issues.append("open_positions may not be initialized in all code paths")
    
    # Check for API calls without error handling
    api_calls = ["api.list_positions()", "api.get_account()", "api.submit_order("]
    for call in api_calls:
        if call in content:
            # Check if wrapped in try/except nearby
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if call in line:
                    # Check if there's a try within 10 lines before
                    has_try = any("try:" in lines[j] for j in range(max(0, i-10), i))
                    if not has_try:
                        issues.append(f"API call '{call}' at line {i+1} may not be error-handled")
    
    print(f"\nPotential Issues Found: {len(issues)}")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("main.py not found")

print("\n" + "="*80)
