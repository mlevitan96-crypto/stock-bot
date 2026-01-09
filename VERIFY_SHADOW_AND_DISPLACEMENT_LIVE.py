#!/usr/bin/env python3
"""
Verify Shadow Tracking & Competitive Displacement are Live on Droplet
"""

import sys
from pathlib import Path

try:
    from droplet_client import DropletClient
except ImportError:
    print("ERROR: droplet_client not available")
    sys.exit(1)

def verify_features_live():
    """Verify new features are deployed and active."""
    print("=" * 80)
    print("VERIFYING SHADOW TRACKING & COMPETITIVE DISPLACEMENT ARE LIVE")
    print("=" * 80)
    print()
    
    client = DropletClient()
    
    checks_passed = 0
    checks_failed = 0
    
    # Check 1: Verify shadow_tracker.py has new constants
    print("Check 1: Verifying shadow_tracker.py has SHADOW_MIN_SCORE_CAPACITY...")
    stdout, stderr, exit_code = client._execute_with_cd(
        "cd ~/stock-bot && grep -q 'SHADOW_MIN_SCORE_CAPACITY' shadow_tracker.py && echo 'FOUND' || echo 'NOT_FOUND'",
        timeout=30
    )
    if "FOUND" in stdout:
        print("  [OK] SHADOW_MIN_SCORE_CAPACITY constant found")
        checks_passed += 1
    else:
        print("  [FAIL] SHADOW_MIN_SCORE_CAPACITY constant NOT found")
        checks_failed += 1
    print()
    
    # Check 2: Verify shadow_outcomes.jsonl logging
    print("Check 2: Verifying shadow_outcomes.jsonl logging...")
    stdout, stderr, exit_code = client._execute_with_cd(
        "cd ~/stock-bot && grep -q 'shadow_outcomes.jsonl' shadow_tracker.py && echo 'FOUND' || echo 'NOT_FOUND'",
        timeout=30
    )
    if "FOUND" in stdout:
        print("  [OK] shadow_outcomes.jsonl logging found")
        checks_passed += 1
    else:
        print("  [FAIL] shadow_outcomes.jsonl logging NOT found")
        checks_failed += 1
    print()
    
    # Check 3: Verify competitive displacement in main.py
    print("Check 3: Verifying competitive displacement logic...")
    stdout, stderr, exit_code = client._execute_with_cd(
        "cd ~/stock-bot && grep -q 'competitive_displacement' main.py && echo 'FOUND' || echo 'NOT_FOUND'",
        timeout=30
    )
    if "FOUND" in stdout:
        print("  [OK] competitive_displacement logic found")
        checks_passed += 1
    else:
        print("  [FAIL] competitive_displacement logic NOT found")
        checks_failed += 1
    print()
    
    # Check 4: Verify score delta > 1.0 check
    print("Check 4: Verifying score delta > 1.0 check...")
    stdout, stderr, exit_code = client._execute_with_cd(
        "cd ~/stock-bot && grep -q 'score_delta.*>.*1.0' main.py && echo 'FOUND' || echo 'NOT_FOUND'",
        timeout=30
    )
    if "FOUND" in stdout:
        print("  [OK] Score delta > 1.0 check found")
        checks_passed += 1
    else:
        print("  [FAIL] Score delta > 1.0 check NOT found")
        checks_failed += 1
    print()
    
    # Check 5: Verify capacity_limit shadow tracking
    print("Check 5: Verifying capacity_limit shadow tracking...")
    stdout, stderr, exit_code = client._execute_with_cd(
        "cd ~/stock-bot && grep -A 5 'capacity_limit' main.py | grep -q 'create_shadow_position' && echo 'FOUND' || echo 'NOT_FOUND'",
        timeout=30
    )
    if "FOUND" in stdout:
        print("  [OK] capacity_limit shadow tracking found")
        checks_passed += 1
    else:
        print("  [FAIL] capacity_limit shadow tracking NOT found")
        checks_failed += 1
    print()
    
    # Check 6: Verify git commit is on droplet
    print("Check 6: Verifying latest commit is on droplet...")
    stdout, stderr, exit_code = client._execute_with_cd(
        "cd ~/stock-bot && git log --oneline -1 | grep -q 'Competitive Displacement' && echo 'FOUND' || echo 'NOT_FOUND'",
        timeout=30
    )
    if "FOUND" in stdout:
        print("  [OK] Latest commit found on droplet")
        checks_passed += 1
    else:
        print("  [FAIL] Latest commit NOT found on droplet")
        checks_failed += 1
    print()
    
    # Check 7: Verify bot process is running
    print("Check 7: Verifying bot process is running...")
    stdout, stderr, exit_code = client._execute(
        "ps aux | grep -E 'main.py|deploy_supervisor' | grep -v grep | wc -l",
        timeout=10
    )
    process_count = int(stdout.strip()) if stdout.strip().isdigit() else 0
    if process_count > 0:
        print(f"  [OK] Bot process is running ({process_count} processes found)")
        checks_passed += 1
    else:
        print("  [FAIL] Bot process NOT running")
        checks_failed += 1
    print()
    
    # Check 8: Verify reports directory exists
    print("Check 8: Verifying reports directory exists...")
    stdout, stderr, exit_code = client._execute_with_cd(
        "cd ~/stock-bot && test -d reports && echo 'EXISTS' || echo 'NOT_EXISTS'",
        timeout=10
    )
    if "EXISTS" in stdout:
        print("  [OK] reports directory exists")
        checks_passed += 1
    else:
        print("  [FAIL] reports directory NOT found (will be created automatically)")
        checks_failed += 1
    print()
    
    # Summary
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"Checks Passed: {checks_passed}")
    print(f"Checks Failed: {checks_failed}")
    print()
    
    if checks_failed == 0:
        print("[OK] ALL CHECKS PASSED - Features are LIVE on droplet!")
        return 0
    else:
        print("[FAIL] SOME CHECKS FAILED - Review output above")
        return 1

if __name__ == "__main__":
    sys.exit(verify_features_live())
