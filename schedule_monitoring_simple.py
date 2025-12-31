#!/usr/bin/env python3
"""
Schedule Specialist Tier Monitoring Orchestrator on Droplet (Simple Version)
Uses subprocess for SSH instead of droplet_client to avoid encoding issues
"""

import subprocess
import sys
import json
import os
from pathlib import Path

def get_ssh_command():
    """Get SSH command from config or environment"""
    config_path = Path("droplet_config.json")
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
            host = config.get("host", "alpaca")
            return ["ssh", host]
    
    # Fallback to environment or default
    host = os.getenv("DROPLET_HOST", "alpaca")
    return ["ssh", host]

def main():
    """Schedule the monitoring orchestrator via cron"""
    
    # The cron command to add
    cron_command = "30 20 * * 1-5 cd /root/stock-bot && venv/bin/python specialist_tier_monitoring_orchestrator.py >> logs/orchestrator.log 2>&1"
    
    # Command to execute on droplet
    remote_command = f'cd ~/stock-bot && (crontab -l 2>/dev/null; echo "{cron_command}") | crontab - && crontab -l'
    
    print("Connecting to droplet to schedule monitoring orchestrator...")
    
    try:
        ssh_cmd = get_ssh_command()
        full_cmd = ssh_cmd + [remote_command]
        
        print(f"Executing: {' '.join(ssh_cmd)} '...'")
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("\n[SUCCESS] Monitoring orchestrator scheduled successfully!")
            print("\nCurrent crontab entries:")
            print(result.stdout)
            
            if "specialist_tier_monitoring_orchestrator.py" in result.stdout:
                print("\n[OK] Cron job verified in crontab")
                print("   Runs: Monday-Friday at 4:30 PM ET (20:30 UTC)")
                print("   Output: logs/orchestrator.log")
                return 0
            else:
                print("\n[WARNING] Cron job executed but not found in output")
                return 1
        else:
            print(f"[ERROR] Command failed with exit code {result.returncode}")
            if result.stderr:
                print(f"Error output: {result.stderr}")
            if result.stdout:
                print(f"Output: {result.stdout}")
            return 1
            
    except subprocess.TimeoutExpired:
        print("[ERROR] Connection timed out")
        return 1
    except FileNotFoundError:
        print("[ERROR] SSH command not found. Please ensure SSH is installed and configured.")
        print("\nPlease run manually on droplet:")
        print(f'  (crontab -l 2>/dev/null; echo "{cron_command}") | crontab -')
        return 1
    except Exception as e:
        print(f"[ERROR] Failed to connect to droplet: {e}")
        print("\nPlease run manually on droplet:")
        print(f'  (crontab -l 2>/dev/null; echo "{cron_command}") | crontab -')
        return 1

if __name__ == "__main__":
    sys.exit(main())
