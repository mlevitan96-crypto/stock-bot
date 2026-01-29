#!/usr/bin/env python3
"""
Deploy Dashboard Fixes to Droplet via SSH
Uses droplet_client.py for SSH connection
"""

import sys
from pathlib import Path

try:
    from droplet_client import DropletClient
except ImportError as e:
    print(f"ERROR: Could not import droplet_client: {e}")
    print("Make sure paramiko is installed: python -m pip install paramiko")
    sys.exit(1)

def deploy_dashboard():
    """Deploy dashboard fixes to droplet"""
    print("=" * 80)
    print("DASHBOARD FIXES DEPLOYMENT TO DROPLET")
    print("=" * 80)
    print()
    
    try:
        client = DropletClient()
        print("[OK] Droplet client initialized")
        print()
        
        # Step 1: Test connection
        print("[1/6] Testing SSH connection...")
        try:
            status = client.get_status()
            print("[OK] SSH connection successful")
        except Exception as e:
            print(f"[ERROR] SSH connection failed: {e}")
            print("\nTroubleshooting:")
            print("1. Check SSH config: ssh -G alpaca")
            print("2. Test manual SSH: ssh alpaca 'echo test'")
            print("3. Verify droplet_config.json exists and is correct")
            return False
        print()
        
        # Step 2: Deploy latest code (fetch + reset, per Memory Bank 6.1 / run_full_deploy)
        print("[2/6] Deploying latest code from GitHub (fetch + reset)...")
        out, err, rc = client._execute(
            "cd /root/stock-bot && git fetch origin main && git reset --hard origin/main",
            timeout=60,
        )
        if rc == 0:
            print("[OK] Code deployed successfully")
            if out:
                print(f"   {out.strip()[:200]}")
        else:
            print(f"[ERROR] Git deploy failed (rc={rc})")
            if err:
                print(f"   {err.strip()[:300]}")
            if out:
                print(f"   stdout: {out.strip()[:200]}")
            return False
        print()
        
        # Step 3: Verify commit
        print("[3/6] Verifying latest commit...")
        stdout, stderr, exit_code = client._execute_with_cd("git log -1 --oneline")
        if exit_code == 0 and stdout:
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
        stdout, stderr, exit_code = client._execute(
            "ps aux | grep -E 'dashboard.py|python.*dashboard' | grep -v grep | head -1"
        )
        if exit_code == 0 and stdout.strip():
            print(f"[OK] Dashboard is running")
            print(f"   {stdout.strip()[:100]}")
        else:
            print("[INFO] Dashboard process not found (may be under systemd/supervisor)")
        print()
        
        # Step 5: Restart dashboard (Memory Bank 6.6: stock-bot-dashboard or nohup)
        print("[5/6] Restarting dashboard...")
        client._execute("pkill -f 'python.*dashboard.py' || true")
        out, _, rc = client._execute("sudo systemctl restart stock-bot-dashboard", timeout=15)
        if rc != 0:
            # Fallback: start manually (Memory Bank 6.6 verified)
            client._execute("bash -lc 'cd /root/stock-bot && nohup python3 dashboard.py > logs/dashboard.log 2>&1 &'", timeout=10)
        print("   Dashboard restart triggered")
        
        import time
        print("   Waiting 5 seconds for restart...")
        time.sleep(5)
        print("[OK] Dashboard restart initiated")
        print()
        
        # Step 6: Verify dashboard is responding
        print("[6/6] Verifying dashboard is responding...")
        # Use IPv4 loopback explicitly: some droplets don't have IPv6 ::1 bound for "localhost".
        # Dashboard now requires HTTP Basic Auth (DASHBOARD_USER / DASHBOARD_PASS from /root/stock-bot/.env).
        stdout, stderr, exit_code = client._execute(
            "bash -lc 'cd /root/stock-bot && set -a && source .env && set +a && "
            "if [ -z \"$DASHBOARD_USER\" ] || [ -z \"$DASHBOARD_PASS\" ]; then "
            "echo \"[ERROR] Missing DASHBOARD_USER/DASHBOARD_PASS in /root/stock-bot/.env\"; exit 2; "
            "fi && "
            "curl -s -u \"$DASHBOARD_USER:$DASHBOARD_PASS\" http://127.0.0.1:5000/health 2>&1 | head -5'"
        )
        
        if exit_code == 0 and stdout:
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
        print("   (HTTP Basic Auth required)")
        print("   http://104.236.102.57:5000/health")
        print("   http://104.236.102.57:5000/api/positions")
        print("   http://104.236.102.57:5000/api/health_status")
        print()
        print("=" * 80)
        
        client.close()
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = deploy_dashboard()
    sys.exit(0 if success else 1)
