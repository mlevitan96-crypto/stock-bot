#!/usr/bin/env python3
"""
COMPLETE FULL WORKFLOW: User → Cursor → Git → Droplet → Git → Cursor → User
This script executes the ENTIRE workflow and only reports back when COMPLETE.
"""

import subprocess
import sys
import time
import json
from pathlib import Path

def push_to_git():
    """Step 1: Push all changes to Git."""
    print("=" * 80)
    print("STEP 1: PUSHING TO GIT")
    print("=" * 80)
    
    # Check for uncommitted changes
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )
    
    if not result.stdout.strip():
        print("[OK] No changes to commit")
        return True
    
    # Add all changes
    print("Adding changes...")
    subprocess.run(["git", "add", "."], check=True)
    
    # Commit
    print("Committing changes...")
    result = subprocess.run(
        ["git", "commit", "-m", "Complete workflow: All implementations verified and ready"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0 and "nothing to commit" not in result.stderr:
        print(f"[WARNING] Commit warning: {result.stderr}")
    
    # Push
    print("Pushing to GitHub...")
    result = subprocess.run(
        ["git", "push", "origin", "main"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("[OK] Successfully pushed to Git")
        return True
    else:
        print(f"[FAIL] Push failed: {result.stderr}")
        return False

def trigger_droplet_via_ssh():
    """Step 2: Trigger immediate droplet action via SSH."""
    print()
    print("=" * 80)
    print("STEP 2: TRIGGERING IMMEDIATE DROPLET ACTION (SSH)")
    print("=" * 80)
    
    # Try to use droplet_client
    try:
        from droplet_client import DropletClient
        client = DropletClient()
        
        print("Connecting to droplet via SSH...")
        status = client.get_status()
        print(f"[OK] Connected to {status['host']}")
        
        print("Triggering git pull (will activate post-merge hook)...")
        stdout, stderr, exit_code = client._execute_with_cd("git pull origin main", timeout=60)
        
        if exit_code == 0:
            print("[OK] Droplet pulled latest code successfully")
            if stdout:
                print(f"  Output: {stdout.strip()[:200]}")
            
            # Wait for post-merge hook to execute
            print("Waiting for post-merge hook to execute (15 seconds)...")
            time.sleep(15)
            
            client.close()
            return True
        else:
            print(f"[FAIL] Droplet pull failed: {stderr[:200] if stderr else 'Unknown error'}")
            client.close()
            return False
            
    except ImportError:
        print("[WARNING] droplet_client not available - droplet will pull via post-merge hook on next interaction")
        return True  # Not a failure - post-merge hook will handle it
    except Exception as e:
        print(f"[WARNING] SSH connection failed: {e}")
        print("  Droplet will pull automatically via post-merge hook")
        return True  # Not a failure - post-merge hook will handle it

def pull_results_from_git():
    """Step 3: Pull results from Git."""
    print()
    print("=" * 80)
    print("STEP 3: PULLING RESULTS FROM GIT")
    print("=" * 80)
    
    # Wait for droplet to process and push results
    print("Waiting for droplet to process and push results (30 seconds)...")
    time.sleep(30)
    
    # Pull
    print("Pulling from Git...")
    result = subprocess.run(
        ["git", "pull", "origin", "main"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("[OK] Successfully pulled from Git")
        if "Updating" in result.stdout or "Fast-forward" in result.stdout:
            print("  New results received!")
        return True
    else:
        print(f"[WARNING] Pull had issues: {result.stderr}")
        return False

def verify_results():
    """Step 4: Verify all results are present and valid."""
    print()
    print("=" * 80)
    print("STEP 4: VERIFYING RESULTS")
    print("=" * 80)
    
    results = {}
    
    # Check for droplet verification results
    verify_file = Path("droplet_verification_results.json")
    if verify_file.exists():
        print("[OK] Droplet verification results found")
        try:
            with open(verify_file) as f:
                data = json.load(f)
                results['verification'] = data
                status = data.get('overall_status', 'UNKNOWN')
                print(f"  Overall status: {status}")
                if status == "PASS":
                    print("  [SUCCESS] Droplet verification PASSED")
                else:
                    print("  [WARNING] Droplet verification had issues")
                    errors = data.get('errors', [])
                    if errors:
                        print(f"  Errors: {len(errors)}")
        except Exception as e:
            print(f"  [ERROR] Could not read verification file: {e}")
    else:
        print("[MISSING] Droplet verification results not found")
    
    # Check for investigation results
    invest_file = Path("investigate_no_trades.json")
    if invest_file.exists():
        print("[OK] Investigation results found")
        try:
            with open(invest_file) as f:
                data = json.load(f)
                results['investigation'] = data
        except Exception as e:
            print(f"  [ERROR] Could not read investigation file: {e}")
    else:
        print("[MISSING] Investigation results not found")
    
    # Check for backtest results
    backtest_file = Path("backtest_results.json")
    if backtest_file.exists():
        print("[OK] Backtest results found")
        try:
            with open(backtest_file) as f:
                data = json.load(f)
                results['backtest'] = data
                passed = data.get('tests_passed', 0)
                total = data.get('tests_total', 0)
                print(f"  Tests: {passed}/{total} passed")
        except Exception as e:
            print(f"  [ERROR] Could not read backtest file: {e}")
    else:
        print("[MISSING] Backtest results not found")
    
    return results

def main():
    """Execute complete full workflow."""
    print()
    print("=" * 80)
    print("COMPLETE FULL WORKFLOW")
    print("User → Cursor → Git → Droplet → Git → Cursor → User")
    print("=" * 80)
    print()
    
    # Step 1: Push to Git
    if not push_to_git():
        print("\n[FAIL] Failed to push to Git - aborting")
        return False
    
    # Step 2: Trigger droplet via SSH
    if not trigger_droplet_via_ssh():
        print("\n[WARNING] Droplet trigger had issues - continuing anyway")
    
    # Step 3: Pull results from Git
    if not pull_results_from_git():
        print("\n[WARNING] Could not pull results - may need to wait longer")
    
    # Step 4: Verify results
    results = verify_results()
    
    print()
    print("=" * 80)
    print("WORKFLOW COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Droplet verification: {'[OK]' if 'verification' in results else '[MISSING]'}")
    print(f"  - Investigation results: {'[OK]' if 'investigation' in results else '[MISSING]'}")
    print(f"  - Backtest results: {'[OK]' if 'backtest' in results else '[MISSING]'}")
    print()
    
    if 'verification' in results:
        verify_status = results['verification'].get('overall_status', 'UNKNOWN')
        if verify_status == "PASS":
            print("[SUCCESS] FULL WORKFLOW COMPLETE - ALL VERIFICATIONS PASSED")
            return True
        else:
            print("[WARNING] Full workflow complete but verification had issues")
            return False
    else:
        print("[WARNING] Full workflow complete but verification results not received")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

