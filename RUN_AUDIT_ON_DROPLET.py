#!/usr/bin/env python3
"""
Run Trading Workflow Audit on Droplet
"""

import sys
from pathlib import Path

try:
    from droplet_client import DropletClient
except ImportError:
    print("ERROR: droplet_client not available")
    sys.exit(1)

def run_audit_on_droplet():
    """Run the audit script on the droplet."""
    print("=" * 80)
    print("RUNNING TRADING WORKFLOW AUDIT ON DROPLET")
    print("=" * 80)
    print()
    
    client = DropletClient()
    
    try:
        # Step 1: Pull latest code
        print("Step 1: Pulling latest code on droplet...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && git fetch origin main && git reset --hard origin/main",
            timeout=120
        )
        
        if exit_code == 0:
            print("[OK] Code pulled successfully")
        else:
            print(f"[WARNING] Git pull had issues: {stderr[:200] if stderr else 'Unknown error'}")
        print()
        
        # Step 2: Run the audit script (try with venv first, fallback to system python)
        print("Step 2: Running trading workflow audit...")
        # Try with venv first
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && (source venv/bin/activate 2>/dev/null && python3 FULL_TRADING_WORKFLOW_AUDIT.py || python3 FULL_TRADING_WORKFLOW_AUDIT.py)",
            timeout=300  # 5 minutes
        )
        
        print()
        print("=" * 80)
        print("AUDIT RESULTS")
        print("=" * 80)
        print()
        
        if stdout:
            try:
                # Try to print with UTF-8 encoding, fallback to ASCII if needed
                print(stdout.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))
            except:
                # If that fails, replace problematic characters
                print(stdout.encode('ascii', errors='replace').decode('ascii', errors='replace'))
        if stderr:
            try:
                print("STDERR:", stderr.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))
            except:
                print("STDERR:", stderr.encode('ascii', errors='replace').decode('ascii', errors='replace'))
        
        print()
        print("=" * 80)
        
        return exit_code == 0
        
    except Exception as e:
        print(f"[ERROR] Failed to run audit: {e}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    success = run_audit_on_droplet()
    sys.exit(0 if success else 1)
