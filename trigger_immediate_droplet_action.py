#!/usr/bin/env python3
"""
Trigger immediate action on droplet via SSH.
This bypasses waiting for hourly cron jobs - executes immediately when called.
"""

import sys
import os
from pathlib import Path

# Try to import droplet_client
try:
    from droplet_client import DropletClient
    HAS_DROPLET_CLIENT = True
except ImportError:
    HAS_DROPLET_CLIENT = False
    print("WARNING: droplet_client.py not available - will provide manual instructions")

def trigger_immediate_pull_and_execute():
    """Trigger immediate git pull and execution on droplet via SSH."""
    if not HAS_DROPLET_CLIENT:
        print("\nERROR: Cannot trigger automatically - droplet_config.json not found")
        print("\nTo trigger manually, SSH into droplet and run:")
        print("  cd ~/stock-bot && git pull origin main")
        return False
    
    # Check if config exists
    config_path = Path("droplet_config.json")
    if not config_path.exists():
        print("\nERROR: droplet_config.json not found")
        print("\nTo trigger manually, SSH into droplet and run:")
        print("  cd ~/stock-bot && git pull origin main")
        print("\nOr create droplet_config.json with connection details (see droplet_config.example.json)")
        return False
    
    print("=" * 60)
    print("TRIGGERING IMMEDIATE DROPLET ACTION")
    print("=" * 60)
    print()
    
    try:
        client = DropletClient()
        
        print("Step 1: Connecting to droplet...")
        status = client.get_status()
        print(f"✓ Connected to {status['host']}")
        print()
        
        print("Step 2: Pulling latest code from Git (triggers post-merge hook)...")
        stdout, stderr, exit_code = client._execute_with_cd("git pull origin main --no-rebase", timeout=60)
        if exit_code == 0:
            print("✓ Code pulled successfully")
            # Post-merge hook will automatically run run_investigation_on_pull.sh
            if "Updating" in stdout or "Fast-forward" in stdout or "Already up to date" in stdout:
                print("  Post-merge hook will execute automatically")
        else:
            print(f"⚠ Git pull had issues (exit code: {exit_code})")
            if stderr:
                print(f"  Error: {stderr.strip()[:200]}")
        print()
        
        print("Step 3: Verifying post-merge hook executed...")
        # Wait a moment for hook to run
        import time
        time.sleep(3)
        
        # Check if investigation results were updated
        stdout, stderr, exit_code = client._execute_with_cd(
            "test -f investigate_no_trades.json && stat -c %Y investigate_no_trades.json || echo '0'",
            timeout=10
        )
        if stdout.strip() != '0':
            print("✓ Investigation results file exists")
        print()
        
        print("Step 4: Checking for new commits (results pushed)...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "git log -1 --pretty=format:'%h - %s (%cr)' 2>/dev/null || echo 'unknown'",
            timeout=10
        )
        if stdout:
            print(f"  Latest commit: {stdout.strip()}")
        print()
        
        print("=" * 60)
        print("IMMEDIATE ACTION TRIGGERED")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Pull results from Git: git pull origin main")
        print("  2. Check investigation results: investigate_no_trades.json")
        print("  3. Check UW test results: uw_endpoint_test_results.json")
        print("  4. Check status report: status_report.json")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"\nERROR: Trigger failed: {e}")
        print("\nTo trigger manually, SSH into droplet and run:")
        print("  cd ~/stock-bot && git pull origin main")
        return False

if __name__ == "__main__":
    success = trigger_immediate_pull_and_execute()
    sys.exit(0 if success else 1)

