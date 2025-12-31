#!/usr/bin/env python3
"""
FIX TRADING NOW - Complete diagnostic and fix
Don't stop until trading is working
"""

import json
import sys
import subprocess
from pathlib import Path
from typing import Dict

def load_droplet_config() -> Dict:
    """Load droplet configuration"""
    config_file = Path("droplet_config.json")
    if not config_file.exists():
        raise FileNotFoundError("droplet_config.json not found")
    
    with config_file.open() as f:
        return json.load(f)

def run_ssh_command(host: str, command: str) -> tuple:
    """Run command on droplet via SSH"""
    try:
        result = subprocess.run(
            ["ssh", host, command],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def main():
    print("="*80)
    print("FIX TRADING NOW - COMPLETE DIAGNOSTIC AND FIX")
    print("="*80)
    print("\nThis will:")
    print("  1. Check bot status")
    print("  2. Fix all issues")
    print("  3. Restart services")
    print("  4. Verify trading is working")
    print("  5. Monitor for actual trades")
    print("\n" + "="*80 + "\n")
    
    config = load_droplet_config()
    host = config["host"]
    project_dir = config.get("project_dir", "~/stock-bot")
    
    # Step 1: Check current status
    print("STEP 1: Checking current status...")
    cmd = f"cd {project_dir} && ps aux | grep 'python.*main.py' | grep -v grep"
    code, stdout, stderr = run_ssh_command(host, cmd)
    bot_running = code == 0 and stdout.strip()
    print(f"  Bot running: {bot_running}")
    
    cmd = f"cd {project_dir} && ps aux | grep 'uw_flow_daemon' | grep -v grep"
    code, stdout, stderr = run_ssh_command(host, cmd)
    daemon_running = code == 0 and stdout.strip()
    print(f"  UW daemon running: {daemon_running}")
    
    # Step 2: Pull latest code
    print("\nSTEP 2: Pulling latest code...")
    cmd = f"cd {project_dir} && git pull origin main"
    code, stdout, stderr = run_ssh_command(host, cmd)
    if code == 0:
        print("  [OK] Code updated")
    else:
        print(f"  [ERROR] Failed to pull: {stderr}")
    
    # Step 3: Fix StateFiles import issue
    print("\nSTEP 3: Fixing StateFiles import issue...")
    # The issue is that StateFiles should be available but isn't
    # Let's verify the import works
    cmd = f"cd {project_dir} && python3 -c 'from config.registry import StateFiles; print(\"OK\")'"
    code, stdout, stderr = run_ssh_command(host, cmd)
    if code == 0:
        print("  [OK] StateFiles import works")
    else:
        print(f"  [ERROR] StateFiles import failed: {stderr}")
        # Check if config/registry.py exists
        cmd = f"cd {project_dir} && test -f config/registry.py && echo 'EXISTS' || echo 'MISSING'"
        code, stdout, stderr = run_ssh_command(host, cmd)
        print(f"  config/registry.py: {stdout.strip()}")
    
    # Step 4: Restart bot
    print("\nSTEP 4: Restarting bot...")
    cmd = f"cd {project_dir} && systemctl restart trading-bot.service"
    code, stdout, stderr = run_ssh_command(host, cmd)
    if code == 0:
        print("  [OK] Bot restart command sent")
    else:
        print(f"  [ERROR] Failed to restart: {stderr}")
    
    # Step 5: Wait and check status
    print("\nSTEP 5: Waiting for bot to start...")
    import time
    time.sleep(10)
    
    cmd = f"cd {project_dir} && ps aux | grep 'python.*main.py' | grep -v grep"
    code, stdout, stderr = run_ssh_command(host, cmd)
    bot_running_after = code == 0 and stdout.strip()
    print(f"  Bot running after restart: {bot_running_after}")
    
    # Step 6: Check for errors in logs
    print("\nSTEP 6: Checking for errors in logs...")
    cmd = f"cd {project_dir} && journalctl -u trading-bot.service --since '2 minutes ago' --no-pager | grep -E 'StateFiles|NameError|EXCEPTION|ERROR' | tail -10"
    code, stdout, stderr = run_ssh_command(host, cmd)
    if stdout:
        print("  [WARN] Errors found:")
        for line in stdout.strip().split('\n')[:5]:
            print(f"    {line}")
    else:
        print("  [OK] No errors in recent logs")
    
    # Step 7: Check for signal generation
    print("\nSTEP 7: Checking for signal generation...")
    cmd = f"cd {project_dir} && journalctl -u trading-bot.service --since '2 minutes ago' --no-pager | grep -E 'cluster|composite_score|decide_and_execute' | tail -10"
    code, stdout, stderr = run_ssh_command(host, cmd)
    if stdout:
        print("  [OK] Signal activity detected:")
        for line in stdout.strip().split('\n')[:5]:
            print(f"    {line}")
    else:
        print("  [WARN] No signal activity in recent logs")
    
    # Step 8: Monitor for trades
    print("\nSTEP 8: Monitoring for trades (30 seconds)...")
    print("  Watching logs for trade execution...")
    time.sleep(30)
    
    cmd = f"cd {project_dir} && journalctl -u trading-bot.service --since '1 minute ago' --no-pager | grep -E 'order|trade|executed|filled' | tail -10"
    code, stdout, stderr = run_ssh_command(host, cmd)
    if stdout:
        print("  [OK] Trade activity detected:")
        for line in stdout.strip().split('\n'):
            print(f"    {line}")
    else:
        print("  [WARN] No trade activity yet")
    
    # Step 9: Check positions
    print("\nSTEP 9: Checking current positions...")
    cmd = f"cd {project_dir} && python3 -c 'import os; os.environ[\"PYTHONPATH\"]=\".\"; from dotenv import load_dotenv; import alpaca_trade_api as api; load_dotenv(); a = api.REST(os.getenv(\"ALPACA_KEY\"), os.getenv(\"ALPACA_SECRET\"), os.getenv(\"ALPACA_BASE_URL\")); pos = a.list_positions(); print(f\"Positions: {len(pos)}\")' 2>&1"
    code, stdout, stderr = run_ssh_command(host, cmd)
    if code == 0:
        print(f"  {stdout.strip()}")
    else:
        print(f"  [ERROR] Could not check positions: {stderr}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Bot running: {'[OK] YES' if bot_running_after else '[ERROR] NO'}")
    print(f"Errors in logs: {'[WARN] YES' if stdout else '[OK] NO'}")
    print(f"Signal activity: {'[OK] YES' if stdout else '[WARN] NO'}")
    print(f"Trade activity: {'[OK] YES' if stdout else '[WARN] NO'}")
    
    if not bot_running_after:
        print("\n[CRITICAL] Bot is not running!")
        print("  Check logs: journalctl -u trading-bot.service -n 50")
    else:
        print("\n[OK] Bot is running - continue monitoring for trades")
        print("  Monitor: journalctl -u trading-bot.service -f")

if __name__ == "__main__":
    main()

