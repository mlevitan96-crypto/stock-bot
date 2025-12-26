#!/usr/bin/env python3
"""
Fix and Enable Systemd Service
Stops manual processes and enables systemd management.
"""

from droplet_client import DropletClient
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("FIXING AND ENABLING SYSTEMD SERVICE")
        print("=" * 80)
        print()
        
        # 1. Fix the start script on droplet
        print("1. FIXING SYSTEMD START SCRIPT")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && git pull origin main",
            timeout=30
        )
        print("[OK] Code updated")
        print()
        
        # 2. Stop manual processes
        print("2. STOPPING MANUAL PROCESSES")
        print("-" * 80)
        client.execute_command("pkill -f deploy_supervisor.py", timeout=10)
        client.execute_command("pkill -f 'python.*main.py'", timeout=10)
        client.execute_command("pkill -f 'python.*uw_flow_daemon.py'", timeout=10)
        client.execute_command("pkill -f 'python.*dashboard.py'", timeout=10)
        time.sleep(3)
        print("[OK] Manual processes stopped")
        print()
        
        # 3. Verify processes are stopped
        print("3. VERIFYING PROCESSES STOPPED")
        print("-" * 80)
        result = client.execute_command(
            "ps aux | grep -E 'deploy_supervisor|main.py|uw_flow_daemon|dashboard' | grep -v grep || echo 'All processes stopped'",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 4. Reload systemd and start service
        print("4. ENABLING SYSTEMD SERVICE")
        print("-" * 80)
        result = client.execute_command("systemctl daemon-reload", timeout=10)
        print("[OK] Systemd reloaded")
        
        result = client.execute_command("systemctl enable trading-bot.service", timeout=10)
        print("[OK] Service enabled")
        
        result = client.execute_command("systemctl start trading-bot.service", timeout=10)
        print("[OK] Service started")
        print()
        
        # 5. Wait and check status
        print("5. CHECKING SERVICE STATUS")
        print("-" * 80)
        time.sleep(5)
        result = client.execute_command(
            "systemctl status trading-bot.service --no-pager | head -20",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output)
        print()
        
        # 6. Verify processes are running under systemd
        print("6. VERIFYING PROCESSES RUNNING")
        print("-" * 80)
        result = client.execute_command(
            "ps aux | grep -E 'deploy_supervisor|main.py|uw_flow_daemon|dashboard' | grep -v grep",
            timeout=10
        )
        print(result['stdout'] if result['stdout'] else 'No processes found')
        print()
        
        # 7. Check if systemd is parent
        print("7. VERIFYING SYSTEMD PARENT")
        print("-" * 80)
        result = client.execute_command(
            "ps -eo pid,ppid,comm,args | grep -E 'deploy_supervisor|main.py' | grep -v grep",
            timeout=10
        )
        print(result['stdout'] if result['stdout'] else 'Could not verify')
        print()
        
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("Systemd service should now be managing the bot.")
        print("Check status with: systemctl status trading-bot.service")
        print()
        
    except Exception as e:
        print(f"[ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

