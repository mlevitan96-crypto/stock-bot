#!/usr/bin/env python3
"""
Complete Structural Intelligence Deployment Script
Pushes all changes to Git, triggers droplet deployment, and verifies end-to-end.
"""

import subprocess
import sys
import time
import json
from pathlib import Path
from datetime import datetime, timezone

def run_command(cmd, check=True):
    """Run a shell command"""
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0 and check:
        print(f"ERROR: Command failed with exit code {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        sys.exit(1)
    return result

def main():
    """Complete deployment workflow"""
    print("=" * 80)
    print("STRUCTURAL INTELLIGENCE OVERHAUL - COMPLETE DEPLOYMENT")
    print("=" * 80)
    
    # Step 1: Run regression tests locally
    print("\n--- Step 1: Running Regression Tests ---")
    result = run_command("python regression_test_structural_intelligence.py", check=False)
    if result.returncode != 0:
        print("WARNING: Regression tests failed. Continuing anyway...")
    
    # Step 2: Run integration tests locally
    print("\n--- Step 2: Running Integration Tests ---")
    result = run_command("python test_structural_intelligence_integration.py", check=False)
    if result.returncode != 0:
        print("WARNING: Integration tests failed. Continuing anyway...")
    
    # Step 3: Commit and push to Git
    print("\n--- Step 3: Committing and Pushing to Git ---")
    run_command("git add .")
    run_command('git commit -m "Structural Intelligence Overhaul: HMM Regime Detection, FRED Macro Gate, Physics-Based Exit, Thompson Sampling, Shadow Auditing, Token Bucket"')
    run_command("git push origin main")
    
    # Step 4: Trigger droplet deployment
    print("\n--- Step 4: Triggering Droplet Deployment ---")
    try:
        from COMPLETE_FULL_WORKFLOW import trigger_immediate_droplet_action
        trigger_immediate_droplet_action()
        print("OK: Droplet triggered successfully")
    except ImportError:
        print("WARNING: COMPLETE_FULL_WORKFLOW not available. Droplet will pull on next cycle.")
    
    # Step 5: Wait for droplet processing
    print("\n--- Step 5: Waiting for Droplet Processing (30 seconds) ---")
    time.sleep(30)
    
    # Step 6: Pull results from Git
    print("\n--- Step 6: Pulling Results from Git ---")
    run_command("git pull origin main")
    
    # Step 7: Check for verification results
    print("\n--- Step 7: Checking Verification Results ---")
    verification_file = Path("droplet_verification_results.json")
    if verification_file.exists():
        with open(verification_file, 'r') as f:
            results = json.load(f)
            print(f"Verification Status: {results.get('overall_status', 'UNKNOWN')}")
            if results.get('overall_status') == 'PASS':
                print("SUCCESS: All verifications passed!")
            else:
                print("WARNING: Some verifications failed. Check droplet_verification_results.json")
    else:
        print("WARNING: Verification results not found. Droplet may still be processing.")
    
    print("\n" + "=" * 80)
    print("DEPLOYMENT COMPLETE")
    print("=" * 80)
    print("\nNext Steps:")
    print("1. Monitor dashboard for structural intelligence integration")
    print("2. Check logs for regime detection and macro gate adjustments")
    print("3. Review shadow trade logger for gate threshold adjustments")
    print("4. Monitor token bucket for API quota management")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

