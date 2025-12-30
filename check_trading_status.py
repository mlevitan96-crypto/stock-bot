#!/usr/bin/env python3
"""
Comprehensive Trading Status Check
Verifies bot is operational and not frozen
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

def check_positions():
    """Check current Alpaca positions"""
    try:
        import alpaca_trade_api as tradeapi
        api = tradeapi.REST(
            os.getenv("ALPACA_API_KEY"),
            os.getenv("ALPACA_API_SECRET"),
            os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
            api_version="v2"
        )
        positions = api.list_positions()
        return {
            "count": len(positions),
            "positions": [{
                "symbol": p.symbol,
                "qty": float(p.qty),
                "entry_price": float(p.avg_entry_price),
                "pnl": float(p.unrealized_pl),
                "pnl_pct": float(p.unrealized_plpc) * 100
            } for p in positions]
        }
    except Exception as e:
        return {"error": str(e)}

def check_bot_status():
    """Check bot heartbeat and status"""
    heartbeat_file = Path("state/bot_heartbeat.json")
    if not heartbeat_file.exists():
        return {"error": "Heartbeat file not found"}
    
    hb = json.loads(heartbeat_file.read_text())
    last_hb = hb.get("last_heartbeat_ts", 0)
    age_sec = datetime.now(timezone.utc).timestamp() - last_hb
    
    freeze_file = Path("state/pre_market_freeze.flag")
    
    return {
        "heartbeat_age_sec": age_sec,
        "heartbeat_age_min": age_sec / 60,
        "running": hb.get("running", False),
        "iter_count": hb.get("iter_count", 0),
        "freeze_flag_exists": freeze_file.exists(),
        "status": "healthy" if age_sec < 300 else "stale"
    }

def check_recent_activity():
    """Check recent trading activity"""
    attr_file = Path("logs/attribution.jsonl")
    if not attr_file.exists():
        return {"error": "Attribution file not found"}
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    entries = []
    exits = []
    
    for line in attr_file.read_text().splitlines()[-200:]:
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if record.get("type") != "attribution":
                continue
            
            trade_id = record.get("trade_id", "")
            ts = record.get("ts", "")
            
            if not ts:
                continue
            
            try:
                if isinstance(ts, (int, float)):
                    trade_time = datetime.fromtimestamp(ts, tz=timezone.utc)
                else:
                    trade_time = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                    if trade_time.tzinfo is None:
                        trade_time = trade_time.replace(tzinfo=timezone.utc)
            except:
                continue
            
            if trade_time < today:
                continue
            
            if trade_id.startswith("open_"):
                entries.append({
                    "symbol": record.get("symbol"),
                    "score": record.get("context", {}).get("entry_score", 0),
                    "timestamp": ts
                })
            else:
                exits.append({
                    "symbol": record.get("symbol"),
                    "pnl_pct": record.get("pnl_pct", 0),
                    "reason": record.get("context", {}).get("close_reason", "unknown"),
                    "timestamp": ts
                })
        except:
            continue
    
    return {
        "entries_today": len(entries),
        "exits_today": len(exits),
        "recent_entries": entries[-5:],
        "recent_exits": exits[-5:]
    }

def check_blocked_trades():
    """Check blocked trades today"""
    blocked_file = Path("state/blocked_trades.jsonl")
    if not blocked_file.exists():
        return {"blocked_today": 0, "reasons": {}}
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    blocked_today = []
    
    for line in blocked_file.read_text().splitlines()[-100:]:
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            ts = record.get("timestamp", "")
            if not ts:
                continue
            try:
                if isinstance(ts, (int, float)):
                    trade_time = datetime.fromtimestamp(ts, tz=timezone.utc)
                else:
                    trade_time = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                    if trade_time.tzinfo is None:
                        trade_time = trade_time.replace(tzinfo=timezone.utc)
            except:
                continue
            
            if trade_time >= today:
                blocked_today.append(record)
        except:
            continue
    
    reasons = {}
    for b in blocked_today:
        reason = b.get("reason", "unknown")
        reasons[reason] = reasons.get(reason, 0) + 1
    
    high_score_blocked = [b for b in blocked_today if b.get("score", 0) >= 2.5]
    
    return {
        "blocked_today": len(blocked_today),
        "reasons": dict(sorted(reasons.items(), key=lambda x: x[1], reverse=True)[:5]),
        "high_score_blocked": len(high_score_blocked)
    }

def check_config():
    """Check trading configuration"""
    try:
        from main import Config
        return {
            "MAX_CONCURRENT_POSITIONS": Config.MAX_CONCURRENT_POSITIONS,
            "MAX_NEW_POSITIONS_PER_CYCLE": Config.MAX_NEW_POSITIONS_PER_CYCLE,
            "MIN_EXEC_SCORE": Config.MIN_EXEC_SCORE,
            "ENTRY_MODE": Config.ENTRY_MODE
        }
    except Exception as e:
        return {"error": str(e)}

def check_uw_daemon():
    """Check UW daemon status"""
    daemon_file = Path("state/uw_flow_daemon_status.json")
    if not daemon_file.exists():
        return {"error": "Daemon status file not found"}
    
    daemon = json.loads(daemon_file.read_text())
    last_update = daemon.get("last_update", "")
    
    try:
        if last_update:
            ts = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - ts).total_seconds()
        else:
            age = None
    except:
        age = None
    
    return {
        "status": daemon.get("status", "unknown"),
        "last_update_age_sec": age,
        "last_update_age_min": age / 60 if age else None
    }

def main():
    print("=" * 80)
    print("COMPREHENSIVE TRADING STATUS CHECK")
    print("=" * 80)
    print()
    
    # Check positions
    print("1. CURRENT POSITIONS")
    print("-" * 80)
    positions = check_positions()
    if "error" in positions:
        print(f"   [ERROR] {positions['error']}")
    else:
        print(f"   Count: {positions['count']}")
        for p in positions['positions']:
            pnl_sign = "+" if p['pnl'] >= 0 else ""
            print(f"   {p['symbol']}: {p['qty']} @ ${p['entry_price']:.2f} (P&L: {pnl_sign}${p['pnl']:.2f}, {pnl_sign}{p['pnl_pct']:.2f}%)")
    print()
    
    # Check bot status
    print("2. BOT STATUS")
    print("-" * 80)
    bot_status = check_bot_status()
    if "error" in bot_status:
        print(f"   [ERROR] {bot_status['error']}")
    else:
        status_icon = "✅" if bot_status['status'] == "healthy" else "⚠️"
        print(f"   {status_icon} Heartbeat: {bot_status['heartbeat_age_min']:.1f} min ago")
        print(f"   Running: {bot_status['running']}")
        print(f"   Iter count: {bot_status['iter_count']}")
        print(f"   Freeze flag: {'EXISTS' if bot_status['freeze_flag_exists'] else 'None'}")
    print()
    
    # Check recent activity
    print("3. RECENT TRADING ACTIVITY")
    print("-" * 80)
    activity = check_recent_activity()
    if "error" in activity:
        print(f"   [ERROR] {activity['error']}")
    else:
        print(f"   Entries today: {activity['entries_today']}")
        print(f"   Exits today: {activity['exits_today']}")
        if activity['recent_entries']:
            print(f"   Recent entries:")
            for e in activity['recent_entries']:
                print(f"     {e['symbol']}: Score {e['score']:.2f}")
    print()
    
    # Check blocked trades
    print("4. BLOCKED TRADES TODAY")
    print("-" * 80)
    blocked = check_blocked_trades()
    print(f"   Blocked today: {blocked['blocked_today']}")
    print(f"   High score (>=2.5) blocked: {blocked['high_score_blocked']}")
    if blocked['reasons']:
        print(f"   Top block reasons:")
        for reason, count in blocked['reasons'].items():
            print(f"     {reason}: {count}")
    print()
    
    # Check config
    print("5. TRADING CONFIGURATION")
    print("-" * 80)
    config = check_config()
    if "error" in config:
        print(f"   [ERROR] {config['error']}")
    else:
        print(f"   MAX_CONCURRENT_POSITIONS: {config['MAX_CONCURRENT_POSITIONS']}")
        print(f"   MAX_NEW_POSITIONS_PER_CYCLE: {config['MAX_NEW_POSITIONS_PER_CYCLE']}")
        print(f"   MIN_EXEC_SCORE: {config['MIN_EXEC_SCORE']}")
        print(f"   ENTRY_MODE: {config['ENTRY_MODE']}")
    print()
    
    # Check UW daemon
    print("6. UW DAEMON STATUS")
    print("-" * 80)
    daemon = check_uw_daemon()
    if "error" in daemon:
        print(f"   [ERROR] {daemon['error']}")
    else:
        print(f"   Status: {daemon['status']}")
        if daemon['last_update_age_min']:
            print(f"   Last update: {daemon['last_update_age_min']:.1f} min ago")
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    issues = []
    if positions.get("count", 0) < 3:
        issues.append(f"Low position count ({positions.get('count', 0)})")
    if bot_status.get("status") != "healthy":
        issues.append("Bot heartbeat stale")
    if bot_status.get("freeze_flag_exists"):
        issues.append("Freeze flag exists")
    if blocked.get("high_score_blocked", 0) > 10:
        issues.append(f"Many high-score trades blocked ({blocked['high_score_blocked']})")
    if activity.get("entries_today", 0) == 0:
        issues.append("No entries today")
    
    if issues:
        print("⚠️  POTENTIAL ISSUES:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ NO ISSUES DETECTED")
        print("   Bot is operational and waiting for high-conviction signals")
    
    print()

if __name__ == "__main__":
    main()

