#!/usr/bin/env python3
"""
Complete Full Cycle - Push to Git → Trigger Droplet → Wait for Results → Verify
This script completes the entire workflow end-to-end with no gaps.
"""

import subprocess
import sys
import time
import json
from pathlib import Path
from datetime import datetime, timezone

def push_to_git():
    """Ensure everything is pushed to Git"""
    print("=" * 80)
    print("STEP 1: PUSHING TO GIT")
    print("=" * 80)
    print()
    
    # Check for uncommitted changes
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )
    
    if result.stdout.strip():
        print("Uncommitted changes found, committing...")
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(
            ["git", "commit", "-m", "Complete full cycle - all implementations"],
            check=True
        )
    
    # Push to Git
    print("Pushing to GitHub...")
    result = subprocess.run(
        ["git", "push", "origin", "main"],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode == 0:
        print("[PASS] Code pushed to Git")
        return True
    else:
        print(f"[FAIL] Git push failed: {result.stderr[:200]}")
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

def wait_for_droplet_results(max_wait_minutes=10):
    """Wait for droplet to pull, verify, and push results back"""
    print("\n" + "=" * 80)
    print("STEP 2: WAITING FOR DROPLET VERIFICATION")
    print("=" * 80)
    print()
    print("The droplet will:")
    print("  1. Pull latest code (via post-merge hook)")
    print("  2. Run complete verification")
    print("  3. Push results back to Git")
    print()
    print("Monitoring for results...")
    print()
    
    max_attempts = max_wait_minutes * 6  # Check every 10 seconds
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        
        # Pull from git to get latest results
        try:
            subprocess.run(
                ["git", "pull", "origin", "main"],
                capture_output=True,
                text=True,
                timeout=30
            )
        except:
            pass
        
        # Check for results
        results = check_droplet_results()
        if results:
            print("\n" + "=" * 80)
            print("DROPLET VERIFICATION RESULTS RECEIVED")
            print("=" * 80)
            print()
            print(f"Timestamp: {results.get('timestamp', 'unknown')}")
            print(f"Status: {'[PASS]' if results.get('verification_passed') else '[FAIL]'}")
            print()
            
            # Print test summary
            tests = results.get("tests", {})
            passed = sum(1 for v in tests.values() if v == "PASS")
            total = len(tests)
            print(f"Tests: {passed}/{total} passed")
            
            if results.get("errors"):
                print(f"\nErrors ({len(results['errors'])}):")
                for error in results["errors"][:10]:
                    print(f"  - {error}")
            
            return results
        
        if attempt % 6 == 0:  # Every minute
            print(f"  Still waiting... ({attempt // 6} minutes)")
        else:
            print(".", end="", flush=True)
        
        time.sleep(10)
    
    print("\n\n[WARNING] Timeout waiting for droplet results")
    print("The droplet may need to be manually triggered")
    return None

def verify_end_to_end(results):
    """Verify end-to-end that everything works"""
    print("\n" + "=" * 80)
    print("STEP 3: END-TO-END VERIFICATION")
    print("=" * 80)
    print()
    
    if not results:
        print("[FAIL] No droplet results to verify")
        return False
    
    # Check local implementation
    print("Verifying local implementation...")
    try:
        result = subprocess.run(
            ["python", "backtest_all_implementations.py"],
            capture_output=True,
            text=True,
            timeout=60
        )
        local_passed = result.returncode == 0
        print(f"  Local backtest: {'[PASS]' if local_passed else '[FAIL]'}")
    except:
        local_passed = False
        print("  Local backtest: [FAIL]")
    
    # Check droplet results
    droplet_passed = results.get("verification_passed", False)
    print(f"  Droplet verification: {'[PASS]' if droplet_passed else '[FAIL]'}")
    
    # Final status
    if local_passed and droplet_passed:
        print("\n[SUCCESS] END-TO-END VERIFICATION COMPLETE")
        print("Everything is working in full circle!")
        return True
    else:
        print("\n[FAILURE] End-to-end verification incomplete")
        return False

def main():
    """Main entry point"""
    print("=" * 80)
    print("COMPLETE FULL CYCLE - END-TO-END VERIFICATION")
    print("=" * 80)
    print()
    
    # Step 1: Push to Git
    if not push_to_git():
        print("\n[FAILURE] Could not push to Git")
        return 1
    
    # Step 2: Wait for droplet results
    results = wait_for_droplet_results(max_wait_minutes=10)
    
    # Step 3: Verify end-to-end
    success = verify_end_to_end(results)
    
    print("\n" + "=" * 80)
    if success:
        print("[SUCCESS] FULL CYCLE COMPLETE - EVERYTHING WORKING")
        print("=" * 80)
        return 0
    else:
        print("[PARTIAL] Full cycle incomplete - check results above")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    sys.exit(main())

