#!/usr/bin/env python3
"""
Execute Droplet Deployment - Complete Workflow
User → Cursor → Git → Droplet (SSH) → Git → Cursor → User
This script executes the COMPLETE workflow including SSH to droplet.
"""

import subprocess
import sys
import time
import json
from pathlib import Path
from datetime import datetime, timezone

def execute_droplet_deployment():
    """Execute complete deployment on droplet via SSH"""
    print("=" * 80)
    print("EXECUTING DROPLET DEPLOYMENT - COMPLETE WORKFLOW")
    print("=" * 80)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    # Step 1: Ensure code is pushed
    print("Step 1: Ensuring code is pushed to Git...")
    result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
    if result.returncode == 0:
        print("[OK] Code pushed to Git")
    else:
        print("[WARNING] Git push had issues (may already be up to date)")
    print()
    
    # Step 2: Connect to droplet and execute deployment
    print("Step 2: Connecting to droplet via SSH...")
    try:
        from droplet_client import DropletClient
        client = DropletClient()
        
        print("[OK] Connected to droplet")
        print()
        
        # Step 2a: Pull latest code
        print("Step 2a: Pulling latest code on droplet...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && git fetch origin main && git reset --hard origin/main",
            timeout=120
        )
        
        if exit_code == 0:
            print("[OK] Code pulled successfully")
            if stdout:
                print(f"  Output: {stdout.strip()[:200]}")
        else:
            print(f"[FAIL] Git pull failed: {stderr[:200] if stderr else 'Unknown error'}")
            client.close()
            return False
        print()
        
        # Step 2b: Make script executable and run deployment
        print("Step 2b: Running deployment verification script...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && chmod +x FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh && bash FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh",
            timeout=600  # 10 minutes for full deployment
        )
        
        if exit_code == 0:
            print("[OK] Deployment script completed")
            if stdout:
                # Show last 30 lines of output
                lines = stdout.strip().split('\n')
                print("  Last output lines:")
                for line in lines[-30:]:
                    print(f"    {line}")
        else:
            print(f"[WARNING] Deployment script had issues (exit code: {exit_code})")
            if stderr:
                print(f"  Error: {stderr.strip()[:300]}")
            if stdout:
                print("  Output:")
                lines = stdout.strip().split('\n')
                for line in lines[-20:]:
                    print(f"    {line}")
        print()
        
        client.close()
        
    except ImportError:
        print("[ERROR] droplet_client not available")
        print("Cannot execute automatically. Manual deployment required:")
        print("  SSH into droplet and run:")
        print("    cd ~/stock-bot")
        print("    git pull origin main")
        print("    bash FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh")
        return False
    except Exception as e:
        print(f"[ERROR] SSH connection failed: {e}")
        print("Cannot execute automatically. Manual deployment required:")
        print("  SSH into droplet and run:")
        print("    cd ~/stock-bot")
        print("    git pull origin main")
        print("    bash FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh")
        return False
    
    # Step 3: Results are pushed synchronously during deployment
    print("Step 3: Deployment script pushes results synchronously...")
    print()
    
    # Step 4: Pull results from Git
    print("Step 4: Pulling results from Git...")
    result = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True)
    if result.returncode == 0:
        print("[OK] Results pulled from Git")
        if "Updating" in result.stdout or "Fast-forward" in result.stdout:
            print("  New results received!")
    else:
        print("[WARNING] Git pull had issues")
    print()
    
    # Step 5: Verify results
    print("Step 5: Verifying deployment results...")
    results = {}
    
    verify_file = Path("droplet_verification_results.json")
    if verify_file.exists():
        print("[OK] Droplet verification results found")
        try:
            with open(verify_file) as f:
                data = json.load(f)
                status = data.get('overall_status', 'UNKNOWN')
                print(f"  Overall status: {status}")
                results['verification'] = status == 'PASS'
        except Exception as e:
            print(f"  [ERROR] Could not read: {e}")
            results['verification'] = False
    else:
        print("[MISSING] Droplet verification results not found")
        results['verification'] = False
    
    integration_file = Path("structural_intelligence_test_results.json")
    if integration_file.exists():
        print("[OK] Integration test results found")
        try:
            with open(integration_file) as f:
                data = json.load(f)
                passed = data.get('tests_passed', 0)
                total = data.get('tests_total', 0)
                print(f"  Tests: {passed}/{total} passed")
                results['integration'] = passed == total
        except Exception as e:
            print(f"  [ERROR] Could not read: {e}")
            results['integration'] = False
    else:
        print("[MISSING] Integration test results not found")
        results['integration'] = False
    
    regression_file = Path("regression_test_results.json")
    if regression_file.exists():
        print("[OK] Regression test results found")
        try:
            with open(regression_file) as f:
                data = json.load(f)
                passed = data.get('tests_passed', 0)
                total = data.get('tests_total', 0)
                print(f"  Tests: {passed}/{total} passed")
                results['regression'] = passed == total
        except Exception as e:
            print(f"  [ERROR] Could not read: {e}")
            results['regression'] = False
    else:
        print("[MISSING] Regression test results not found")
        results['regression'] = False
    
    print()
    print("=" * 80)
    print("DEPLOYMENT COMPLETE")
    print("=" * 80)
    print(f"Completed: {datetime.now(timezone.utc).isoformat()}")
    print()
    print("Results Summary:")
    print(f"  Verification: {'PASS' if results.get('verification') else 'FAIL/MISSING'}")
    print(f"  Integration: {'PASS' if results.get('integration') else 'FAIL/MISSING'}")
    print(f"  Regression: {'PASS' if results.get('regression') else 'FAIL/MISSING'}")
    print()
    
    if all(results.values()):
        print("[SUCCESS] ALL VERIFICATIONS PASSED - DEPLOYMENT SUCCESSFUL")
        return True
    else:
        print("[WARNING] SOME VERIFICATIONS FAILED OR MISSING")
        print()
        print("If results are missing, the deployment script may still be running.")
        print("Wait a few minutes and pull again: git pull origin main")
        return False

if __name__ == "__main__":
    success = execute_droplet_deployment()
    sys.exit(0 if success else 1)

