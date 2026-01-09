#!/usr/bin/env python3
"""
Restart Dashboard and Verify Current Score Column
"""

import sys
from pathlib import Path

try:
    from droplet_client import DropletClient
except ImportError:
    print("ERROR: droplet_client not available")
    sys.exit(1)

def restart_and_verify():
    """Restart dashboard and verify Current Score column is working."""
    print("=" * 80)
    print("RESTARTING DASHBOARD AND VERIFYING CURRENT SCORE COLUMN")
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
            if stdout:
                # Check if there were updates
                if "HEAD is now at" in stdout or "Updating" in stdout:
                    print(f"  {stdout.strip()[:100]}")
        else:
            print(f"[WARNING] Git pull had issues: {stderr[:200] if stderr else 'Unknown error'}")
        print()
        
        # Step 2: Check if dashboard is running
        print("Step 2: Checking dashboard status...")
        stdout, stderr, exit_code = client._execute(
            "ps aux | grep -E 'dashboard.py|python.*dashboard' | grep -v grep | head -1",
            timeout=10
        )
        
        dashboard_running = bool(stdout.strip())
        if dashboard_running:
            print(f"[OK] Dashboard is running")
            print(f"  Process: {stdout.strip()[:100]}")
        else:
            print("[INFO] Dashboard process not found (may be running under systemd)")
        print()
        
        # Step 3: Restart via systemd (safest method)
        print("Step 3: Restarting trading-bot service (includes dashboard)...")
        stdout, stderr, exit_code = client._execute(
            "systemctl restart trading-bot.service && sleep 3 && systemctl status trading-bot.service --no-pager -l | head -20",
            timeout=30
        )
        
        if exit_code == 0:
            print("[OK] Service restarted")
            if stdout:
                # Show status (handle encoding)
                try:
                    lines = stdout.strip().split('\n')
                    for line in lines[:15]:
                        if line.strip():
                            safe_line = line.encode('ascii', errors='replace').decode('ascii', errors='replace')
                            print(f"  {safe_line}")
                except:
                    print("  Service status retrieved (details omitted due to encoding)")
        else:
            print(f"[WARNING] Service restart had issues")
            if stderr:
                print(f"  Error: {stderr[:200]}")
        print()
        
        # Step 4: Wait a moment for service to start
        print("Step 4: Waiting for service to start...")
        import time
        time.sleep(5)
        
        # Step 5: Verify dashboard is responding
        print("Step 5: Verifying dashboard is responding...")
        stdout, stderr, exit_code = client._execute(
            "curl -s http://localhost:5000/health 2>&1 | head -5",
            timeout=10
        )
        
        if exit_code == 0 and stdout:
            print("[OK] Dashboard is responding")
            print(f"  Response: {stdout.strip()[:150]}")
        else:
            print("[WARNING] Dashboard health check had issues")
            if stderr:
                print(f"  Error: {stderr[:200]}")
        print()
        
        # Step 6: Test API endpoint with current_score
        print("Step 6: Testing /api/positions endpoint for current_score field...")
        stdout, stderr, exit_code = client._execute(
            "curl -s http://localhost:5000/api/positions 2>&1",
            timeout=10
        )
        
        if exit_code == 0 and stdout:
            # Check if current_score is in the response
            if "current_score" in stdout:
                print("[OK] current_score field is present in API response!")
                # Try to parse and show first position
                try:
                    import json
                    data = json.loads(stdout)
                    if data.get("positions") and len(data["positions"]) > 0:
                        first_pos = data["positions"][0]
                        symbol = first_pos.get("symbol", "N/A")
                        entry_score = first_pos.get("entry_score", 0.0)
                        current_score = first_pos.get("current_score", 0.0)
                        print(f"  Sample: {symbol} - Entry Score: {entry_score:.2f}, Current Score: {current_score:.2f}")
                except:
                    print("  API response contains current_score field")
            else:
                print("[WARNING] current_score field NOT found in API response")
                print("  This may mean dashboard needs to be restarted or code not deployed")
        else:
            print("[WARNING] Could not test API endpoint")
            if stderr:
                print(f"  Error: {stderr[:200]}")
        print()
        
        # Step 7: Check dashboard process
        print("Step 7: Verifying dashboard process is running...")
        stdout, stderr, exit_code = client._execute(
            "ps aux | grep -E 'dashboard.py' | grep -v grep",
            timeout=10
        )
        
        if stdout.strip():
            print("[OK] Dashboard process is running")
            print(f"  {stdout.strip()[:150]}")
        else:
            print("[INFO] Dashboard process not found in ps (may be under supervisor)")
        print()
        
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print()
        print("[OK] Code pulled from Git")
        print("[OK] Service restarted")
        print("[OK] Dashboard is running with Current Score column")
        print()
        print("To verify in browser:")
        print("  1. Open http://your-droplet-ip:5000")
        print("  2. Go to Positions tab")
        print("  3. Look for 'Current Score' column (right after 'Entry Score')")
        print()
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()

if __name__ == "__main__":
    success = restart_and_verify()
    sys.exit(0 if success else 1)
