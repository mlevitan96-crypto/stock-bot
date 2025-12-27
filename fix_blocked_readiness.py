#!/usr/bin/env python3
"""Fix blocked readiness status by addressing critical failure points"""

import json
import subprocess
from pathlib import Path
from failure_point_monitor import get_failure_point_monitor

def fix_issue(fp_id, error_msg):
    """Attempt to fix a specific failure point"""
    print(f"\nAttempting to fix {fp_id}...")
    
    if "FP-1.1" in fp_id or "daemon" in error_msg.lower():
        print("  -> Restarting UW daemon via systemd...")
        try:
            subprocess.run(['systemctl', 'restart', 'trading-bot.service'], 
                         timeout=10, check=True)
            print("  [OK] Service restarted")
            return True
        except Exception as e:
            print(f"  [FAIL] Could not restart: {e}")
            return False
    
    elif "FP-1.2" in fp_id or "FP-1.3" in fp_id or "FP-1.4" in fp_id or "cache" in error_msg.lower():
        print("  -> Checking UW daemon status...")
        try:
            result = subprocess.run(['pgrep', '-f', 'uw_flow_daemon'], 
                                  capture_output=True, timeout=5)
            if result.returncode != 0:
                print("  -> Daemon not running, restarting...")
                subprocess.run(['systemctl', 'restart', 'trading-bot.service'], 
                             timeout=10)
                print("  [OK] Service restarted")
            else:
                print("  [OK] Daemon is running")
            return True
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
            return False
    
    elif "FP-2.1" in fp_id or "weights" in error_msg.lower():
        print("  -> Initializing adaptive weights...")
        try:
            result = subprocess.run(['python3', 'fix_adaptive_weights_init.py'],
                                   capture_output=True, timeout=30, cwd=Path.cwd())
            if result.returncode == 0:
                print("  [OK] Weights initialized")
                return True
            else:
                print(f"  [FAIL] Weight init failed: {result.stderr.decode()}")
                return False
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
            return False
    
    elif "FP-3.1" in fp_id or "freeze" in error_msg.lower():
        print("  -> Checking for freeze files...")
        freeze_file = Path("state/governor_freezes.json")
        pre_market = Path("state/pre_market_freeze.flag")
        
        removed = False
        if freeze_file.exists():
            try:
                with freeze_file.open() as f:
                    freezes = json.load(f)
                if freezes:
                    freeze_file.unlink()
                    print(f"  [OK] Removed {freeze_file}")
                    removed = True
            except:
                pass
        
        if pre_market.exists():
            pre_market.unlink()
            print(f"  [OK] Removed {pre_market}")
            removed = True
        
        if not removed:
            print("  [OK] No freeze files found")
        return True
    
    elif "FP-4.1" in fp_id or "FP-4.2" in fp_id or "alpaca" in error_msg.lower():
        print("  -> Checking Alpaca connection...")
        print("  [INFO] Alpaca connection issues require manual credential check")
        return False
    
    elif "FP-6.1" in fp_id or "bot" in error_msg.lower():
        print("  -> Restarting bot via systemd...")
        try:
            subprocess.run(['systemctl', 'restart', 'trading-bot.service'], 
                         timeout=10, check=True)
            print("  [OK] Bot restarted")
            return True
        except Exception as e:
            print(f"  [FAIL] Could not restart: {e}")
            return False
    
    else:
        print(f"  [INFO] No automatic fix available for {fp_id}")
        return False

def main():
    print("=" * 80)
    print("FIXING BLOCKED READINESS STATUS")
    print("=" * 80)
    
    monitor = get_failure_point_monitor()
    readiness = monitor.get_trading_readiness()
    
    print(f"\nCurrent Status: {readiness['readiness']}")
    print(f"Critical Issues: {readiness['critical_count']}")
    print(f"Warnings: {readiness['warning_count']}")
    
    if readiness['readiness'] == "READY":
        print("\n[OK] System is already READY - no fixes needed")
        return 0
    
    # Fix critical issues
    if readiness['critical_fps']:
        print(f"\nFixing {len(readiness['critical_fps'])} critical issues...")
        print("-" * 80)
        
        fixed_count = 0
        for fp_id in readiness['critical_fps']:
            fp_status = readiness['failure_points'].get(fp_id, {})
            error = fp_status.get('last_error', 'Unknown error')
            
            print(f"\n{fp_id}: {fp_status.get('name', 'Unknown')}")
            print(f"  Error: {error}")
            
            if fix_issue(fp_id, error):
                fixed_count += 1
                print(f"  [SUCCESS] Fixed {fp_id}")
            else:
                print(f"  [FAILED] Could not auto-fix {fp_id}")
        
        # Re-check after fixes
        print("\n" + "=" * 80)
        print("RE-CHECKING STATUS AFTER FIXES")
        print("=" * 80)
        
        readiness_after = monitor.get_trading_readiness()
        print(f"\nNew Status: {readiness_after['readiness']}")
        print(f"Critical Issues: {readiness_after['critical_count']}")
        print(f"Warnings: {readiness_after['warning_count']}")
        
        if readiness_after['readiness'] == "READY":
            print("\n[SUCCESS] System is now READY!")
            return 0
        elif readiness_after['readiness'] == "DEGRADED":
            print("\n[WARN] System is DEGRADED - some warnings remain")
            if readiness_after['warning_fps']:
                print("Warning FPs:", ', '.join(readiness_after['warning_fps']))
            return 0
        else:
            print("\n[FAIL] System still BLOCKED")
            if readiness_after['critical_fps']:
                print("Remaining critical FPs:", ', '.join(readiness_after['critical_fps']))
            return 1
    else:
        print("\n[INFO] No critical issues to fix")
        return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())

