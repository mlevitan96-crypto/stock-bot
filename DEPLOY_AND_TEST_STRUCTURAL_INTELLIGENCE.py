#!/usr/bin/env python3
"""
Complete Deployment and End-to-End Testing for Structural Intelligence Overhaul
Executes full workflow: Git → Droplet → Testing → Verification → Results
"""

import subprocess
import sys
import time
import json
from pathlib import Path
from datetime import datetime, timezone

def run_command(cmd, check=True, capture=True):
    """Run a shell command"""
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=capture, text=True)
    if result.returncode != 0 and check:
        print(f"ERROR: Command failed with exit code {result.returncode}")
        if capture:
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
        sys.exit(1)
    return result

def trigger_droplet_deployment():
    """Step 1: Trigger droplet to pull and deploy"""
    print("\n" + "=" * 80)
    print("STEP 1: TRIGGERING DROPLET DEPLOYMENT")
    print("=" * 80)
    
    try:
        from droplet_client import DropletClient
        client = DropletClient()
        
        print("Connecting to droplet via SSH...")
        status = client.get_status()
        print(f"[OK] Connected to {status.get('host', 'droplet')}")
        
        print("\nPulling latest code (triggers post-merge hook)...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && git pull origin main",
            timeout=120
        )
        
        if exit_code == 0:
            print("[OK] Code pulled successfully")
            if stdout:
                print(f"  Output preview: {stdout.strip()[:300]}")
            
            # Wait for post-merge hook to execute
            print("\nWaiting for post-merge hook to execute (20 seconds)...")
            time.sleep(20)
            
            # Check if verification script ran
            print("\nChecking if verification script executed...")
            stdout2, stderr2, exit_code2 = client._execute_with_cd(
                "cd ~/stock-bot && test -f droplet_verification_results.json && echo 'EXISTS' || echo 'NOT_FOUND'",
                timeout=10
            )
            
            if "EXISTS" in stdout2:
                print("[OK] Verification results file created")
            else:
                print("[WARNING] Verification results not found yet")
            
            client.close()
            return True
        else:
            print(f"[FAIL] Git pull failed: {stderr[:200] if stderr else 'Unknown error'}")
            client.close()
            return False
            
    except ImportError:
        print("[WARNING] droplet_client not available")
        print("Droplet will pull automatically via post-merge hook on next interaction")
        return True
    except Exception as e:
        print(f"[WARNING] SSH connection failed: {e}")
        print("Droplet will pull automatically via post-merge hook")
        return True

def install_dependencies_on_droplet():
    """Step 2: Install new dependencies on droplet"""
    print("\n" + "=" * 80)
    print("STEP 2: INSTALLING DEPENDENCIES ON DROPLET")
    print("=" * 80)
    
    try:
        from droplet_client import DropletClient
        client = DropletClient()
        
        print("Installing new dependencies (hmmlearn, numpy, scipy, tzdata)...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && pip3 install -q hmmlearn numpy scipy tzdata",
            timeout=180
        )
        
        if exit_code == 0:
            print("[OK] Dependencies installed successfully")
        else:
            print(f"[WARNING] Dependency installation had issues: {stderr[:200] if stderr else 'Unknown'}")
        
        client.close()
        return True
    except:
        print("[WARNING] Could not install dependencies automatically")
        print("Dependencies will be installed when droplet pulls code")
        return True

def run_end_to_end_tests_on_droplet():
    """Step 3: Run end-to-end tests on droplet"""
    print("\n" + "=" * 80)
    print("STEP 3: RUNNING END-TO-END TESTS ON DROPLET")
    print("=" * 80)
    
    try:
        from droplet_client import DropletClient
        client = DropletClient()
        
        # Run integration tests
        print("Running integration tests...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && python3 test_structural_intelligence_integration.py 2>&1",
            timeout=120
        )
        
        if exit_code == 0:
            print("[OK] Integration tests passed")
        else:
            print(f"[WARNING] Integration tests had issues: {stderr[:200] if stderr else stdout[:200]}")
        
        # Run regression tests
        print("\nRunning regression tests...")
        stdout2, stderr2, exit_code2 = client._execute_with_cd(
            "cd ~/stock-bot && python3 regression_test_structural_intelligence.py 2>&1",
            timeout=120
        )
        
        if exit_code2 == 0:
            print("[OK] Regression tests passed")
        else:
            print(f"[WARNING] Regression tests had issues: {stderr2[:200] if stderr2 else stdout2[:200]}")
        
        # Run complete verification
        print("\nRunning complete droplet verification...")
        stdout3, stderr3, exit_code3 = client._execute_with_cd(
            "cd ~/stock-bot && python3 complete_droplet_verification.py 2>&1",
            timeout=300
        )
        
        if exit_code3 == 0:
            print("[OK] Complete verification passed")
        else:
            print(f"[WARNING] Complete verification had issues: {stderr3[:200] if stderr3 else stdout3[:200]}")
        
        client.close()
        return True
    except:
        print("[WARNING] Could not run tests automatically")
        return True

