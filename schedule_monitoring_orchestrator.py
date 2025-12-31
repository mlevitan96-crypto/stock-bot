#!/usr/bin/env python3
"""
Schedule Specialist Tier Monitoring Orchestrator on Droplet
Adds cron job to run orchestrator daily at 4:30 PM ET (20:30 UTC)
"""

import sys
from droplet_client import DropletClient

def main():
    """Schedule the monitoring orchestrator via cron"""
    
    # The cron command to add
    cron_command = "30 20 * * 1-5 cd /root/stock-bot && venv/bin/python specialist_tier_monitoring_orchestrator.py >> logs/orchestrator.log 2>&1"
    
    # Command to add to crontab (preserves existing entries)
    add_cron_cmd = f'(crontab -l 2>/dev/null; echo "{cron_command}") | crontab -'
    
    # Command to verify crontab was updated
    verify_cron_cmd = "crontab -l"
    
    print("Connecting to droplet to schedule monitoring orchestrator...")
    
    try:
        client = DropletClient()
        with client:
            # Add cron job
            print("Adding cron job...")
            result = client.execute_command(
                f"cd ~/stock-bot && {add_cron_cmd}",
                timeout=30
            )
            
            if not result.get("success"):
                print(f"ERROR: Failed to add cron job: {result.get('stderr', 'Unknown error')}")
                return 1
            
            print("[OK] Cron job added successfully")
            
            # Verify cron job was added
            print("Verifying cron job...")
            verify_result = client.execute_command(
                verify_cron_cmd,
                timeout=30
            )
            
            if verify_result.get("success"):
                stdout = verify_result.get("stdout", "")
                print("\nCurrent crontab entries:")
                print(stdout)
                
                # Check if our cron job is in the output
                if "specialist_tier_monitoring_orchestrator.py" in stdout:
                    print("\n[SUCCESS] Monitoring orchestrator scheduled successfully!")
                    print("   Runs: Monday-Friday at 4:30 PM ET (20:30 UTC)")
                    print("   Output: logs/orchestrator.log")
                    return 0
                else:
                    print("\n⚠️  WARNING: Cron job command executed but not found in crontab")
                    print("   Please verify manually with: crontab -l")
                    return 1
            else:
                print(f"⚠️  WARNING: Could not verify cron job: {verify_result.get('stderr', 'Unknown error')}")
                print("   Cron job may have been added. Please verify manually with: crontab -l")
                return 1
                
    except Exception as e:
        print(f"ERROR: Failed to connect to droplet: {e}")
        print("\nPlease run manually on droplet:")
        print(f'  (crontab -l 2>/dev/null; echo "{cron_command}") | crontab -')
        return 1

if __name__ == "__main__":
    sys.exit(main())
