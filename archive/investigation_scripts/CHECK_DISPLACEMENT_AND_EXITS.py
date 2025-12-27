#!/usr/bin/env python3
"""
Check why displacement isn't working and if exits are functioning
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

LOGS_DIR = Path("logs")
STATE_DIR = Path("state")
DATA_DIR = Path("data")

print("=" * 80)
print("DISPLACEMENT & EXIT DIAGNOSIS")
print("=" * 80)
print()

# 1. Check displacement logs
print("1. DISPLACEMENT LOGS")
print("-" * 80)
displacement_file = LOGS_DIR / "displacement.jsonl"
if displacement_file.exists():
    now = time.time()
    cutoff_1h = now - 3600
    
    events_1h = []
    for line in displacement_file.read_text().splitlines()[-50:]:
        try:
            event = json.loads(line.strip())
            if event.get("_ts", 0) > cutoff_1h:
                events_1h.append(event)
        except:
            pass
    
    if events_1h:
        print(f"Displacement events in last hour: {len(events_1h)}")
        for e in events_1h[-5:]:
            msg = e.get("msg", "unknown")
            symbol = e.get("symbol", "unknown")
            reasons = e.get("reasons", {})
            print(f"  {msg}: {symbol}")
            if reasons:
                print(f"    Reasons: {reasons}")
    else:
        print("⚠️  No displacement events in last hour")
        print("  This means displacement is being called but finding no candidates")
else:
    print("⚠️  Displacement log does not exist")
print()

# 2. Check exit logs
print("2. EXIT LOGS")
print("-" * 80)
exit_file = LOGS_DIR / "exit.jsonl"
if exit_file.exists():
    now = time.time()
    cutoff_1h = now - 3600
    
    exits_1h = []
    for line in exit_file.read_text().splitlines()[-50:]:
        try:
            event = json.loads(line.strip())
            if event.get("_ts", 0) > cutoff_1h:
                exits_1h.append(event)
        except:
            pass
    
    if exits_1h:
        print(f"Exits in last hour: {len(exits_1h)}")
        for e in exits_1h[-5:]:
            symbol = e.get("symbol", "unknown")
            reason = e.get("reason", "unknown")
            print(f"  {symbol}: {reason}")
    else:
        print("⚠️  No exits in last hour")
        print("  Positions may not be meeting exit criteria")
else:
    print("⚠️  Exit log does not exist")
print()

# 3. Check actual positions (if API available)
print("3. POSITION ANALYSIS")
print("-" * 80)
try:
    import alpaca_trade_api as tradeapi
    key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY", "")
    secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET", "")
    base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    
    if key and secret:
        api = tradeapi.REST(key, secret, base_url)
        positions = api.list_positions()
        
        print(f"Current positions: {len(positions)}")
        
        # Load metadata
        metadata_path = STATE_DIR / "position_metadata.json"
        metadata = {}
        if metadata_path.exists():
            try:
                metadata = json.loads(metadata_path.read_text())
            except:
                pass
        
        # Analyze each position
        now = datetime.now(timezone.utc)
        displacement_candidates = []
        
        for pos in positions:
            symbol = getattr(pos, "symbol", "")
            entry_price = float(getattr(pos, "avg_entry_price", 0))
            current_price = float(getattr(pos, "current_price", entry_price))
            pnl_pct = (current_price - entry_price) / entry_price if entry_price > 0 else 0
            
            pos_meta = metadata.get(symbol, {})
            entry_ts_str = pos_meta.get("entry_ts")
            age_hours = 0
            if entry_ts_str:
                try:
                    entry_ts = datetime.fromisoformat(entry_ts_str.replace("Z", "+00:00"))
                    if entry_ts.tzinfo is None:
                        entry_ts = entry_ts.replace(tzinfo=timezone.utc)
                    age_hours = (now - entry_ts).total_seconds() / 3600
                except:
                    pass
            
            original_score = pos_meta.get("entry_score", 0)
            
            # Check displacement eligibility
            eligible = True
            reasons = []
            if age_hours < 4:
                eligible = False
                reasons.append(f"too_young({age_hours:.1f}h < 4h)")
            if abs(pnl_pct) > 0.01:
                eligible = False
                reasons.append(f"pnl_out_of_range({pnl_pct*100:.2f}% > ±1%)")
            
            if eligible:
                displacement_candidates.append({
                    "symbol": symbol,
                    "age_hours": age_hours,
                    "pnl_pct": pnl_pct,
                    "original_score": original_score
                })
            
            print(f"  {symbol}: age={age_hours:.1f}h, pnl={pnl_pct*100:.2f}%, score={original_score:.2f}")
            if reasons:
                print(f"    Not eligible: {', '.join(reasons)}")
        
        print()
        print(f"Displacement-eligible positions: {len(displacement_candidates)}")
        if displacement_candidates:
            print("  Eligible symbols:")
            for c in displacement_candidates:
                print(f"    {c['symbol']}: age={c['age_hours']:.1f}h, pnl={c['pnl_pct']*100:.2f}%")
        else:
            print("  ⚠️  NO positions eligible for displacement")
            print("  This is why displacement isn't working!")
    else:
        print("⚠️  Alpaca credentials not available")
except Exception as e:
    print(f"⚠️  Could not check positions: {e}")
print()

# 4. Check displacement cooldowns
print("4. DISPLACEMENT COOLDOWNS")
print("-" * 80)
cooldown_file = STATE_DIR / "displacement_cooldowns.json"
if cooldown_file.exists():
    try:
        cooldowns = json.loads(cooldown_file.read_text())
        now = datetime.now(timezone.utc)
        active_cooldowns = []
        
        for symbol, cooldown_ts in cooldowns.items():
            try:
                cooldown_dt = datetime.fromisoformat(cooldown_ts.replace("Z", "+00:00"))
                if cooldown_dt.tzinfo is None:
                    cooldown_dt = cooldown_dt.replace(tzinfo=timezone.utc)
                hours_left = (cooldown_dt + timedelta(hours=6) - now).total_seconds() / 3600
                if hours_left > 0:
                    active_cooldowns.append((symbol, hours_left))
            except:
                pass
        
        if active_cooldowns:
            print(f"Active cooldowns: {len(active_cooldowns)}")
            for symbol, hours in active_cooldowns:
                print(f"  {symbol}: {hours:.1f} hours remaining")
        else:
            print("✅ No active cooldowns")
    except Exception as e:
        print(f"⚠️  Could not read cooldowns: {e}")
else:
    print("✅ No cooldown file (no recent displacements)")
print()

# 5. Recommendations
print("=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)
print()
print("If displacement isn't working:")
print("  1. Positions may be too new (< 4 hours)")
print("  2. Positions may have P&L outside ±1% (too strict)")
print("  3. New signals may not exceed original by 2.0 (too high requirement)")
print("  4. All positions may be in 6-hour cooldown")
print()
print("Solutions:")
print("  - Relax displacement criteria (increase max_pnl_pct, reduce score_advantage)")
print("  - Check if exits are working (should close losing/stale positions)")
print("  - Consider closing positions that are losing money")
print()
