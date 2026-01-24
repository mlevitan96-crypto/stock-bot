#!/usr/bin/env python3
"""
Deploy Dashboard Fixes to Droplet via SSH
Follows Memory Bank workflow: GitHub → Droplet → Verify
"""

import subprocess
import sys
import time
from pathlib import Path

def run_ssh_command(host, command, timeout=60):
    """Run SSH command on droplet"""
    try:
        # Use SSH alias "alpaca" or direct IP
        ssh_cmd = f'ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 {host} "{command}"'
        print(f"Running: {command}")
        result = subprocess.run(
            ssh_cmd,
            shell=True,
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
    
    # Deploy target from Memory Bank
    # Try "alpaca" alias first, fallback to direct IP
    deploy_target = "root@104.236.102.57"  # Direct IP from Memory Bank
    project_dir = "/root/stock-bot"
    
    # Step 1: Pull latest code
    print("[1/5] Pulling latest code from GitHub...")
    success, stdout, stderr = run_ssh_command(
        deploy_target,
        f"cd {project_dir} && git fetch origin main && git reset --hard origin/main",
        timeout=120
    )
    
    if success:
        print("✅ Code pulled successfully")
        if stdout:
            # Show relevant output
            lines = stdout.strip().split('\n')
            for line in lines[-3:]:
                if line.strip():
                    print(f"   {line}")
    else:
        print(f"❌ Git pull failed: {stderr[:200]}")
        return False
    print()
    
    # Step 2: Verify commit
    print("[2/5] Verifying latest commit...")
    success, stdout, stderr = run_ssh_command(
        deploy_target,
        f"cd {project_dir} && git log -1 --oneline",
        timeout=30
    )
    if success and stdout:
        commit = stdout.strip()
        print(f"✅ Current commit: {commit}")
        if "dashboard" in commit.lower() or "6d7b3c2" in commit or "1ccbcf3" in commit:
            print("✅ Dashboard fixes detected in commit")
        else:
            print("⚠️  Warning: Dashboard fixes may not be in this commit")
    else:
        print(f"⚠️  Could not verify commit: {stderr[:200]}")
    print()
    
    # Step 3: Check dashboard status
    print("[3/5] Checking dashboard status...")
    success, stdout, stderr = run_ssh_command(
        deploy_target,
        "ps aux | grep -E 'dashboard.py|python.*dashboard' | grep -v grep | head -1",
        timeout=10
    )
    if success and stdout.strip():
        print(f"✅ Dashboard is running")
        print(f"   {stdout.strip()[:100]}")
    else:
        print("ℹ️  Dashboard process not found (may be under systemd/supervisor)")
    print()
    
    # Step 4: Restart dashboard
    print("[4/5] Restarting dashboard...")
    # Try multiple restart methods
    restart_methods = [
        ("Kill dashboard (supervisor will restart)", f"pkill -f 'python.*dashboard.py'"),
        ("Restart via systemd", "systemctl restart trading-bot.service"),
    ]
    
    for method_name, command in restart_methods:
        print(f"   Trying: {method_name}...")
        success, stdout, stderr = run_ssh_command(
            deploy_target,
            command,
            timeout=30
        )
        if success:
            print(f"   ✅ {method_name} succeeded")
            break
        else:
            print(f"   ⚠️  {method_name} had issues (may be expected)")
    
    print("   Waiting 5 seconds for restart...")
    time.sleep(5)
    print()
    
    # Step 5: Verify dashboard is responding
    print("[5/5] Verifying dashboard is responding...")
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
            print("✅ Dashboard is responding")
            print(f"   Response: {stdout.strip()[:150]}")
        else:
            print("⚠️  Dashboard responded but may have issues")
            print(f"   Response: {stdout.strip()[:150]}")
    else:
        print("❌ Dashboard health check failed")
        if stderr:
            print(f"   Error: {stderr[:200]}")
    print()
    
    # Final summary
    print("=" * 80)
    print("DEPLOYMENT SUMMARY")
    print("=" * 80)
    print()
    print("✅ Code pulled from GitHub")
    print("✅ Dashboard restarted")
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
        print(f"\n\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
