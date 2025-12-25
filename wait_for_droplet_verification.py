#!/usr/bin/env python3
"""
Wait for droplet verification results and report status
This script monitors for droplet_verification_results.json to appear in git
"""

import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

def check_for_results():
    """Check if verification results are available"""
    results_file = Path("droplet_verification_results.json")
    if results_file.exists():
        try:
            with open(results_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None
    return None

def pull_from_git():
    """Pull latest from git"""
    try:
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except:
        return False

def main():
    """Main monitoring loop"""
    print("=" * 80)
    print("WAITING FOR DROPLET VERIFICATION RESULTS")
    print("=" * 80)
    print()
    print("Monitoring for droplet_verification_results.json...")
    print("The droplet will automatically:")
    print("  1. Pull latest code (triggered by git push)")
    print("  2. Run complete verification")
    print("  3. Push results back to git")
    print()
    
    max_attempts = 20
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"Attempt {attempt}/{max_attempts}: Checking for results...")
        
        # Pull from git first
        if pull_from_git():
            print("  ✓ Pulled from git")
        
        # Check for results
        results = check_for_results()
        if results:
            print("\n" + "=" * 80)
            print("DROPLET VERIFICATION RESULTS RECEIVED")
            print("=" * 80)
            print()
            print(f"Timestamp: {results.get('timestamp', 'unknown')}")
            print(f"Verification Status: {'[PASS]' if results.get('verification_passed') else '[FAIL]'}")
            print()
            
            # Print test results
            print("Test Results:")
            for test_name, status in results.get("tests", {}).items():
                status_char = "[PASS]" if status == "PASS" else "[FAIL]"
                print(f"  {status_char} {test_name}")
            
            # Print errors if any
            if results.get("errors"):
                print("\nErrors:")
                for error in results["errors"]:
                    print(f"  - {error}")
            
            print()
            if results.get("verification_passed"):
                print("[SUCCESS] ALL VERIFICATIONS PASSED ON DROPLET")
                return 0
            else:
                print(f"[FAILURE] {len(results.get('errors', []))} VERIFICATION(S) FAILED")
                return 1
        
        if attempt < max_attempts:
            print("  No results yet, waiting 10 seconds...")
            time.sleep(10)
    
    print("\n" + "=" * 80)
    print("TIMEOUT: Droplet verification results not received")
    print("=" * 80)
    print()
    print("Possible reasons:")
    print("  1. Droplet hasn't pulled yet (may need manual trigger)")
    print("  2. Post-merge hook not configured")
    print("  3. Verification script encountered errors")
    print()
    print("To manually trigger on droplet, SSH in and run:")
    print("  cd ~/stock-bot && git pull origin main")
    print()
    return 2

if __name__ == "__main__":
    import sys
    sys.exit(main())

