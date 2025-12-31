#!/usr/bin/env python3
"""
Daily Alpha Audit - Specialist Tier Monitoring
Authoritative Source: MEMORY_BANK.md

Generates daily performance reports (Mon-Thu post-market close) with:
- Win rates for RISK_ON vs MIXED regimes
- Today's stats vs weekly average comparison
- VWAP Deviation metrics
- Momentum Lead-Time metrics

Output: reports/daily_alpha_audit_YYYY-MM-DD.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Base directory
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Data files
ATTRIBUTION_LOG = LOG_DIR / "attribution.jsonl"
GATE_LOG = LOG_DIR / "gate.jsonl"
ORDERS_LOG = LOG_DIR / "orders.jsonl"
BLOCKED_TRADES_LOG = BASE_DIR / "state" / "blocked_trades.jsonl"


def load_jsonl(file_path: Path) -> List[Dict]:
    """Load JSONL file and return list of records"""
    if not file_path.exists():
        return []
    
    records = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"Error loading {file_path}: {e}", file=sys.stderr)
    
    return records


def parse_timestamp(ts: Any) -> Optional[datetime]:
    """Parse various timestamp formats to datetime"""
    if ts is None:
        return None
    
    try:
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(float(ts), tz=timezone.utc)
        elif isinstance(ts, str):
            # Try ISO format
            if 'T' in ts:
                return datetime.fromisoformat(ts.replace('Z', '+00:00'))
            # Try timestamp string
            return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    except Exception:
        pass
    
    return None


def get_today_trades(date: datetime) -> List[Dict]:
    """Get all trades from today (attribution.jsonl)"""
    today_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    trades = []
    for record in load_jsonl(ATTRIBUTION_LOG):
        if record.get("type") != "attribution":
            continue
        
        context = record.get("context", {})
        entry_ts_str = context.get("entry_ts") or record.get("ts") or record.get("timestamp")
        entry_dt = parse_timestamp(entry_ts_str)
        
        if entry_dt and today_start <= entry_dt < today_end:
            trades.append(record)
    
    return trades


def get_weekly_trades(date: datetime) -> List[Dict]:
    """Get all trades from the past 7 days"""
    week_start = date.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
    
    trades = []
    for record in load_jsonl(ATTRIBUTION_LOG):
        if record.get("type") != "attribution":
            continue
        
        context = record.get("context", {})
        entry_ts_str = context.get("entry_ts") or record.get("ts") or record.get("timestamp")
        entry_dt = parse_timestamp(entry_ts_str)
        
        if entry_dt and entry_dt >= week_start:
            trades.append(record)
    
    return trades


def calculate_vwap_deviation(trades: List[Dict]) -> Dict[str, Any]:
    """
    Calculate VWAP deviation metrics.
    VWAP Deviation = (Entry Price - VWAP) / VWAP * 100
    """
    if not trades:
        return {
            "avg_deviation_pct": 0.0,
            "median_deviation_pct": 0.0,
            "positive_deviations": 0,
            "negative_deviations": 0,
            "sample_count": 0
        }
    
    deviations = []
    positive_count = 0
    negative_count = 0
    
    # Group trades by symbol and hour for VWAP calculation
    symbol_hour_trades: Dict[str, Dict[str, List[Dict]]] = defaultdict(lambda: defaultdict(list))
    
    for trade in trades:
        context = trade.get("context", {})
        symbol = trade.get("symbol", "")
        entry_price = context.get("entry_price", 0.0)
        entry_ts_str = context.get("entry_ts") or trade.get("ts") or trade.get("timestamp")
        entry_dt = parse_timestamp(entry_ts_str)
        
        if not symbol or not entry_price or not entry_dt:
            continue
        
        hour_key = entry_dt.strftime("%Y-%m-%d-%H")
        symbol_hour_trades[symbol][hour_key].append({
            "price": entry_price,
            "qty": context.get("qty", 1),
            "trade": trade
        })
    
    # Calculate VWAP per symbol-hour and deviation
    for symbol, hour_trades in symbol_hour_trades.items():
        for hour_key, trades_list in hour_trades.items():
            if not trades_list:
                continue
            
            # Calculate VWAP for this symbol-hour
            total_value = sum(t["price"] * t["qty"] for t in trades_list)
            total_volume = sum(t["qty"] for t in trades_list)
            vwap = total_value / total_volume if total_volume > 0 else 0.0
            
            if vwap <= 0:
                continue
            
            # Calculate deviation for each trade in this hour
            for trade_data in trades_list:
                entry_price = trade_data["price"]
                deviation_pct = ((entry_price - vwap) / vwap) * 100.0
                deviations.append(deviation_pct)
                
                if deviation_pct > 0:
                    positive_count += 1
                elif deviation_pct < 0:
                    negative_count += 1
    
    if not deviations:
        return {
            "avg_deviation_pct": 0.0,
            "median_deviation_pct": 0.0,
            "positive_deviations": 0,
            "negative_deviations": 0,
            "sample_count": 0
        }
    
    deviations.sort()
    median = deviations[len(deviations) // 2] if deviations else 0.0
    
    return {
        "avg_deviation_pct": round(sum(deviations) / len(deviations), 4),
        "median_deviation_pct": round(median, 4),
        "positive_deviations": positive_count,
        "negative_deviations": negative_count,
        "sample_count": len(deviations),
        "std_deviation_pct": round(
            (sum((d - sum(deviations)/len(deviations))**2 for d in deviations) / len(deviations))**0.5,
            4
        ) if deviations else 0.0
    }


def calculate_momentum_lead_time(trades: List[Dict], orders: List[Dict]) -> Dict[str, Any]:
    """
    Calculate Momentum Lead-Time metrics.
    Lead-Time = Time between signal generation and trade execution
    """
    # Build order timestamp map by symbol
    order_times: Dict[str, List[datetime]] = defaultdict(list)
    
    for order in orders:
        symbol = order.get("symbol", "")
        order_ts = parse_timestamp(order.get("ts") or order.get("timestamp") or order.get("_ts"))
        if symbol and order_ts:
            order_times[symbol].append(order_ts)
    
    # Build signal generation times from trades (use entry_ts as proxy for signal time)
    lead_times = []
    
    for trade in trades:
        context = trade.get("context", {})
        symbol = trade.get("symbol", "")
        entry_ts_str = context.get("entry_ts")
        entry_dt = parse_timestamp(entry_ts_str)
        
        if not symbol or not entry_dt:
            continue
        
        # Find closest order time (execution time)
        if symbol in order_times:
            closest_order_time = None
            min_diff = float('inf')
            
            for order_time in order_times[symbol]:
                diff = abs((order_time - entry_dt).total_seconds())
                if diff < min_diff and order_time >= entry_dt:
                    min_diff = diff
                    closest_order_time = order_time
            
            if closest_order_time:
                lead_time_seconds = (closest_order_time - entry_dt).total_seconds()
                if lead_time_seconds >= 0:  # Only count positive lead times
                    lead_times.append(lead_time_seconds)
    
    if not lead_times:
        return {
            "avg_lead_time_seconds": 0.0,
            "median_lead_time_seconds": 0.0,
            "min_lead_time_seconds": 0.0,
            "max_lead_time_seconds": 0.0,
            "sample_count": 0
        }
    
    lead_times.sort()
    
    return {
        "avg_lead_time_seconds": round(sum(lead_times) / len(lead_times), 2),
        "median_lead_time_seconds": round(lead_times[len(lead_times) // 2], 2),
        "min_lead_time_seconds": round(min(lead_times), 2),
        "max_lead_time_seconds": round(max(lead_times), 2),
        "sample_count": len(lead_times)
    }


def analyze_regime_performance(trades: List[Dict]) -> Dict[str, Dict[str, Any]]:
    """Analyze performance by market regime"""
    regime_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "trades": 0,
        "wins": 0,
        "losses": 0,
        "total_pnl_usd": 0.0,
        "total_pnl_pct": 0.0,
        "avg_pnl_pct": 0.0,
        "avg_hold_minutes": 0.0
    })
    
    for trade in trades:
        context = trade.get("context", {})
        regime = context.get("market_regime", "UNKNOWN").upper()
        
        pnl_pct = trade.get("pnl_pct", 0.0) or context.get("pnl_pct", 0.0)
        pnl_usd = trade.get("pnl_usd", 0.0) or context.get("pnl_usd", 0.0)
        hold_minutes = context.get("hold_minutes", 0.0)
        
        stats = regime_stats[regime]
        stats["trades"] += 1
        stats["total_pnl_usd"] += pnl_usd
        stats["total_pnl_pct"] += pnl_pct
        stats["avg_hold_minutes"] += hold_minutes
        
        if pnl_pct > 0:
            stats["wins"] += 1
        elif pnl_pct < 0:
            stats["losses"] += 1
    
    # Calculate averages and win rates
    result = {}
    for regime, stats in regime_stats.items():
        trades_count = stats["trades"]
        if trades_count == 0:
            continue
        
        result[regime] = {
            "trades": trades_count,
            "wins": stats["wins"],
            "losses": stats["losses"],
            "win_rate": round(stats["wins"] / trades_count, 4) if trades_count > 0 else 0.0,
            "total_pnl_usd": round(stats["total_pnl_usd"], 2),
            "total_pnl_pct": round(stats["total_pnl_pct"], 4),
            "avg_pnl_pct": round(stats["total_pnl_pct"] / trades_count, 4) if trades_count > 0 else 0.0,
            "avg_pnl_usd": round(stats["total_pnl_usd"] / trades_count, 2) if trades_count > 0 else 0.0,
            "avg_hold_minutes": round(stats["avg_hold_minutes"] / trades_count, 1) if trades_count > 0 else 0.0
        }
    
    return result


def calculate_liquidity_metrics(trades: List[Dict], orders: List[Dict]) -> Dict[str, Any]:
    """Calculate liquidity metrics: bid/ask spread width at entry vs historical hour averages"""
    # Group orders by hour
    hour_spreads: Dict[str, List[float]] = defaultdict(list)
    
    for order in orders:
        spread_bps = order.get("spread_bps") or order.get("spread")
        if spread_bps is None:
            continue
        
        order_ts = parse_timestamp(order.get("ts") or order.get("timestamp") or order.get("_ts"))
        if order_ts:
            hour_key = order_ts.strftime("%Y-%m-%d-%H")
            hour_spreads[hour_key].append(float(spread_bps))
    
    # Calculate historical hour averages
    hour_avg_spreads = {
        hour: sum(spreads) / len(spreads)
        for hour, spreads in hour_spreads.items()
        if spreads
    }
    
    # Match trades to their entry spreads
    trade_spreads = []
    for trade in trades:
        context = trade.get("context", {})
        entry_ts_str = context.get("entry_ts")
        entry_dt = parse_timestamp(entry_ts_str)
        symbol = trade.get("symbol", "")
        
        if entry_dt:
            hour_key = entry_dt.strftime("%Y-%m-%d-%H")
            if hour_key in hour_avg_spreads:
                # Find actual spread for this trade from orders
                for order in orders:
                    if order.get("symbol") == symbol:
                        order_ts = parse_timestamp(order.get("ts") or order.get("timestamp") or order.get("_ts"))
                        if order_ts and abs((order_ts - entry_dt).total_seconds()) < 60:  # Within 1 minute
                            spread = order.get("spread_bps") or order.get("spread")
                            if spread:
                                trade_spreads.append({
                                    "spread_bps": float(spread),
                                    "hour_avg_bps": hour_avg_spreads[hour_key],
                                    "deviation_from_avg": float(spread) - hour_avg_spreads[hour_key]
                                })
                                break
    
    if not trade_spreads:
        return {
            "avg_spread_bps": 0.0,
            "avg_hour_spread_bps": 0.0,
            "avg_deviation_from_hour_avg": 0.0,
            "sample_count": 0
        }
    
    return {
        "avg_spread_bps": round(sum(t["spread_bps"] for t in trade_spreads) / len(trade_spreads), 2),
        "avg_hour_spread_bps": round(sum(t["hour_avg_bps"] for t in trade_spreads) / len(trade_spreads), 2),
        "avg_deviation_from_hour_avg": round(
            sum(t["deviation_from_avg"] for t in trade_spreads) / len(trade_spreads),
            2
        ),
        "sample_count": len(trade_spreads)
    }


def generate_daily_alpha_audit(target_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Generate daily alpha audit report.
    
    Args:
        target_date: Date to analyze (defaults to today)
    
    Returns:
        Dictionary with audit results
    """
    if target_date is None:
        target_date = datetime.now(timezone.utc)
    
    # Ensure we're analyzing a weekday (Mon-Fri)
    day_of_week = target_date.weekday()
    if day_of_week >= 5:  # Saturday or Sunday
        # Use last Friday instead
        days_back = day_of_week - 4
        target_date = target_date - timedelta(days=days_back)
    
    today_trades = get_today_trades(target_date)
    weekly_trades = get_weekly_trades(target_date)
    orders = load_jsonl(ORDERS_LOG)
    
    # Today's regime performance
    today_regime_perf = analyze_regime_performance(today_trades)
    
    # Weekly regime performance (for comparison)
    weekly_regime_perf = analyze_regime_performance(weekly_trades)
    
    # Calculate weekly averages
    weekly_avg_win_rate = {}
    for regime, stats in weekly_regime_perf.items():
        if stats["trades"] > 0:
            weekly_avg_win_rate[regime] = stats["win_rate"]
    
    # Today vs Weekly comparison
    regime_comparison = {}
    for regime in set(list(today_regime_perf.keys()) + list(weekly_avg_win_rate.keys())):
        today_stats = today_regime_perf.get(regime, {})
        weekly_avg = weekly_avg_win_rate.get(regime, 0.0)
        today_wr = today_stats.get("win_rate", 0.0)
        
        regime_comparison[regime] = {
            "today_win_rate": today_wr,
            "weekly_avg_win_rate": weekly_avg,
            "divergence_pct": round((today_wr - weekly_avg) * 100, 2) if weekly_avg > 0 else 0.0,
            "today_trades": today_stats.get("trades", 0),
            "today_avg_pnl_pct": today_stats.get("avg_pnl_pct", 0.0)
        }
    
    # VWAP Deviation
    vwap_deviation = calculate_vwap_deviation(today_trades)
    
    # Momentum Lead-Time
    momentum_lead_time = calculate_momentum_lead_time(today_trades, orders)
    
    # Liquidity Metrics
    liquidity_metrics = calculate_liquidity_metrics(today_trades, orders)
    
    # Overall today stats
    total_trades = len(today_trades)
    total_wins = sum(1 for t in today_trades if (t.get("pnl_pct", 0.0) or t.get("context", {}).get("pnl_pct", 0.0)) > 0)
    total_losses = sum(1 for t in today_trades if (t.get("pnl_pct", 0.0) or t.get("context", {}).get("pnl_pct", 0.0)) < 0)
    total_pnl_usd = sum(t.get("pnl_usd", 0.0) or t.get("context", {}).get("pnl_usd", 0.0) for t in today_trades)
    total_pnl_pct = sum(t.get("pnl_pct", 0.0) or t.get("context", {}).get("pnl_pct", 0.0) for t in today_trades)
    
    report = {
        "report_date": target_date.strftime("%Y-%m-%d"),
        "report_timestamp": datetime.now(timezone.utc).isoformat(),
        "report_type": "daily_alpha_audit",
        "authoritative_source": "MEMORY_BANK.md",
        
        "today_summary": {
            "total_trades": total_trades,
            "total_wins": total_wins,
            "total_losses": total_losses,
            "win_rate": round(total_wins / total_trades, 4) if total_trades > 0 else 0.0,
            "total_pnl_usd": round(total_pnl_usd, 2),
            "total_pnl_pct": round(total_pnl_pct, 4),
            "avg_pnl_pct": round(total_pnl_pct / total_trades, 4) if total_trades > 0 else 0.0
        },
        
        "regime_performance": {
            "today": today_regime_perf,
            "weekly_average": weekly_avg_win_rate,
            "comparison": regime_comparison
        },
        
        "vwap_deviation": vwap_deviation,
        "momentum_lead_time": momentum_lead_time,
        "liquidity_metrics": liquidity_metrics,
        
        "data_quality": {
            "today_trades_analyzed": total_trades,
            "weekly_trades_analyzed": len(weekly_trades),
            "orders_analyzed": len(orders)
        }
    }
    
    return report


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Daily Alpha Audit Report")
    parser.add_argument("--date", type=str, help="Date to analyze (YYYY-MM-DD), defaults to today")
    parser.add_argument("--output", type=str, help="Output file path (defaults to reports/daily_alpha_audit_YYYY-MM-DD.json)")
    
    args = parser.parse_args()
    
    # Parse target date
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"Invalid date format: {args.date}. Use YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)
    
    # Generate report
    report = generate_daily_alpha_audit(target_date)
    
    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        report_date = report["report_date"]
        output_file = REPORTS_DIR / f"daily_alpha_audit_{report_date}.json"
    
    # Write report
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"Daily Alpha Audit report written to: {output_file}")
    print(f"Date: {report['report_date']}")
    print(f"Total Trades: {report['today_summary']['total_trades']}")
    print(f"Win Rate: {report['today_summary']['win_rate']:.2%}")
    print(f"Total P&L: ${report['today_summary']['total_pnl_usd']:.2f} ({report['today_summary']['total_pnl_pct']:.2%})")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
