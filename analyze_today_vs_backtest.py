#!/usr/bin/env python3
"""Compare today's live trades against 7-day backtest findings"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

LOGS_DIR = Path("logs")
ATTRIBUTION_LOG = LOGS_DIR / "attribution.jsonl"
BACKTEST_REPORT = Path("reports/7_day_quick_audit.json")

def parse_timestamp(ts_str):
    """Parse various timestamp formats"""
    if not ts_str:
        return None
    try:
        if isinstance(ts_str, (int, float)):
            return datetime.fromtimestamp(ts_str, tz=timezone.utc)
        if isinstance(ts_str, str):
            ts_str = ts_str.replace("Z", "+00:00")
            return datetime.fromisoformat(ts_str)
    except:
        pass
    return None

def load_today_trades():
    """Load today's trades"""
    today = datetime.now(timezone.utc).date()
    trades = []
    
    if not ATTRIBUTION_LOG.exists():
        return trades
    
    with ATTRIBUTION_LOG.open("r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                trade = json.loads(line)
                if trade.get("type") != "attribution":
                    continue
                
                ts_str = trade.get("ts") or trade.get("timestamp")
                trade_date = None
                if ts_str:
                    trade_dt = parse_timestamp(ts_str)
                    if trade_dt:
                        trade_date = trade_dt.date()
                
                if trade_date == today:
                    trades.append(trade)
            except:
                continue
    
    return trades

def analyze_trades(trades):
    """Analyze trade patterns"""
    if not trades:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "stale_exits": 0,
            "stale_exit_pct": 0.0,
            "avg_hold_minutes": 0.0,
            "total_pnl_usd": 0.0
        }
    
    winning = [t for t in trades if t.get("pnl_usd", 0) > 0]
    stale = [t for t in trades if "stale" in (t.get("close_reason", "") or "").lower()]
    
    hold_times = []
    for t in trades:
        hold = t.get("hold_minutes") or t.get("context", {}).get("hold_minutes", 0)
        if hold:
            hold_times.append(float(hold))
    
    return {
        "total_trades": len(trades),
        "win_rate": len(winning) / len(trades) * 100 if trades else 0.0,
        "stale_exits": len(stale),
        "stale_exit_pct": len(stale) / len(trades) * 100 if trades else 0.0,
        "avg_hold_minutes": sum(hold_times) / len(hold_times) if hold_times else 0.0,
        "total_pnl_usd": sum(t.get("pnl_usd", 0) for t in trades)
    }

def load_backtest_report():
    """Load backtest report"""
    if not BACKTEST_REPORT.exists():
        return None
    
    with BACKTEST_REPORT.open("r") as f:
        return json.load(f)

def main():
    print("=" * 80)
    print("TODAY'S TRADES vs 7-DAY BACKTEST COMPARISON")
    print("=" * 80)
    
    # Load today's trades
    today_trades = load_today_trades()
    today_stats = analyze_trades(today_trades)
    
    print(f"\n📊 TODAY'S LIVE SESSION ({datetime.now(timezone.utc).date()}):")
    print(f"  Total Trades: {today_stats['total_trades']}")
    print(f"  Win Rate: {today_stats['win_rate']:.2f}%")
    print(f"  Stale Exits: {today_stats['stale_exits']} ({today_stats['stale_exit_pct']:.2f}%)")
    print(f"  Avg Hold Time: {today_stats['avg_hold_minutes']:.1f} minutes")
    print(f"  Total P&L: ${today_stats['total_pnl_usd']:.2f}")
    
    # Load backtest report
    backtest = load_backtest_report()
    if backtest:
        summary = backtest.get("backtest_summary", {})
        stale_analysis = backtest.get("stale_exit_analysis", {})
        
        print(f"\n📈 7-DAY BACKTEST BASELINE:")
        print(f"  Total Trades: {summary.get('total_trades', 0)}")
        print(f"  Win Rate: {summary.get('win_rate', '0.00%')}")
        print(f"  Stale Exits: {stale_analysis.get('stale_exits', 0)} ({stale_analysis.get('stale_exit_pct', 0.0):.2f}%)")
        print(f"  Avg Hold Time: {summary.get('avg_hold_minutes', 0.0):.1f} minutes")
        print(f"  Total P&L: {summary.get('total_pnl_usd', '$0.00')}")
        
        # Compare
        print(f"\n🔄 COMPARISON:")
        if today_stats['total_trades'] > 0:
            backtest_win_rate = float(summary.get('win_rate', '0.00%').replace('%', ''))
            win_rate_diff = today_stats['win_rate'] - backtest_win_rate
            print(f"  Win Rate Difference: {win_rate_diff:+.2f}% (Today vs Backtest)")
            
            stale_pct_diff = today_stats['stale_exit_pct'] - stale_analysis.get('stale_exit_pct', 0.0)
            print(f"  Stale Exit % Difference: {stale_pct_diff:+.2f}% (Today vs Backtest)")
            
            if abs(stale_pct_diff) > 10:
                print(f"  ⚠️  SIGNIFICANT DEVIATION: Stale exit rate differs by >10%")
            else:
                print(f"  ✅ Stale exit rate is consistent with backtest")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
