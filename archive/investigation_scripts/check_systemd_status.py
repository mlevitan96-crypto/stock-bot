#!/usr/bin/env python3
"""Check if bot is running under systemd."""

from droplet_client import DropletClient

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("CHECKING SYSTEMD STATUS")
        print("=" * 80)
        print()
        
        # 1. Check for systemd service files
        print("1. SYSTEMD SERVICE FILES")
        print("-" * 80)
        result = client.execute_command(
            "ls -la /etc/systemd/system/*.service 2>&1 | grep -E 'stock|bot|trading|uw' || echo 'No matching service files found'",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 2. Check running systemd services
        print("2. RUNNING SYSTEMD SERVICES")
        print("-" * 80)
        result = client.execute_command(
            "systemctl list-units --type=service --state=running 2>&1 | grep -E 'stock|bot|trading|uw' || echo 'No matching running services'",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 3. Check specific service status
        print("3. SPECIFIC SERVICE STATUS")
        print("-" * 80)
        services = ['stock-bot', 'trading-bot', 'uw-daemon', 'stock-bot.service', 'trading-bot.service']
        for service in services:
            result = client.execute_command(f"systemctl status {service} 2>&1 | head -10 || echo 'Service {service} not found'", timeout=10)
            if 'not found' not in result['stdout'] and 'could not be found' not in result['stdout']:
                print(f"{service}:")
                output = result['stdout'][:500].encode('ascii', 'ignore').decode('ascii')
                print(output)
                print()
        
        # 4. Check how processes are actually running
        print("4. ACTUAL PROCESS STATUS")
        print("-" * 80)
        result = client.execute_command(
            "ps aux | grep -E 'main.py|uw_flow_daemon|dashboard|deploy_supervisor' | grep -v grep",
            timeout=10
        )
        print("Running processes:")
        print(result['stdout'] if result['stdout'] else 'No processes found')
        print()
        
        # 5. Check if processes are children of systemd
        print("5. PROCESS PARENT CHECK")
        print("-" * 80)
        result = client.execute_command(
            "ps -eo pid,ppid,comm,args | grep -E 'main.py|uw_flow_daemon|dashboard' | grep -v grep",
            timeout=10
        )
        print(result['stdout'] if result['stdout'] else 'No processes found')
        print()
        # Check if systemd is parent (PID 1)
        result2 = client.execute_command(
            "ps -eo pid,ppid,comm | grep -E 'main.py|uw_flow_daemon' | grep -v grep | awk '{print $2}' | xargs -I {} ps -p {} -o comm= 2>/dev/null | head -5",
            timeout=10
        )
        print("Parent processes:")
        print(result2['stdout'] if result2['stdout'] else 'Could not determine parent')
        print()
        
        # 6. Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("If systemd services are found and running, bot is managed by systemd.")
        print("If processes are running but no systemd services, bot is running manually.")
        print()
        
    except Exception as e:
        print(f"[ERROR] Check failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

