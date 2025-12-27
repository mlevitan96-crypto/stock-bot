#!/usr/bin/env python3
"""
End-to-End Verification - Confirms everything works in full circle
This verifies the complete workflow: Code → Git → Droplet → Verification → Results → Git
"""

import json
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone

def check_git_status():
    """Check if we're up to date with remote"""
    try:
        result = subprocess.run(
            ["git", "fetch", "origin", "main"],
            capture_output=True,
            text=True,
            timeout=30
        )
        result = subprocess.run(
            ["git", "status", "-sb"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return "ahead" not in result.stdout and "behind" not in result.stdout
    except:
        return False

def check_droplet_results():
    """Check if droplet verification results are available"""
    results_file = Path("droplet_verification_results.json")
    if results_file.exists():
        try:
            with open(results_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None
    return None

def verify_local_implementation():
    """Verify all implementations work locally"""
    print("=" * 80)
    print("LOCAL VERIFICATION")
    print("=" * 80)
    print()
    
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "local_verification": {},
        "errors": []
    }
    
    # Run backtest
    print("Running comprehensive backtest...")
    try:
        result = subprocess.run(
            ["python", "backtest_all_implementations.py"],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("  [PASS] Backtest passed")
            results["local_verification"]["backtest"] = "PASS"
        else:
            print(f"  [FAIL] Backtest failed")
            results["local_verification"]["backtest"] = "FAIL"
            results["errors"].append("Backtest failed")
    except Exception as e:
        print(f"  [FAIL] Backtest error: {e}")
        results["local_verification"]["backtest"] = "FAIL"
        results["errors"].append(f"Backtest error: {e}")
    
    # Check files exist
    print("\nChecking implementation files...")
    required_files = [
        "tca_data_manager.py",
        "execution_quality_learner.py",
        "signal_pattern_learner.py",
        "parameter_optimizer.py",
        "backtest_all_implementations.py",
        "complete_droplet_verification.py",
        "force_droplet_pull_and_verify.sh"
    ]
    
    for file in required_files:
        if Path(file).exists():
            print(f"  [PASS] {file}")
            results["local_verification"][f"file_{file}"] = "PASS"
        else:
            print(f"  [FAIL] {file} MISSING")
            results["local_verification"][f"file_{file}"] = "FAIL"
            results["errors"].append(f"Missing file: {file}")
    
    return results

def main():
    """Main verification"""
    print("=" * 80)
    print("END-TO-END VERIFICATION")
    print("=" * 80)
    print()
    
    # Step 1: Verify local implementation
    local_results = verify_local_implementation()
    
    # Step 2: Check Git status
    print("\n" + "=" * 80)
    print("GIT STATUS CHECK")
    print("=" * 80)
    print()
    if check_git_status():
        print("[PASS] Git is up to date")
    else:
        print("[WARNING] Git may not be up to date")
    
    # Step 3: Check for droplet results
    print("\n" + "=" * 80)
    print("DROPLET RESULTS CHECK")
    print("=" * 80)
    print()
    
    # Pull from git to get latest results
    print("Pulling from Git to check for droplet results...")
    try:
        subprocess.run(
            ["git", "pull", "origin", "main"],
            capture_output=True,
            text=True,
            timeout=30
        )
    except:
        pass
    
    droplet_results = check_droplet_results()
    if droplet_results:
        print("[SUCCESS] Droplet verification results found!")
        print(f"  Timestamp: {droplet_results.get('timestamp', 'unknown')}")
        print(f"  Status: {'[PASS]' if droplet_results.get('verification_passed') else '[FAIL]'}")
        
        # Print test summary
        tests = droplet_results.get("tests", {})
        passed = sum(1 for v in tests.values() if v == "PASS")
        total = len(tests)
        print(f"  Tests: {passed}/{total} passed")
        
        if droplet_results.get("errors"):
            print(f"  Errors: {len(droplet_results['errors'])}")
            for error in droplet_results["errors"][:5]:
                print(f"    - {error}")
        
        if droplet_results.get("verification_passed"):
            print("\n[SUCCESS] Droplet verification PASSED")
        else:
            print("\n[FAILURE] Droplet verification FAILED")
    else:
        print("[WAITING] Droplet verification results not yet available")
        print("  The droplet needs to pull and run verification")
        print("  This will happen automatically via post-merge hook")
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL STATUS")
    print("=" * 80)
    print()
    
    local_passed = all(
        v == "PASS" for k, v in local_results["local_verification"].items()
        if k.startswith("file_") or k == "backtest"
    )
    
    print(f"Local Implementation: {'[PASS]' if local_passed else '[FAIL]'}")
    print(f"Droplet Verification: {'[PASS]' if droplet_results and droplet_results.get('verification_passed') else '[WAITING/FAIL]'}")
    
    if local_passed and droplet_results and droplet_results.get("verification_passed"):
        print("\n[SUCCESS] END-TO-END VERIFICATION COMPLETE")
        print("Everything is working in full circle!")
        return 0
    elif local_passed:
        print("\n[PARTIAL] Local verification passed, waiting for droplet results")
        return 1
    else:
        print("\n[FAILURE] Local verification failed")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())

