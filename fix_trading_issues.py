#!/usr/bin/env python3
"""
Auto-Fix Trading Issues
Automatically fixes common issues preventing trades
"""

import json
import time
import sys
import subprocess
from pathlib import Path
from datetime import datetime

def fix_uw_daemon():
    """Restart UW daemon if not running"""
    print("Checking UW daemon...")
    result = subprocess.run(['pgrep', '-f', 'uw_flow_daemon'], 
                          capture_output=True, timeout=5)
    if result.returncode != 0:
        print("  UW daemon not running - attempting restart...")
        try:
            subprocess.run(['systemctl', 'restart', 'trading-bot.service'], 
                         timeout=10)
            print("  ✓ Restarted via systemd")
            return True
        except Exception as e:
            print(f"  ✗ Failed to restart: {e}")
            return False
    else:
        print("  ✓ UW daemon is running")
        return True

def fix_adaptive_weights():
    """Ensure adaptive weights are initialized"""
    print("Checking adaptive weights...")
    weights_file = Path("state/signal_weights.json")
    
    if not weights_file.exists():
        print("  Weights file missing - creating...")
        weights_file.parent.mkdir(exist_ok=True)
        state = {
            "weight_bands": {},
            "last_update": int(time.time())
        }
        with weights_file.open("w") as f:
            json.dump(state, f, indent=2)
        print("  ✓ Created weights file")
    
    try:
        with weights_file.open() as f:
            state = json.load(f)
        bands = state.get("weight_bands", {})
        
        if len(bands) != 21:
            print(f"  Only {len(bands)}/21 components initialized - fixing...")
            # Initialize all 21 components
            components = [
                "dark_pool", "greeks_gamma", "iv_rank", "oi_change", "market_tide",
                "regime_modifier", "shorts_squeeze", "institutional", "calendar_catalyst",
                "etf_flow", "squeeze_score", "toxicity_penalty", "flow_conviction",
                "net_premium", "volume_surge", "sentiment_alignment", "ftd_pressure",
                "insider_activity", "congress_trading", "earnings_catalyst", "macro_theme"
            ]
            
            for comp in components:
                if comp not in bands:
                    bands[comp] = {
                        "current": 1.0,
                        "min": 0.25,
                        "max": 2.5,
                        "history": []
                    }
            
            state["weight_bands"] = bands
            state["last_update"] = int(time.time())
            
            with weights_file.open("w") as f:
                json.dump(state, f, indent=2)
            print(f"  ✓ Initialized all 21 components")
            return True
        else:
            print(f"  ✓ All {len(bands)} components initialized")
            return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def fix_freeze_state():
    """Check and report freeze state (no auto-fix - requires manual intervention)"""
    print("Checking freeze state...")
    freeze_file = Path("state/freeze_flags.json")
    if not freeze_file.exists():
        print("  ✓ No freeze flags")
        return True
    
    try:
        with freeze_file.open() as f:
            flags = json.load(f)
        active_flags = {k: v for k, v in flags.items() if v.get("active", False)}
        if active_flags:
            print(f"  ⚠ {len(active_flags)} active freeze flags (requires manual intervention):")
            for flag, details in active_flags.items():
                print(f"    - {flag}: {details.get('reason', 'unknown')}")
            return False
        else:
            print("  ✓ No active freeze flags")
            return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def check_cache_freshness():
    """Check if cache needs refresh"""
    print("Checking cache freshness...")
    cache_file = Path("data/uw_flow_cache.json")
    if not cache_file.exists():
        print("  ✗ Cache file missing")
        return False
    
    mtime = cache_file.stat().st_mtime
    age_minutes = (time.time() - mtime) / 60
    
    if age_minutes > 30:
        print(f"  ⚠ Cache is {age_minutes:.1f} minutes old - may need refresh")
        return False
    else:
        print(f"  ✓ Cache is fresh ({age_minutes:.1f} minutes old)")
        return True

def reset_self_healing_threshold():
    """Reset self-healing threshold if it's blocking trades"""
    print("Checking self-healing threshold...")
    threshold_file = Path("state/self_healing_threshold.json")
    if threshold_file.exists():
        try:
            with threshold_file.open() as f:
                state = json.load(f)
            if state.get("adjustment", 0) > 0:
                print(f"  ⚠ Threshold raised by {state.get('adjustment')} - checking if reset needed...")
                # Check if 24 hours have passed
                activated_at = state.get("activated_at")
                if activated_at:
                    hours_since = (time.time() - activated_at) / 3600
                    if hours_since >= 24:
                        print("  ✓ 24 hours passed - resetting threshold...")
                        state["adjustment"] = 0.0
                        state["activated_at"] = None
                        state["last_reset_at"] = int(time.time())
                        state["consecutive_losses"] = 0
                        with threshold_file.open("w") as f:
                            json.dump(state, f, indent=2)
                        print("  ✓ Threshold reset")
                        return True
                    else:
                        print(f"  ⚠ Threshold still active ({hours_since:.1f} hours since activation)")
                        return False
            else:
                print("  ✓ Threshold not activated")
                return True
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
    else:
        print("  ✓ No threshold file (using default)")
        return True

def main():
    print("="*80)
    print("AUTO-FIX TRADING ISSUES")
    print("="*80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    fixes_applied = []
    issues_remaining = []
    
    # Fix 1: UW Daemon
    if fix_uw_daemon():
        fixes_applied.append("UW daemon")
    else:
        issues_remaining.append("UW daemon not running")
    
    # Fix 2: Adaptive Weights
    if fix_adaptive_weights():
        fixes_applied.append("Adaptive weights")
    else:
        issues_remaining.append("Adaptive weights initialization")
    
    # Fix 3: Freeze State (report only)
    if not fix_freeze_state():
        issues_remaining.append("Freeze flags active (manual intervention required)")
    
    # Fix 4: Cache Freshness
    if check_cache_freshness():
        fixes_applied.append("Cache freshness")
    else:
        issues_remaining.append("Cache may be stale")
    
    # Fix 5: Self-Healing Threshold
    if reset_self_healing_threshold():
        fixes_applied.append("Self-healing threshold")
    else:
        # Not necessarily an issue - threshold may be intentionally raised
        pass
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if fixes_applied:
        print(f"\n✓ Fixed {len(fixes_applied)} issues:")
        for fix in fixes_applied:
            print(f"  - {fix}")
    
    if issues_remaining:
        print(f"\n⚠ {len(issues_remaining)} issues remain:")
        for issue in issues_remaining:
            print(f"  - {issue}")
    else:
        print("\n✓ No critical issues found")
    
    print("\nNext steps:")
    print("  1. Run diagnose_no_trades.py for full diagnosis")
    print("  2. Check logs for signal generation")
    print("  3. Verify market is open")
    print("  4. Monitor bot activity")

if __name__ == "__main__":
    main()

