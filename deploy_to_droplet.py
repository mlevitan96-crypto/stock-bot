#!/usr/bin/env python3
"""
Deploy fixes directly to droplet via SSH.
This script uses droplet_client.py to execute commands on the droplet.
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

def deploy_via_ssh():
    """Deploy fixes via SSH using droplet_client."""
    if not HAS_DROPLET_CLIENT:
        print("\nERROR: Cannot deploy automatically - droplet_config.json not found")
        print("\nTo deploy manually, SSH into droplet and run:")
        print("  cd ~/stock-bot && git pull origin main && bash FINAL_DEPLOYMENT_SCRIPT.sh")
        return False
    
    # Check if config exists
    config_path = Path("droplet_config.json")
    if not config_path.exists():
        print("\nERROR: droplet_config.json not found")
        print("\nTo deploy manually, SSH into droplet and run:")
        print("  cd ~/stock-bot && git pull origin main && bash FINAL_DEPLOYMENT_SCRIPT.sh")
        print("\nOr create droplet_config.json with connection details (see droplet_config.example.json)")
        return False
    
    print("=" * 60)
    print("DEPLOYING FIXES TO DROPLET")
    print("=" * 60)
    print()
    
    try:
        client = DropletClient()
        
        print("Step 1: Connecting to droplet...")
        status = client.get_status()
        print(f"OK: Connected to {status['host']}")
        print(f"  Uptime: {status.get('uptime', 'unknown')}")
        print(f"  Processes: {status.get('process_count', 0)}")
        print()
        
        print("Step 2: Pulling latest fixes from Git...")
        stdout, stderr, exit_code = client._execute_with_cd("git pull origin main")
        if exit_code == 0:
            print("OK: Code pulled successfully")
            if stdout:
                print(f"  {stdout.strip()[:200]}")
        else:
            print(f"WARNING: Git pull had issues (exit code: {exit_code})")
            if stderr:
                print(f"  Error: {stderr.strip()[:200]}")
        print()
        
        print("Step 3: Running deployment script...")
        stdout, stderr, exit_code = client._execute_with_cd("bash FINAL_DEPLOYMENT_SCRIPT.sh", timeout=120)
        if exit_code == 0:
            print("OK: Deployment script completed")
            # Show last few lines
            if stdout:
                lines = stdout.strip().split('\n')
                for line in lines[-10:]:
                    print(f"  {line}")
        else:
            print(f"WARNING: Deployment script had issues (exit code: {exit_code})")
            if stderr:
                print(f"  Error: {stderr.strip()[:200]}")
        print()
        
        print("Step 4: Verifying services...")
        status = client.get_status()
        print(f"  Processes running: {status.get('process_count', 0)}")
        print()
        
        print("Step 5: Checking investigation results...")
        stdout, stderr, exit_code = client._execute_with_cd("test -f investigate_no_trades.json && echo 'EXISTS' || echo 'NOT_FOUND'")
        if "EXISTS" in stdout:
            print("OK: Investigation results file exists")
            # Try to get a summary
            stdout, stderr, exit_code = client._execute_with_cd("head -20 investigate_no_trades.json")
            if stdout:
                print("  Preview:")
                for line in stdout.strip().split('\n')[:5]:
                    print(f"    {line}")
        else:
            print("WARNING: Investigation results not found yet")
        print()
        
        print("=" * 60)
        print("DEPLOYMENT COMPLETE")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Check investigation results: investigate_no_trades.json")
        print("  2. Monitor services: screen -r supervisor")
        print("  3. Check dashboard: http://your-droplet-ip:5000")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"\nERROR: Deployment failed: {e}")
        print("\nTo deploy manually, SSH into droplet and run:")
        print("  cd ~/stock-bot && git pull origin main && bash FINAL_DEPLOYMENT_SCRIPT.sh")
        return False

if __name__ == "__main__":
    success = deploy_via_ssh()
    sys.exit(0 if success else 1)
