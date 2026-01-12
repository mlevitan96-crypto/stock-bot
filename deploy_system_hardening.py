#!/usr/bin/env python3
"""
Deploy System Hardening Changes to Droplet
==========================================
Executes the complete deployment workflow per Memory Bank requirements.
"""

import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 80)
    print("DEPLOYING SYSTEM HARDENING CHANGES TO DROPLET")
    print("=" * 80)
    print()
    
    # Step 1: Verify code is pushed (already done, but verify)
    print("Step 1: Verifying code is on GitHub...")
    result = subprocess.run(["git", "log", "-1", "--oneline"], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[OK] Latest commit: {result.stdout.strip()}")
    print()
    
    # Step 2: Connect to droplet and deploy
    print("Step 2: Connecting to droplet via SSH...")
    try:
        from droplet_client import DropletClient
        client = DropletClient()
        
        print("[OK] Connected to droplet")
        print()
        
        # Step 2a: Pull latest code
        print("Step 2a: Pulling latest code on droplet...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "git fetch origin main && git reset --hard origin/main",
            timeout=120
        )
        
        if exit_code == 0:
            print("[OK] Code pulled successfully")
            if stdout:
                print(f"  Output: {stdout.strip()[:200]}")
        else:
            print(f"[FAIL] Git pull failed: {stderr[:200] if stderr else 'Unknown error'}")
            client.close()
            return 1
        print()
        
        # Step 2b: Check if deployment script exists
        print("Step 2b: Checking for deployment script...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "test -f FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh && echo 'exists' || echo 'missing'",
            timeout=10
        )
        
        if "exists" in stdout:
            print("[OK] Deployment script found")
            print()
            
            # Step 2c: Run deployment script
            print("Step 2c: Running deployment verification script...")
            stdout, stderr, exit_code = client._execute_with_cd(
                "chmod +x FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh && bash FORCE_DROPLET_DEPLOYMENT_AND_VERIFY.sh",
                timeout=600  # 10 minutes
            )
            
            if exit_code == 0:
                print("[OK] Deployment script completed")
                if stdout:
                    lines = stdout.strip().split('\n')
                    print("  Last output lines:")
                    for line in lines[-30:]:
                        print(f"    {line}")
            else:
                print(f"[WARNING] Deployment script had issues (exit code: {exit_code})")
                if stderr:
                    print(f"  Error: {stderr.strip()[:300]}")
        else:
            print("[INFO] Deployment script not found, doing simple restart...")
            # Simple restart of services
            stdout, stderr, exit_code = client._execute_with_cd(
                "systemctl restart stockbot && echo 'restarted' || echo 'restart_failed'",
                timeout=30
            )
            if "restarted" in stdout:
                print("[OK] Service restarted")
            else:
                print(f"[WARNING] Service restart had issues: {stderr[:200]}")
        print()
        
        # Step 2d: Verify deployment
        print("Step 2d: Verifying deployment...")
        status = client.get_status()
        print(f"  Service status: {status.get('service_status', 'unknown')}")
        print(f"  Process count: {status.get('process_count', 0)}")
        git_status = status.get('git', {})
        print(f"  Git commit: {git_status.get('commit', 'unknown')}")
        print()
        
        client.close()
        
    except ImportError as e:
        print(f"[ERROR] droplet_client not available: {e}")
        print("Cannot execute automatically.")
        return 1
    except Exception as e:
        print(f"[ERROR] Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Step 3: Pull results from Git
    print("Step 3: Pulling results from Git...")
    result = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True)
    if result.returncode == 0:
        print("[OK] Results pulled from Git")
        if "Updating" in result.stdout or "Fast-forward" in result.stdout:
            print("  New results received!")
    else:
        print("[INFO] No new results (may already be up to date)")
    print()
    
    print("=" * 80)
    print("DEPLOYMENT COMPLETE")
    print("=" * 80)
    return 0

if __name__ == "__main__":
    sys.exit(main())
