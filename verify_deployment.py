#!/usr/bin/env python3
"""Quick verification that all fixes are deployed"""
import sys
from pathlib import Path

print("=" * 60)
print("DEPLOYMENT VERIFICATION")
print("=" * 60)

# Check 1: critical_trading_health_checks.py exists
if Path("critical_trading_health_checks.py").exists():
    print("✓ critical_trading_health_checks.py exists")
else:
    print("✗ critical_trading_health_checks.py missing")

# Check 2: RESILIENT_ARCHITECTURE_MONITORING.md exists
if Path("RESILIENT_ARCHITECTURE_MONITORING.md").exists():
    print("✓ RESILIENT_ARCHITECTURE_MONITORING.md exists")
else:
    print("✗ RESILIENT_ARCHITECTURE_MONITORING.md missing")

# Check 3: sre_diagnostics has new methods
try:
    with open("sre_diagnostics.py") as f:
        content = f.read()
        if "def check_entry_thresholds" in content:
            print("✓ sre_diagnostics.check_entry_thresholds exists")
        else:
            print("✗ check_entry_thresholds missing")
        if "def check_freshness_killing_scores" in content:
            print("✓ sre_diagnostics.check_freshness_killing_scores exists")
        else:
            print("✗ check_freshness_killing_scores missing")
except:
    print("✗ Error checking sre_diagnostics.py")

# Check 4: health_supervisor has new check
try:
    with open("health_supervisor.py") as f:
        content = f.read()
        if "_check_critical_trading_issues" in content:
            print("✓ health_supervisor._check_critical_trading_issues exists")
        else:
            print("✗ _check_critical_trading_issues missing")
except:
    print("✗ Error checking health_supervisor.py")

# Check 5: main.py has freshness fix
try:
    with open("main.py") as f:
        content = f.read()
        if 'enriched["freshness"] = 0.9' in content:
            print("✓ main.py freshness fix (0.9 minimum) exists")
        else:
            print("✗ freshness fix missing in main.py")
except:
    print("✗ Error checking main.py")

print("=" * 60)
