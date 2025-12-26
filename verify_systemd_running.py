#!/usr/bin/env python3
"""Verify systemd service is running correctly."""

from droplet_client import DropletClient

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("VERIFYING SYSTEMD SERVICE STATUS")
        print("=" * 80)
        print()
        
        # 1. Check service status
        print("1. SERVICE STATUS")
        print("-" * 80)
        result = client.execute_command(
            "systemctl status trading-bot.service --no-pager | head -15",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output)
        print()
        
        # 2. Check if service is active
        print("2. SERVICE ACTIVE CHECK")
        print("-" * 80)
        result = client.execute_command("systemctl is-active trading-bot.service", timeout=10)
        is_active = result['stdout'].strip() == 'active'
        print(f"Service active: {is_active}")
        print()
        
        # 3. Check if service is enabled
        print("3. SERVICE ENABLED CHECK")
        print("-" * 80)
        result = client.execute_command("systemctl is-enabled trading-bot.service", timeout=10)
        is_enabled = result['stdout'].strip() == 'enabled'
        print(f"Service enabled: {is_enabled}")
        print()
        
        # 4. Check running processes
        print("4. RUNNING PROCESSES")
        print("-" * 80)
        result = client.execute_command(
            "ps aux | grep -E 'deploy_supervisor|main.py|uw_flow_daemon|dashboard' | grep -v grep",
            timeout=10
        )
        processes = result['stdout'].strip().split('\n') if result['stdout'] else []
        print(f"Processes found: {len(processes)}")
        for proc in processes[:10]:
            print(f"  {proc[:100]}")
        print()
        
        # 5. Check process hierarchy
        print("5. PROCESS HIERARCHY")
        print("-" * 80)
        result = client.execute_command(
            "ps -eo pid,ppid,comm,args | grep -E 'deploy_supervisor|main.py|systemd_start' | grep -v grep",
            timeout=10
        )
        print(result['stdout'] if result['stdout'] else 'Could not determine hierarchy')
        print()
        
        # 6. Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        if is_active and is_enabled and len(processes) >= 3:
            print("[OK] Systemd service is running correctly")
            print(f"[OK] Service is enabled on boot")
            print(f"[OK] {len(processes)} processes running")
            print("\nAll systems operational under systemd management!")
        else:
            print("⚠️  Some issues detected:")
            if not is_active:
                print("  - Service is not active")
            if not is_enabled:
                print("  - Service is not enabled")
            if len(processes) < 3:
                print(f"  - Only {len(processes)} processes running (expected at least 3)")
        print()
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

