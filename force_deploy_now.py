#!/usr/bin/env python3
"""
Force deploy fixes to droplet right now.
Uses droplet_client to execute commands directly.
"""

import sys
from pathlib import Path

try:
    from droplet_client import DropletClient
except ImportError:
    print("ERROR: droplet_client not available. Install paramiko: pip install paramiko")
    print("\nOr deploy manually on droplet:")
    print("  cd ~/stock-bot && rm -f setup_droplet_git.sh && git pull origin main && bash FINAL_DEPLOYMENT_SCRIPT.sh")
    sys.exit(1)

def main():
    config_path = Path("droplet_config.json")
    if not config_path.exists():
        print("ERROR: droplet_config.json not found")
        print("Create it with droplet connection details (see droplet_config.example.json)")
        sys.exit(1)
    
    print("=" * 60)
    print("FORCE DEPLOYING TO DROPLET NOW")
    print("=" * 60)
    print()
    
    try:
        client = DropletClient()
        
        # Step 1: Remove conflicting file
        print("Step 1: Removing conflicting files...")
        stdout, stderr, exit_code = client._execute_with_cd("rm -f setup_droplet_git.sh 2>/dev/null; echo 'OK'")
        print("OK: Conflicting files removed")
        print()
        
        # Step 2: Pull latest
        print("Step 2: Pulling latest fixes...")
        stdout, stderr, exit_code = client._execute_with_cd("git pull origin main", timeout=60)
        if exit_code == 0:
            print("OK: Code pulled successfully")
            if stdout:
                for line in stdout.strip().split('\n')[-5:]:
                    if line.strip():
                        print(f"  {line}")
        else:
            # If pull fails, try reset
            print("WARNING: Pull failed, trying reset...")
            stdout, stderr, exit_code = client._execute_with_cd("git fetch origin main && git reset --hard origin/main", timeout=60)
            if exit_code == 0:
                print("OK: Reset successful")
            else:
                print(f"ERROR: Reset failed: {stderr[:200]}")
                return False
        print()
        
        # Step 3: Run deployment
        print("Step 3: Running deployment script...")
        stdout, stderr, exit_code = client._execute_with_cd("bash FINAL_DEPLOYMENT_SCRIPT.sh", timeout=180)
        if exit_code == 0:
            print("OK: Deployment completed")
            # Show last 15 lines
            if stdout:
                lines = stdout.strip().split('\n')
                for line in lines[-15:]:
                    if line.strip():
                        print(f"  {line}")
        else:
            print(f"WARNING: Deployment had issues (exit code: {exit_code})")
            if stderr:
                print(f"  Error: {stderr[:300]}")
        print()
        
        # Step 4: Check results
        print("Step 4: Checking results...")
        stdout, stderr, exit_code = client._execute_with_cd("test -f investigate_no_trades.json && echo 'EXISTS' || echo 'NOT_FOUND'")
        if "EXISTS" in stdout:
            print("OK: Investigation results file exists")
        else:
            print("WARNING: Investigation results not found")
        print()
        
        print("=" * 60)
        print("DEPLOYMENT COMPLETE")
        print("=" * 60)
        
        client.close()
        return True
        
    except Exception as e:
        print(f"\nERROR: Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

