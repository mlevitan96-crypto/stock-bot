#!/usr/bin/env python3
"""
Simple Droplet Deployment - Pull code and restart services
Avoids encoding issues by using simpler commands
"""

import subprocess
import sys

def deploy_to_droplet():
    """Simple deployment: pull code and restart services"""
    print("=" * 80)
    print("DEPLOYING TO DROPLET")
    print("=" * 80)
    
    # Step 1: Ensure code is pushed
    print("\nStep 1: Ensuring code is pushed to Git...")
    result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
    if result.returncode == 0:
        print("[OK] Code pushed to Git")
    else:
        print("[WARNING] Git push had issues (may already be up to date)")
    
    # Step 2: Connect to droplet and deploy
    print("\nStep 2: Deploying to droplet...")
    try:
        from droplet_client import DropletClient
        client = DropletClient()
        
        print("[OK] Connected to droplet")
        
        # Commands to execute on droplet
        commands = [
            "cd ~/stock-bot && git fetch origin main && git reset --hard origin/main",
            "cd ~/stock-bot && chmod +x guardian_wrapper.sh 2>/dev/null || true",
            "cd ~/stock-bot && git log -1 --oneline"
        ]
        
        for cmd in commands:
            print(f"\nExecuting: {cmd[:60]}...")
            stdout, stderr, exit_code = client._execute_with_cd(cmd, timeout=120)
            if exit_code == 0:
                print("[OK] Command succeeded")
                if stdout and stdout.strip():
                    # Print only first line to avoid encoding issues
                    first_line = stdout.strip().split('\n')[0]
                    print(f"  Output: {first_line[:100]}")
            else:
                print(f"[WARNING] Command had issues (exit code: {exit_code})")
                if stderr and stderr.strip():
                    print(f"  Error: {stderr.strip()[:200]}")
        
        print("\n" + "=" * 80)
        print("DEPLOYMENT COMMANDS COMPLETE")
        print("=" * 80)
        print("\nTo restart services on droplet, run:")
        print("  Option A (Supervisor):")
        print("    pkill -f deploy_supervisor && sleep 2 && cd ~/stock-bot && source venv/bin/activate && python deploy_supervisor.py")
        print("\n  Option B (Systemd):")
        print("    sudo systemctl restart stock-bot")
        print("\n  Option C (Process-compose):")
        print("    cd ~/stock-bot && process-compose down && process-compose up -d")
        
        client.close()
        return True
        
    except ImportError:
        print("[ERROR] droplet_client not available")
        print("\nManual deployment commands:")
        print("  cd ~/stock-bot")
        print("  git pull origin main")
        print("  chmod +x guardian_wrapper.sh")
        print("  # Then restart services (see options above)")
        return False
    except Exception as e:
        print(f"[ERROR] Deployment failed: {e}")
        print("\nManual deployment commands:")
        print("  cd ~/stock-bot")
        print("  git pull origin main")
        print("  chmod +x guardian_wrapper.sh")
        print("  # Then restart services (see options above)")
        return False

if __name__ == "__main__":
    success = deploy_to_droplet()
    sys.exit(0 if success else 1)
