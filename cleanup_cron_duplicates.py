#!/usr/bin/env python3
"""
Clean up duplicate cron entries for monitoring orchestrator
"""

import subprocess
import sys
import json
import os
from pathlib import Path

def get_ssh_command():
    """Get SSH command from config"""
    config_path = Path("droplet_config.json")
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
            host = config.get("host", "alpaca")
            return ["ssh", host]
    host = os.getenv("DROPLET_HOST", "alpaca")
    return ["ssh", host]

def main():
    """Remove duplicate cron entries, keeping only one"""
    
    remote_command = '''cd ~/stock-bot && \
crontab -l 2>/dev/null | \
grep -v "specialist_tier_monitoring_orchestrator.py" | \
(cat; echo '30 20 * * 1-5 cd /root/stock-bot && venv/bin/python specialist_tier_monitoring_orchestrator.py >> logs/orchestrator.log 2>&1') | \
crontab - && \
crontab -l'''
    
    print("Cleaning up duplicate cron entries...")
    
    try:
        ssh_cmd = get_ssh_command()
        full_cmd = ssh_cmd + [remote_command]
        
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("\n[SUCCESS] Cron entries cleaned up!")
            print("\nCurrent crontab entries:")
            print(result.stdout)
            
            count = result.stdout.count("specialist_tier_monitoring_orchestrator.py")
            if count == 1:
                print(f"\n[OK] Found exactly 1 monitoring orchestrator cron job (as expected)")
                return 0
            else:
                print(f"\n[WARNING] Found {count} monitoring orchestrator cron jobs (expected 1)")
                return 1
        else:
            print(f"[ERROR] Command failed: {result.stderr}")
            return 1
            
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
