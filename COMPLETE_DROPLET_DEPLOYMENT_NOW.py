#!/usr/bin/env python3
"""
Complete Droplet Deployment - Forces deployment and verification
This script attempts to SSH into droplet and execute deployment
"""

import subprocess
import sys
import time
import json
from pathlib import Path
from datetime import datetime, timezone

def execute_on_droplet_via_ssh(command, description):
    """Execute command on droplet via SSH if possible"""
    try:
        from droplet_client import DropletClient
        client = DropletClient()
        
        print(f"  Executing: {description}...")
        stdout, stderr, exit_code = client._execute_with_cd(command, timeout=300)
        
        if exit_code == 0:
            print(f"  [OK] {description} completed")
            if stdout:
                print(f"    Output: {stdout.strip()[:200]}")
            client.close()
            return True
        else:
            print(f"  [FAIL] {description} failed: {stderr[:200] if stderr else 'Unknown error'}")
            client.close()
            return False
    except ImportError:
        print(f"  ⚠ Cannot execute automatically - droplet_client not available")
        print(f"  Manual command: {command}")
        return None
    except Exception as e:
        print(f"  ⚠ SSH connection failed: {e}")
        print(f"  Manual command: {command}")
        return None

def main():
    """Complete deployment workflow"""
    print("=" * 80)
    print("COMPLETE DROPLET DEPLOYMENT - STRUCTURAL INTELLIGENCE")
    print("=" * 80)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    # Step 1: Ensure code is pushed
    print("Step 1: Ensuring all code is pushed to Git...")
    result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
    if result.returncode == 0:
        print("  [OK] Code pushed to Git")
    else:
        print("  [WARNING] Git push had issues (may already be up to date)")
    print()
    
    # Step 2: Pull on droplet
    print("Step 2: Pulling latest code on droplet...")
    result = execute_on_droplet_via_ssh(
        "cd ~/stock-bot && git fetch origin main && git reset --hard origin/main",
        "Pull latest code"
    )
    print()
    
    # Step 3: Run deployment script
    print("Step 3: Running deployment verification script...")
    result = execute_on_droplet_via_ssh(
        "cd ~/stock-bot && chmod +x FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh && bash FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh",
        "Deployment verification"
    )
    print()
    
    # Step 4: Wait for results
    print("Step 4: Waiting for results (60 seconds)...")
    time.sleep(60)
    print()
    
    # Step 5: Pull results
    print("Step 5: Pulling results from Git...")
    result = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True)
    if result.returncode == 0:
        print("  ✓ Results pulled from Git")
    else:
        print("  ⚠ Git pull had issues")
    print()
    
    # Step 6: Verify results
    print("Step 6: Verifying results...")
    results = {}
    
    verify_file = Path("droplet_verification_results.json")
    if verify_file.exists():
        print("  [OK] Droplet verification results found")
        try:
            with open(verify_file) as f:
                data = json.load(f)
                status = data.get('overall_status', 'UNKNOWN')
                print(f"    Overall status: {status}")
                results['verification'] = status == 'PASS'
        except:
            results['verification'] = False
    else:
        print("  [MISSING] Droplet verification results not found")
        results['verification'] = False
    
    integration_file = Path("structural_intelligence_test_results.json")
    if integration_file.exists():
        print("  [OK] Integration test results found")
        try:
            with open(integration_file) as f:
                data = json.load(f)
                passed = data.get('tests_passed', 0)
                total = data.get('tests_total', 0)
                print(f"    Tests: {passed}/{total} passed")
                results['integration'] = passed == total
        except:
            results['integration'] = False
    else:
        print("  [MISSING] Integration test results not found")
        results['integration'] = False
    
    regression_file = Path("regression_test_results.json")
    if regression_file.exists():
        print("  [OK] Regression test results found")
        try:
            with open(regression_file) as f:
                data = json.load(f)
                passed = data.get('tests_passed', 0)
                total = data.get('tests_total', 0)
                print(f"    Tests: {passed}/{total} passed")
                results['regression'] = passed == total
        except:
            results['regression'] = False
    else:
        print("  [MISSING] Regression test results not found")
        results['regression'] = False
    
    print()
    print("=" * 80)
    print("DEPLOYMENT COMPLETE")
    print("=" * 80)
    print(f"Completed: {datetime.now(timezone.utc).isoformat()}")
    print()
    print("Results:")
    print(f"  Verification: {'PASS' if results.get('verification') else 'FAIL/MISSING'}")
    print(f"  Integration: {'PASS' if results.get('integration') else 'FAIL/MISSING'}")
    print(f"  Regression: {'PASS' if results.get('regression') else 'FAIL/MISSING'}")
    print()
    
    if all(results.values()):
        print("[SUCCESS] ALL VERIFICATIONS PASSED - DEPLOYMENT SUCCESSFUL")
        return 0
    else:
        print("⚠ SOME VERIFICATIONS FAILED OR MISSING")
        print()
        print("If results are missing, manually run on droplet:")
        print("  cd ~/stock-bot")
        print("  git pull origin main")
        print("  bash FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh")
        return 1

if __name__ == "__main__":
    sys.exit(main())