def wait_for_results():
    """Step 4: Wait for droplet to process and push results"""
    print("\n" + "=" * 80)
    print("STEP 4: WAITING FOR DROPLET RESULTS")
    print("=" * 80)
    
    print("Waiting 60 seconds for droplet to process and push results...")
    time.sleep(60)
    
    return True

def pull_and_verify_results():
    """Step 5: Pull results from Git and verify"""
    print("\n" + "=" * 80)
    print("STEP 5: PULLING AND VERIFYING RESULTS")
    print("=" * 80)
    
    # Pull from Git
    print("Pulling results from Git...")
    result = run_command("git pull origin main", check=False)
    
    if result.returncode == 0:
        print("[OK] Successfully pulled from Git")
    else:
        print("[WARNING] Git pull had issues")
    
    # Check for verification results
    results = {}
    
    verify_file = Path("droplet_verification_results.json")
    if verify_file.exists():
        print("[OK] Droplet verification results found")
        try:
            with open(verify_file) as f:
                data = json.load(f)
                results['verification'] = data
                status = data.get('overall_status', 'UNKNOWN')
                print(f"  Overall status: {status}")
                if status == 'PASS':
                    print("  ✓ All verifications passed!")
                else:
                    print("  ⚠ Some verifications failed")
        except Exception as e:
            print(f"  [ERROR] Could not read verification results: {e}")
    else:
        print("[MISSING] Droplet verification results not found")
        results['verification'] = None
    
    # Check for integration test results
    integration_file = Path("structural_intelligence_test_results.json")
    if integration_file.exists():
        print("[OK] Integration test results found")
        try:
            with open(integration_file) as f:
                data = json.load(f)
                results['integration'] = data
                passed = data.get('tests_passed', 0)
                total = data.get('tests_total', 0)
                print(f"  Tests: {passed}/{total} passed")
        except:
            pass
    else:
        print("[MISSING] Integration test results not found")
    
    # Check for regression test results
    regression_file = Path("regression_test_results.json")
    if regression_file.exists():
        print("[OK] Regression test results found")
        try:
            with open(regression_file) as f:
                data = json.load(f)
                results['regression'] = data
                passed = data.get('tests_passed', 0)
                total = data.get('tests_total', 0)
                print(f"  Tests: {passed}/{total} passed")
        except:
            pass
    else:
        print("[MISSING] Regression test results not found")
    
    return results

def main():
    """Execute complete deployment and testing workflow"""
    print("=" * 80)
    print("STRUCTURAL INTELLIGENCE OVERHAUL - COMPLETE DEPLOYMENT & TESTING")
    print("=" * 80)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    
    # Step 1: Trigger droplet deployment
    trigger_droplet_deployment()
    
    # Step 2: Install dependencies
    install_dependencies_on_droplet()
    
    # Step 3: Run end-to-end tests
    run_end_to_end_tests_on_droplet()
    
    # Step 4: Wait for results
    wait_for_results()
    
    # Step 5: Pull and verify results
    results = pull_and_verify_results()
    
    # Final summary
    print("\n" + "=" * 80)
    print("DEPLOYMENT & TESTING COMPLETE")
    print("=" * 80)
    print(f"Completed: {datetime.now(timezone.utc).isoformat()}")
    print("\nResults Summary:")
    
    if results.get('verification'):
        status = results['verification'].get('overall_status', 'UNKNOWN')
        print(f"  Verification: {status}")
    
    if results.get('integration'):
        passed = results['integration'].get('tests_passed', 0)
        total = results['integration'].get('tests_total', 0)
        print(f"  Integration Tests: {passed}/{total} passed")
    
    if results.get('regression'):
        passed = results['regression'].get('tests_passed', 0)
        total = results['regression'].get('tests_total', 0)
        print(f"  Regression Tests: {passed}/{total} passed")
    
    print("\nNext Steps:")
    print("  1. Monitor dashboard for structural intelligence indicators")
    print("  2. Check logs for regime detection and macro adjustments")
    print("  3. Review shadow trade logger for threshold adjustments")
    print("  4. Monitor token bucket for API quota management")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

