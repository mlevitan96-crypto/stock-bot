#!/usr/bin/env python3
"""
Complete immediate workflow: Push to Git → Trigger Droplet → Pull Results → Analyze
This is the main entry point for all interactions - executes everything immediately.
"""

import subprocess
import sys
import time
from pathlib import Path

def push_to_git():
    """Push all changes to Git."""
    print("=" * 60)
    print("STEP 1: PUSHING TO GIT")
    print("=" * 60)
    
    # Check for uncommitted changes
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )
    
    if not result.stdout.strip():
        print("✓ No changes to commit")
        return True
    
    # Add all changes
    print("Adding changes...")
    subprocess.run(["git", "add", "."], check=True)
    
    # Commit
    print("Committing changes...")
    result = subprocess.run(
        ["git", "commit", "-m", "Auto-commit: Immediate workflow trigger"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0 and "nothing to commit" not in result.stderr:
        print(f"⚠ Commit warning: {result.stderr}")
    
    # Push
    print("Pushing to GitHub...")
    result = subprocess.run(
        ["git", "push", "origin", "main"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ Successfully pushed to Git")
        return True
    else:
        print(f"✗ Push failed: {result.stderr}")
        return False

def trigger_droplet():
    """Trigger immediate action on droplet."""
    print()
    print("=" * 60)
    print("STEP 2: TRIGGERING IMMEDIATE DROPLET ACTION")
    print("=" * 60)
    
    # Try to use immediate trigger script
    trigger_script = Path("trigger_immediate_droplet_action.py")
    if trigger_script.exists():
        print("Using SSH to trigger immediate pull...")
        result = subprocess.run(
            [sys.executable, str(trigger_script)],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode == 0:
            print("✓ Droplet triggered successfully")
            return True
        else:
            print(f"⚠ SSH trigger failed (will rely on post-merge hook)")
            print("  Droplet will pull automatically on next interaction")
            return False
    else:
        print("⚠ SSH trigger script not available")
        print("  Droplet will pull automatically via post-merge hook")
        return True  # Not a failure - post-merge hook will handle it

def pull_results():
    """Pull results from Git."""
    print()
    print("=" * 60)
    print("STEP 3: PULLING RESULTS FROM GIT")
    print("=" * 60)
    
    # Wait a moment for droplet to process
    print("Waiting for droplet to process (10 seconds)...")
    time.sleep(10)
    
    # Pull
    print("Pulling from Git...")
    result = subprocess.run(
        ["git", "pull", "origin", "main"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ Successfully pulled from Git")
        if "Updating" in result.stdout or "Fast-forward" in result.stdout:
            print("  New results received!")
        else:
            print("  No new results yet (may need to wait longer)")
        return True
    else:
        print(f"⚠ Pull had issues: {result.stderr}")
        return False

def analyze_results():
    """Analyze pulled results."""
    print()
    print("=" * 60)
    print("STEP 4: ANALYZING RESULTS")
    print("=" * 60)
    
    results = {}
    
    # Check for investigation results
    invest_file = Path("investigate_no_trades.json")
    if invest_file.exists():
        print("✓ Investigation results found")
        try:
            import json
            with open(invest_file) as f:
                data = json.load(f)
                results['investigation'] = data
                print(f"  Status: {data.get('summary', {}).get('status', 'unknown')}")
                issues = data.get('summary', {}).get('issues', [])
                if issues:
                    print(f"  Issues: {len(issues)} found")
        except Exception as e:
            print(f"  ⚠ Error reading: {e}")
    else:
        print("  No investigation results yet")
    
    # Check for UW test results
    uw_file = Path("uw_endpoint_test_results.json")
    if uw_file.exists():
        print("✓ UW endpoint test results found")
        try:
            import json
            with open(uw_file) as f:
                data = json.load(f)
                results['uw_test'] = data
                print(f"  Endpoints tested: {len(data.get('endpoints', {}))}")
        except Exception as e:
            print(f"  ⚠ Error reading: {e}")
    else:
        print("  No UW test results yet")
    
    # Check for status report
    status_file = Path("status_report.json")
    if status_file.exists():
        print("✓ Status report found")
        try:
            import json
            with open(status_file) as f:
                data = json.load(f)
                results['status'] = data
                print(f"  Services: {data.get('services', {})}")
        except Exception as e:
            print(f"  ⚠ Error reading: {e}")
    else:
        print("  No status report yet")
    
    return results

def main():
    """Execute complete immediate workflow."""
    print()
    print("🚀 IMMEDIATE DROPLET WORKFLOW")
    print("=" * 60)
    print()
    
    # Step 1: Push to Git
    if not push_to_git():
        print("\n✗ Failed to push to Git - aborting")
        return False
    
    # Step 2: Trigger droplet
    trigger_droplet()
    
    # Step 3: Pull results
    if not pull_results():
        print("\n⚠ Could not pull results - may need to wait longer")
    
    # Step 4: Analyze
    results = analyze_results()
    
    print()
    print("=" * 60)
    print("WORKFLOW COMPLETE")
    print("=" * 60)
    print()
    print("Summary:")
    print(f"  - Investigation results: {'✓' if 'investigation' in results else '✗'}")
    print(f"  - UW test results: {'✓' if 'uw_test' in results else '✗'}")
    print(f"  - Status report: {'✓' if 'status' in results else '✗'}")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

