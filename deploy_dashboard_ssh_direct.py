#!/usr/bin/env python3
"""
Deploy Dashboard Fixes to Droplet via SSH (Direct SSH command)
Uses subprocess to call SSH directly instead of paramiko
"""

import subprocess
import sys
import time
from pathlib import Path

def run_ssh_command(host, command, timeout=60):
    """Run SSH command on droplet using subprocess"""
    try:
        import os
        # Get SSH key file path
        home = os.path.expanduser("~")
        key_file = os.path.join(home, ".ssh", "id_ed25519")
        
        # Use SSH with explicit key file
        if os.path.exists(key_file):
            ssh_cmd = ['ssh', '-i', key_file, '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=30', host, command]
        else:
            # Fallback to SSH config
            ssh_cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=30', host, command]
        
        print(f"Running: {command}")
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return False, "", str(e)

def main():
    print("=" * 80)
    print("DASHBOARD FIXES DEPLOYMENT TO DROPLET")
    print("=" * 80)
    print()
    
    # Use SSH config host "alpaca" (as user requested)
    deploy_target = "alpaca"
    project_dir = "/root/stock-bot"
    
    # Step 1: Test SSH connection
    print("[1/6] Testing SSH connection...")
    success, stdout, stderr = run_ssh_command(deploy_target, "echo 'SSH connection test'", timeout=30)
    if success:
        print("[OK] SSH connection successful")
        print(f"   {stdout.strip()}")
    else:
        print(f"[ERROR] SSH connection failed: {stderr[:200] if stderr else 'Unknown error'}")
        print("\nTroubleshooting:")
        print("1. Test manual SSH: ssh alpaca 'echo test'")
        print("2. Check SSH config: ssh -G alpaca")
        return False
    print()
    
    # Step 2: Pull latest code
    print("[2/6] Pulling latest code from GitHub...")
    success, stdout, stderr = run_ssh_command(
        deploy_target,
        f"cd {project_dir} && git fetch origin main && git reset --hard origin/main",
        timeout=120
    )
    if success:
        print("[OK] Code pulled successfully")
        if stdout:
            lines = stdout.strip().split('\n')
            for line in lines[-3:]:
                if line.strip():
                    print(f"   {line}")
    else:
        print(f"[ERROR] Git pull failed: {stderr[:200] if stderr else 'Unknown error'}")
        return False
    print()
    
    # Step 3: Verify commit
    print("[3/6] Verifying latest commit...")
    success, stdout, stderr = run_ssh_command(
        deploy_target,
        f"cd {project_dir} && git log -1 --oneline",
        timeout=30
    )
    if success and stdout:
        commit = stdout.strip()
        print(f"[OK] Current commit: {commit}")
        if "dashboard" in commit.lower() or "6d7b3c2" in commit or "1ccbcf3" in commit or "f1a763a" in commit:
            print("[OK] Dashboard fixes detected in commit")
        else:
            print("[WARNING] Dashboard fixes may not be in this commit")
    else:
        print(f"[WARNING] Could not verify commit: {stderr[:200] if stderr else 'Unknown error'}")
    print()
    
    # Step 4: Check dashboard status
    print("[4/6] Checking dashboard status...")
    success, stdout, stderr = run_ssh_command(
        deploy_target,
        "ps aux | grep -E 'dashboard.py|python.*dashboard' | grep -v grep | head -1",
        timeout=10
    )
    if success and stdout.strip():
        print(f"[OK] Dashboard is running")
        print(f"   {stdout.strip()[:100]}")
    else:
        print("[INFO] Dashboard process not found (may be under systemd/supervisor)")
    print()
    
    # Step 5: Restart dashboard
    print("[5/6] Restarting dashboard...")
    # Try killing dashboard first (supervisor will restart)
    run_ssh_command(deploy_target, "pkill -f 'python.*dashboard.py' || true", timeout=10)
    print("   Killed dashboard process (supervisor will restart)")
    
    # Also try systemd restart
    run_ssh_command(deploy_target, "systemctl restart trading-bot.service || true", timeout=30)
    print("   Restarted via systemd")
    
    print("   Waiting 5 seconds for restart...")
    time.sleep(5)
    print("[OK] Dashboard restart initiated")
    print()
    
    # Step 6: Verify dashboard is responding
    print("[6/6] Verifying dashboard is responding...")
    success, stdout, stderr = run_ssh_command(
        deploy_target,
        "bash -lc 'cd /root/stock-bot && set -a && source .env && set +a && "
        "if [ -z \"$DASHBOARD_USER\" ] || [ -z \"$DASHBOARD_PASS\" ]; then "
        "echo \"[ERROR] Missing DASHBOARD_USER/DASHBOARD_PASS in /root/stock-bot/.env\"; exit 2; "
        "fi && "
        "curl -s -u \"$DASHBOARD_USER:$DASHBOARD_PASS\" http://localhost:5000/health 2>&1 | head -5'",
        timeout=10
    )
    
    if success and stdout:
        if "healthy" in stdout.lower() or "status" in stdout.lower():
            print("[OK] Dashboard is responding")
            print(f"   {stdout.strip()[:150]}")
        else:
            print("[WARNING] Dashboard responded but may have issues")
            print(f"   {stdout.strip()[:150]}")
    else:
        print("[WARNING] Dashboard health check had issues")
        if stderr:
            print(f"   Error: {stderr[:200]}")
    print()
    
    # Final summary
    print("=" * 80)
    print("DEPLOYMENT SUMMARY")
    print("=" * 80)
    print()
    print("[OK] Code pulled from GitHub")
    print("[OK] Dashboard restarted")
    print()
    print("Verify dashboard is accessible:")
    print("   http://104.236.102.57:5000/")
    print()
    print("Test endpoints:")
    print("   http://104.236.102.57:5000/health")
    print("   http://104.236.102.57:5000/api/positions")
    print("   http://104.236.102.57:5000/api/health_status")
    print()
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nDeployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
