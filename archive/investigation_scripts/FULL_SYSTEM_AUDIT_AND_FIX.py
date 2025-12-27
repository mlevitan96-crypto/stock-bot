#!/usr/bin/env python3
"""
FULL SYSTEM AUDIT AND FIX
Comprehensive diagnostic to identify ALL issues preventing bot from running
"""

import sys
import subprocess
import traceback
from pathlib import Path

def check_imports():
    """Check all critical imports"""
    print("=" * 80)
    print("CHECKING IMPORTS")
    print("=" * 80)
    
    critical_imports = [
        "main",
        "config.registry",
        "uw_flow_daemon",
        "v3_2_features",
        "dashboard",
        "deploy_supervisor",
    ]
    
    failed = []
    for module in critical_imports:
        try:
            __import__(module)
            print(f"✓ {module}")
        except Exception as e:
            print(f"✗ {module}: {e}")
            failed.append((module, str(e)))
            traceback.print_exc()
    
    return failed

def check_syntax():
    """Check syntax of critical files"""
    print("\n" + "=" * 80)
    print("CHECKING SYNTAX")
    print("=" * 80)
    
    critical_files = [
        "main.py",
        "uw_flow_daemon.py",
        "v3_2_features.py",
        "dashboard.py",
        "deploy_supervisor.py",
    ]
    
    failed = []
    for file in critical_files:
        if not Path(file).exists():
            print(f"✗ {file}: FILE NOT FOUND")
            failed.append((file, "FILE NOT FOUND"))
            continue
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", file],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"✓ {file}")
            else:
                print(f"✗ {file}: {result.stderr}")
                failed.append((file, result.stderr))
        except Exception as e:
            print(f"✗ {file}: {e}")
            failed.append((file, str(e)))
    
    return failed

def check_runtime():
    """Try to run main.py and capture errors"""
    print("\n" + "=" * 80)
    print("CHECKING RUNTIME (main.py)")
    print("=" * 80)
    
    try:
        # Try importing main
        import main
        print("✓ main.py imports successfully")
        
        # Try accessing critical attributes
        try:
            _ = main.Config
            print("✓ Config class accessible")
        except Exception as e:
            print(f"✗ Config class: {e}")
            return [("main.Config", str(e))]
        
        try:
            _ = main.app
            print("✓ Flask app accessible")
        except Exception as e:
            print(f"✗ Flask app: {e}")
            return [("main.app", str(e))]
        
        return []
    except Exception as e:
        print(f"✗ main.py import failed: {e}")
        traceback.print_exc()
        return [("main.py", str(e))]

def main():
    print("=" * 80)
    print("FULL SYSTEM AUDIT")
    print("=" * 80)
    print()
    
    import_failures = check_imports()
    syntax_failures = check_syntax()
    runtime_failures = check_runtime()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    all_failures = import_failures + syntax_failures + runtime_failures
    
    if not all_failures:
        print("✓ ALL CHECKS PASSED")
        return 0
    else:
        print(f"✗ {len(all_failures)} ISSUES FOUND:")
        for item, error in all_failures:
            print(f"  - {item}: {error[:100]}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
