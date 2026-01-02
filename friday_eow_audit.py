#!/usr/bin/env python3
"""
Friday End-of-Week (EOW) Structural Audit - Specialist Tier Monitoring
Authoritative Source: MEMORY_BANK.md

Synthesizes full week of data with:
- Alpha Decay curves
- Stealth Flow effectiveness (100% win-rate target for Low Magnitude Flow)
- P&L impact of Temporal Liquidity Gate
- Greeks decay analysis (CEX/VEX)
- Capacity Efficiency stats (trades saved by displacement)

Output: reports/EOW_structural_audit_YYYY-MM-DD.md
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

# Base directory
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
STATE_DIR = BASE_DIR / "state"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# CRITICAL: Use standardized data path from config/registry.py
try:
    from config.registry import LogFiles
    ATTRIBUTION_LOG = LogFiles.ATTRIBUTION
    print(f"[EOW Audit] Using standardized path: {ATTRIBUTION_LOG}", file=sys.stderr)
except ImportError:
    # Fallback to local path if registry not available
    ATTRIBUTION_LOG = LOG_DIR / "attribution.jsonl"
    print(f"[EOW Audit] WARNING: Using fallback path: {ATTRIBUTION_LOG}", file=sys.stderr)

GATE_LOG = LOG_DIR / "gate.jsonl"
BLOCKED_TRADES_LOG = STATE_DIR / "blocked_trades.jsonl"
ORDERS_LOG = LOG_DIR / "orders.jsonl"
DISPLACEMENT_LOG = LOG_DIR / "displacement.jsonl" if (LOG_DIR / "displacement.jsonl").exists() else GATE_LOG


def fuzzy_search_attribution_log() -> List[Path]:
    """
    Fuzzy search for attribution.jsonl across all log directories.
    Returns list of candidate paths found.
    """
    candidates = []
    
    # Primary path (standardized)
    if ATTRIBUTION_LOG.exists():
        candidates.append(ATTRIBUTION_LOG)
    
    # Search common alternative locations
    search_paths = [
        BASE_DIR / "logs" / "attribution.jsonl",
        BASE_DIR / "data" / "attribution.jsonl",
        BASE_DIR / "state" / "attribution.jsonl",
        Path("logs") / "attribution.jsonl",
        Path("data") / "attribution.jsonl",
        Path(".") / "logs" / "attribution.jsonl",
    ]
    
    for path in search_paths:
        if path.exists() and path not in candidates:
            candidates.append(path)
    
    # Also search parent directories (in case script is run from subdirectory)
    for parent in [BASE_DIR.parent, BASE_DIR.parent.parent]:
        alt_path = parent / "logs" / "attribution.jsonl"
        if alt_path.exists() and alt_path not in candidates:
            candidates.append(alt_path)
    
    return candidates


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


def load_attribution_with_fuzzy_search() -> Tuple[List[Dict], Path]:
    """
    Load attribution log with fuzzy search fallback.
    Returns (records, actual_path_used)
    """
    # Try primary path first
    if ATTRIBUTION_LOG.exists():
        records = load_jsonl(ATTRIBUTION_LOG)
        if records:
            return records, ATTRIBUTION_LOG
    
    # Primary path empty or missing - try fuzzy search
    candidates = fuzzy_search_attribution_log()
    
    if candidates:
        # Use first candidate that has data
        for candidate_path in candidates:
            records = load_jsonl(candidate_path)
            if records:
                print(f"[EOW Audit] WARNING: Primary path empty, found data at: {candidate_path}", file=sys.stderr)
                print(f"[EOW Audit] Data source: {candidate_path} ({len(records)} records)", file=sys.stderr)
                return records, candidate_path
        # If we found paths but they're empty, report that
        if candidates:
            print(f"[EOW Audit] WARNING: Found attribution log files but all are empty:", file=sys.stderr)
            for c in candidates:
                print(f"  - {c}", file=sys.stderr)
            return [], candidates[0]  # Return empty list but indicate we found the path
    
    # No candidates found
    print(f"[EOW Audit] CRITICAL ERROR: Attribution log not found at primary path: {ATTRIBUTION_LOG}", file=sys.stderr)
    print(f"[EOW Audit] Searched paths:", file=sys.stderr)
    print(f"  - Primary: {ATTRIBUTION_LOG}", file=sys.stderr)
    for alt in [BASE_DIR / "logs" / "attribution.jsonl", BASE_DIR / "data" / "attribution.jsonl"]:
        print(f"  - Alternative: {alt} (exists: {alt.exists()})", file=sys.stderr)
    
    return [], ATTRIBUTION_LOG  # Return empty list with primary path for error reporting


def parse_timestamp(ts: Any) -> Optional[datetime]:
    """Parse various timestamp formats to datetime"""
    if ts is None:
        return None
    
    try:
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(float(ts), tz=timezone.utc)
        elif isinstance(ts, str):
            if 'T' in ts:
                return datetime.fromisoformat(ts.replace('Z', '+00:00'))
            return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    except Exception:
        pass
    
    return None


def get_week_trades(friday_date: datetime) -> Tuple[List[Dict], Path]:
    """
    Get all trades from Monday-Friday of the week.
    Returns (trades_list, data_source_path)
    """
    # Find Monday of the week
    days_since_monday = friday_date.weekday()
    monday = friday_date - timedelta(days=days_since_monday)
    monday_start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    saturday_start = monday_start + timedelta(days=5)
    
    # Use fuzzy search to find attribution log
    records, data_source_path = load_attribution_with_fuzzy_search()
    
    trades = []
    for record in records:
        if record.get("type") != "attribution":
            continue
        
        # CRITICAL: Support both flat schema (mandatory fields) and nested schema (backward compatibility)
        # Flat schema: symbol, entry_score, exit_pnl, market_regime, stealth_boost_applied at top level
        # Nested schema: fields in context dict
        
        # Extract entry timestamp - try multiple locations
        entry_ts_str = None
        context = record.get("context", {})
        
        # Try context first (nested schema)
        if isinstance(context, dict):
            entry_ts_str = context.get("entry_ts") or context.get("entry_timestamp")
        
        # Try top level (flat schema)
        if not entry_ts_str:
            entry_ts_str = record.get("entry_ts") or record.get("ts") or record.get("timestamp")
        
        entry_dt = parse_timestamp(entry_ts_str)
        
        if entry_dt and monday_start <= entry_dt < saturday_start:
            trades.append(record)
    
    return trades, data_source_path


def extract_trade_field(trade: Dict, field_name: str, default: Any = None) -> Any:
    """
    Extract field from trade record supporting both flat and nested schemas.
    Tries: top-level field -> context.field -> default
    """
    # Try top level first (flat schema)
    if field_name in trade:
        value = trade[field_name]
        if value is not None and value != "":
            return value
    
    # Try context dict (nested schema)
    context = trade.get("context", {})
    if isinstance(context, dict) and field_name in context:
        value = context[field_name]
        if value is not None and value != "":
            return value
    
    return default


def calculate_alpha_decay_curves(trades: List[Dict]) -> Dict[str, Any]:
    """
    Calculate Alpha Decay curves.
    Tracks P&L evolution over time after entry to identify optimal hold times.
    """
    # Bin trades by hold time (minutes)
    hold_time_bins = {
        "0-30": [],
        "30-60": [],
        "60-90": [],
        "90-120": [],
        "120-180": [],
        "180-240": [],
        "240+": []
    }
    
    for trade in trades:
        # Support both flat and nested schemas
        hold_minutes = extract_trade_field(trade, "hold_minutes", 0.0)
        pnl_pct = extract_trade_field(trade, "pnl_pct", 0.0) or extract_trade_field(trade, "exit_pnl", 0.0)
        
        if hold_minutes < 30:
            hold_time_bins["0-30"].append(pnl_pct)
        elif hold_minutes < 60:
            hold_time_bins["30-60"].append(pnl_pct)
        elif hold_minutes < 90:
            hold_time_bins["60-90"].append(pnl_pct)
        elif hold_minutes < 120:
            hold_time_bins["90-120"].append(pnl_pct)
        elif hold_minutes < 180:
            hold_time_bins["120-180"].append(pnl_pct)
        elif hold_minutes < 240:
            hold_time_bins["180-240"].append(pnl_pct)
        else:
            hold_time_bins["240+"].append(pnl_pct)
    
    # Calculate average P&L per bin
    decay_curve = {}
    for bin_name, pnl_list in hold_time_bins.items():
        if pnl_list:
            decay_curve[bin_name] = {
                "avg_pnl_pct": round(sum(pnl_list) / len(pnl_list), 4),
                "median_pnl_pct": round(sorted(pnl_list)[len(pnl_list) // 2], 4),
                "sample_count": len(pnl_list),
                "win_rate": round(sum(1 for p in pnl_list if p > 0) / len(pnl_list), 4)
            }
        else:
            decay_curve[bin_name] = {
                "avg_pnl_pct": 0.0,
                "median_pnl_pct": 0.0,
                "sample_count": 0,
                "win_rate": 0.0
            }
    
    # Find peak alpha (maximum average P&L)
    peak_bin = max(
        [(bin_name, stats["avg_pnl_pct"]) for bin_name, stats in decay_curve.items() if stats["sample_count"] > 0],
        key=lambda x: x[1],
        default=(None, 0.0)
    )
    
    # Find stale exit point (where P&L goes flat/negative)
    stale_bin = None
    for bin_name in ["0-30", "30-60", "60-90", "90-120", "120-180", "180-240", "240+"]:
        stats = decay_curve[bin_name]
        if stats["sample_count"] > 0 and stats["avg_pnl_pct"] <= 0:
            stale_bin = bin_name
            break
    
    return {
        "decay_curve": decay_curve,
        "peak_alpha_bin": peak_bin[0],
        "peak_alpha_pnl_pct": peak_bin[1],
        "stale_exit_bin": stale_bin,
        "total_trades_analyzed": sum(stats["sample_count"] for stats in decay_curve.values())
    }


def analyze_stealth_flow_effectiveness(trades: List[Dict]) -> Dict[str, Any]:
    """
    Analyze Stealth Flow (Low Magnitude Flow) effectiveness.
    Target: 100% win rate for flow_conv < 0.3
    
    CRITICAL: Supports both flat schema (stealth_boost_applied field) and nested schema (flow_conv check)
    """
    stealth_trades = []
    other_trades = []
    
    for trade in trades:
        # CRITICAL: Check stealth_boost_applied field first (flat schema)
        stealth_boost_applied = extract_trade_field(trade, "stealth_boost_applied", False)
        
        # Also check flow_magnitude from context (backward compatibility)
        flow_magnitude = extract_trade_field(trade, "flow_magnitude", "")
        context = trade.get("context", {})
        components = context.get("components", {}) if isinstance(context, dict) else {}
        
        # Determine if this is a stealth flow trade
        is_stealth = False
        if stealth_boost_applied:
            is_stealth = True
        elif flow_magnitude == "LOW":
            is_stealth = True
        else:
            # Fallback: Check flow_conv from components
            flow_comp = components.get("flow") or components.get("options_flow")
            if isinstance(flow_comp, dict):
                flow_conv = flow_comp.get("conviction", 0.0)
            elif isinstance(flow_comp, (int, float)):
                flow_conv = float(flow_comp)
            else:
                flow_conv = 0.0
            
            if flow_conv < 0.3:
                is_stealth = True
        
        # Extract P&L (support both flat and nested schema)
        pnl_pct = extract_trade_field(trade, "pnl_pct", 0.0) or extract_trade_field(trade, "exit_pnl", 0.0)
        
        if is_stealth:
            stealth_trades.append({
                "pnl_pct": pnl_pct,
                "symbol": extract_trade_field(trade, "symbol", ""),
                "win": pnl_pct > 0,
                "stealth_boost_applied": stealth_boost_applied
            })
        else:
            other_trades.append({
                "pnl_pct": pnl_pct,
                "symbol": extract_trade_field(trade, "symbol", ""),
                "win": pnl_pct > 0
            })
    
    # Calculate stealth flow stats
    stealth_wins = sum(1 for t in stealth_trades if t["win"])
    stealth_total = len(stealth_trades)
    stealth_win_rate = stealth_wins / stealth_total if stealth_total > 0 else 0.0
    stealth_avg_pnl = sum(t["pnl_pct"] for t in stealth_trades) / stealth_total if stealth_total > 0 else 0.0
    
    # Compare to other flow
    other_wins = sum(1 for t in other_trades if t["win"])
    other_total = len(other_trades)
    other_win_rate = other_wins / other_total if other_total > 0 else 0.0
    other_avg_pnl = sum(t["pnl_pct"] for t in other_trades) / other_total if other_total > 0 else 0.0
    
    return {
        "stealth_flow": {
            "trades": stealth_total,
            "wins": stealth_wins,
            "win_rate": round(stealth_win_rate, 4),
            "target_win_rate": 1.0,  # 100% target
            "meets_target": stealth_win_rate >= 1.0,
            "avg_pnl_pct": round(stealth_avg_pnl, 4),
            "avg_pnl_usd": round(
                sum(t.get("pnl_usd", 0.0) for t in stealth_trades) / stealth_total if stealth_total > 0 else 0.0,
                2
            )
        },
        "other_flow": {
            "trades": other_total,
            "wins": other_wins,
            "win_rate": round(other_win_rate, 4),
            "avg_pnl_pct": round(other_avg_pnl, 4)
        },
        "comparison": {
            "win_rate_advantage_pct": round((stealth_win_rate - other_win_rate) * 100, 2),
            "pnl_advantage_pct": round((stealth_avg_pnl - other_avg_pnl) * 100, 2)
        }
    }


def analyze_temporal_liquidity_gate_impact(trades: List[Dict], gates: List[Dict]) -> Dict[str, Any]:
    """
    Analyze P&L impact of Temporal Liquidity Gate.
    Identifies trades that were allowed vs blocked by liquidity/spread checks.
    """
    # Find liquidity-related gate blocks
    liquidity_blocked = []
    for gate_event in gates:
        msg = gate_event.get("msg", "").lower()
        if "spread" in msg or "liquidity" in msg or "illiquid" in msg:
            liquidity_blocked.append(gate_event)
    
    # Analyze executed trades for liquidity characteristics
    executed_liquidity_stats = []
    orders = load_jsonl(ORDERS_LOG)
    
    # Match trades to orders to get spread info
    for trade in trades:
        # Support both flat and nested schema
        symbol = extract_trade_field(trade, "symbol", "")
        context = trade.get("context", {}) if isinstance(trade.get("context"), dict) else {}
        entry_ts_str = extract_trade_field(trade, "entry_ts", None) or context.get("entry_ts")
        entry_dt = parse_timestamp(entry_ts_str)
        pnl_pct = extract_trade_field(trade, "pnl_pct", 0.0) or extract_trade_field(trade, "exit_pnl", 0.0)
        
        # Find matching order
        for order in orders:
            if order.get("symbol") == symbol:
                order_ts = parse_timestamp(order.get("ts") or order.get("timestamp") or order.get("_ts"))
                if order_ts and entry_dt and abs((order_ts - entry_dt).total_seconds()) < 300:  # Within 5 minutes
                    spread_bps = order.get("spread_bps") or order.get("spread")
                    if spread_bps:
                        executed_liquidity_stats.append({
                            "symbol": symbol,
                            "spread_bps": float(spread_bps),
                            "pnl_pct": pnl_pct,
                            "win": pnl_pct > 0
                        })
                    break
    
    if executed_liquidity_stats:
        avg_spread = sum(s["spread_bps"] for s in executed_liquidity_stats) / len(executed_liquidity_stats)
        avg_pnl = sum(s["pnl_pct"] for s in executed_liquidity_stats) / len(executed_liquidity_stats)
        win_rate = sum(1 for s in executed_liquidity_stats if s["win"]) / len(executed_liquidity_stats)
    else:
        avg_spread = 0.0
        avg_pnl = 0.0
        win_rate = 0.0
    
    return {
        "liquidity_gate_blocks": len(liquidity_blocked),
        "executed_trades_liquidity": {
            "sample_count": len(executed_liquidity_stats),
            "avg_spread_bps": round(avg_spread, 2),
            "avg_pnl_pct": round(avg_pnl, 4),
            "win_rate": round(win_rate, 4)
        },
        "gate_threshold_bps": 50.0,  # MAX_SPREAD_BPS from config
        "analysis": "Temporal Liquidity Gate prevents execution in illiquid names (>50 bps spread)"
    }


def analyze_greeks_decay(trades: List[Dict]) -> Dict[str, Any]:
    """
    Analyze Greeks decay (CEX/VEX - Call/Volatility Exposure).
    Tracks how gamma/delta exposure changes over position lifetime.
    """
    # This would ideally use real-time Greeks data, but we'll analyze based on entry/exit context
    # For now, analyze trades that mention gamma in exit reasons or context
    
    gamma_related_trades = []
    for trade in trades:
        context = trade.get("context", {})
        close_reason = context.get("close_reason", "").lower()
        components = context.get("components", {})
        
        # Check if gamma-related
        has_gamma = "gamma" in close_reason or "gamma" in str(components).lower()
        
        if has_gamma:
            pnl_pct = trade.get("pnl_pct", 0.0) or context.get("pnl_pct", 0.0)
            hold_minutes = context.get("hold_minutes", 0.0)
            gamma_related_trades.append({
                "pnl_pct": pnl_pct,
                "hold_minutes": hold_minutes,
                "close_reason": close_reason
            })
    
    if gamma_related_trades:
        avg_pnl = sum(t["pnl_pct"] for t in gamma_related_trades) / len(gamma_related_trades)
        avg_hold = sum(t["hold_minutes"] for t in gamma_related_trades) / len(gamma_related_trades)
    else:
        avg_pnl = 0.0
        avg_hold = 0.0
    
    return {
        "gamma_related_trades": len(gamma_related_trades),
        "avg_pnl_pct": round(avg_pnl, 4),
        "avg_hold_minutes": round(avg_hold, 1),
        "analysis": "Greeks decay analysis requires real-time gamma/delta tracking - tracked via structural exit recommendations",
        "note": "Full CEX/VEX analysis requires integration with structural_intelligence.structural_exit module"
    }


def analyze_capacity_efficiency(gates: List[Dict]) -> Dict[str, Any]:
    """
    Analyze Capacity Efficiency: trades saved by displacement.
    Tracks how many positions were displaced vs how many trades were blocked due to capacity limits.
    """
    displacement_successful = 0
    displacement_failed = 0
    max_positions_blocked = 0
    
    for gate_event in gates:
        msg = gate_event.get("msg", "").lower()
        
        if "displacement" in msg:
            if "successful" in msg or "displaced" in msg:
                displacement_successful += 1
            elif "failed" in msg:
                displacement_failed += 1
        
        if "max_positions" in msg or "capacity" in msg:
            max_positions_blocked += 1
    
    # Also check blocked_trades for displacement-related blocks
    blocked_trades = load_jsonl(BLOCKED_TRADES_LOG)
    displacement_blocked = sum(
        1 for bt in blocked_trades
        if "displacement" in bt.get("reason", "").lower()
    )
    
    total_capacity_saved = displacement_successful
    capacity_efficiency = displacement_successful / (displacement_successful + max_positions_blocked) if (displacement_successful + max_positions_blocked) > 0 else 0.0
    
    return {
        "displacement_successful": displacement_successful,
        "displacement_failed": displacement_failed,
        "max_positions_blocked": max_positions_blocked,
        "displacement_blocked_trades": displacement_blocked,
        "total_trades_saved_by_displacement": total_capacity_saved,
        "capacity_efficiency": round(capacity_efficiency, 4),
        "analysis": f"Displacement saved {total_capacity_saved} trades that would have been blocked by capacity limits"
    }


def analyze_opportunity_cost(blocked_trades: List[Dict], executed_trades: List[Dict]) -> Dict[str, Any]:
    """
    Analyze Opportunity Cost: high-score blocked signals vs actual P&L of occupying trades.
    """
    # Find high-score blocked trades (>= 5.0)
    high_score_blocked = [
        bt for bt in blocked_trades
        if bt.get("score", 0.0) >= 5.0
    ]
    
    # Calculate theoretical P&L for blocked trades (would need price simulation)
    # For now, just report counts and scores
    
    # Get P&L of executed trades for comparison
    executed_pnl = [extract_trade_field(t, "pnl_pct", 0.0) or extract_trade_field(t, "exit_pnl", 0.0) for t in executed_trades]
    avg_executed_pnl = sum(executed_pnl) / len(executed_pnl) if executed_pnl else 0.0
    
    return {
        "high_score_blocked_count": len(high_score_blocked),
        "high_score_blocked_avg_score": round(
            sum(bt.get("score", 0.0) for bt in high_score_blocked) / len(high_score_blocked) if high_score_blocked else 0.0,
            2
        ),
        "executed_trades_avg_pnl_pct": round(avg_executed_pnl, 4),
        "opportunity_cost_note": "Full opportunity cost requires counterfactual price simulation (see counterfactual_analyzer.py)",
        "high_score_blocked_reasons": {
            reason: sum(1 for bt in high_score_blocked if bt.get("reason") == reason)
            for reason in set(bt.get("reason", "unknown") for bt in high_score_blocked)
        }
    }


def generate_eow_audit(friday_date: Optional[datetime] = None) -> str:
    """
    Generate Friday EOW Structural Audit report in Markdown format.
    
    Args:
        friday_date: Friday date to analyze (defaults to today if Friday, otherwise last Friday)
    
    Returns:
        Markdown formatted report string
    """
    if friday_date is None:
        friday_date = datetime.now(timezone.utc)
    
    # Ensure we're analyzing a Friday
    days_since_friday = (friday_date.weekday() - 4) % 7
    if days_since_friday != 0:
        friday_date = friday_date - timedelta(days=days_since_friday)
    
    week_trades, data_source_path = get_week_trades(friday_date)
    
    # Report data source location
    if not week_trades:
        print(f"[EOW Audit] WARNING: No trades found for week ending {friday_date.strftime('%Y-%m-%d')}", file=sys.stderr)
        print(f"[EOW Audit] Data source path: {data_source_path} (exists: {data_source_path.exists() if hasattr(data_source_path, 'exists') else False})", file=sys.stderr)
    else:
        print(f"[EOW Audit] Found {len(week_trades)} trades from data source: {data_source_path}", file=sys.stderr)
    
    gates = load_jsonl(GATE_LOG)
    blocked_trades = load_jsonl(BLOCKED_TRADES_LOG)
    
    # Filter gates for this week
    monday = friday_date - timedelta(days=friday_date.weekday())
    monday_start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    saturday_start = monday_start + timedelta(days=5)
    
    week_gates = [
        g for g in gates
        if parse_timestamp(g.get("ts") or g.get("timestamp") or g.get("_ts"))
        and monday_start <= parse_timestamp(g.get("ts") or g.get("timestamp") or g.get("_ts")) < saturday_start
    ]
    
    # Perform analyses
    alpha_decay = calculate_alpha_decay_curves(week_trades)
    stealth_flow = analyze_stealth_flow_effectiveness(week_trades)
    liquidity_gate = analyze_temporal_liquidity_gate_impact(week_trades, week_gates)
    greeks_decay = analyze_greeks_decay(week_trades)
    capacity_efficiency = analyze_capacity_efficiency(week_gates)
    opportunity_cost = analyze_opportunity_cost(blocked_trades, week_trades)
    
    # Overall week stats (support both flat and nested schema)
    total_trades = len(week_trades)
    total_wins = sum(1 for t in week_trades if (extract_trade_field(t, "pnl_pct", 0.0) or extract_trade_field(t, "exit_pnl", 0.0)) > 0)
    total_pnl_usd = sum(extract_trade_field(t, "pnl_usd", 0.0) for t in week_trades)
    total_pnl_pct = sum(extract_trade_field(t, "pnl_pct", 0.0) or extract_trade_field(t, "exit_pnl", 0.0) for t in week_trades)
    
    # Generate Markdown report
    report_lines = [
        "# Friday End-of-Week (EOW) Structural Audit",
        "",
        f"**Week Ending:** {friday_date.strftime('%Y-%m-%d')}",
        f"**Report Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Authoritative Source:** MEMORY_BANK.md",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"- **Total Trades:** {total_trades}",
        f"- **Win Rate:** {total_wins/total_trades:.2%}" if total_trades > 0 else "- **Win Rate:** N/A",
        f"- **Total P&L:** ${total_pnl_usd:,.2f} ({total_pnl_pct:.2%})",
        "",
        "---",
        "",
        "## 1. Alpha Decay Curves",
        "",
        "P&L evolution over position lifetime to identify optimal hold times:",
        "",
        "| Hold Time (min) | Avg P&L % | Median P&L % | Win Rate | Sample Count |",
        "|-----------------|-----------|--------------|----------|--------------|"
    ]
    
    for bin_name in ["0-30", "30-60", "60-90", "90-120", "120-180", "180-240", "240+"]:
        stats = alpha_decay["decay_curve"][bin_name]
        report_lines.append(
            f"| {bin_name} | {stats['avg_pnl_pct']:.2%} | {stats['median_pnl_pct']:.2%} | "
            f"{stats['win_rate']:.2%} | {stats['sample_count']} |"
        )
    
    report_lines.extend([
        "",
        f"**Peak Alpha:** {alpha_decay['peak_alpha_bin']} ({alpha_decay['peak_alpha_pnl_pct']:.2%})",
        f"**Stale Exit Point:** {alpha_decay['stale_exit_bin'] or 'Not identified'}",
        "",
        "---",
        "",
        "## 2. Stealth Flow Effectiveness",
        "",
        "**Target:** 100% win rate for Low Magnitude Flow (flow_conv < 0.3)",
        "",
        f"| Metric | Stealth Flow | Other Flow | Advantage |",
        "|--------|--------------|------------|-----------|",
        f"| Trades | {stealth_flow['stealth_flow']['trades']} | {stealth_flow['other_flow']['trades']} | - |",
        f"| Win Rate | {stealth_flow['stealth_flow']['win_rate']:.2%} | {stealth_flow['other_flow']['win_rate']:.2%} | "
        f"{stealth_flow['comparison']['win_rate_advantage_pct']:+.2f}pp |",
        f"| Avg P&L % | {stealth_flow['stealth_flow']['avg_pnl_pct']:.2%} | {stealth_flow['other_flow']['avg_pnl_pct']:.2%} | "
        f"{stealth_flow['comparison']['pnl_advantage_pct']:+.2f}pp |",
        "",
        f"**Meets Target (100% win rate):** {'✅ YES' if stealth_flow['stealth_flow']['meets_target'] else '❌ NO'}",
        "",
        "---",
        "",
        "## 3. Temporal Liquidity Gate Impact",
        "",
        f"**Gate Threshold:** {liquidity_gate['gate_threshold_bps']} bps",
        f"**Trades Blocked:** {liquidity_gate['liquidity_gate_blocks']}",
        f"**Executed Trades (Liquidity Stats):**",
        f"- Sample Count: {liquidity_gate['executed_trades_liquidity']['sample_count']}",
        f"- Avg Spread: {liquidity_gate['executed_trades_liquidity']['avg_spread_bps']:.2f} bps",
        f"- Avg P&L: {liquidity_gate['executed_trades_liquidity']['avg_pnl_pct']:.2%}",
        f"- Win Rate: {liquidity_gate['executed_trades_liquidity']['win_rate']:.2%}",
        "",
        "---",
        "",
        "## 4. Greeks Decay Analysis (CEX/VEX)",
        "",
        f"**Gamma-Related Trades:** {greeks_decay['gamma_related_trades']}",
        f"**Avg P&L:** {greeks_decay['avg_pnl_pct']:.2%}",
        f"**Avg Hold Time:** {greeks_decay['avg_hold_minutes']:.1f} minutes",
        "",
        f"*Note:* {greeks_decay['note']}",
        "",
        "---",
        "",
        "## 5. Capacity Efficiency",
        "",
        f"**Displacement Successful:** {capacity_efficiency['displacement_successful']}",
        f"**Displacement Failed:** {capacity_efficiency['displacement_failed']}",
        f"**Max Positions Blocked:** {capacity_efficiency['max_positions_blocked']}",
        f"**Total Trades Saved by Displacement:** {capacity_efficiency['total_trades_saved_by_displacement']}",
        f"**Capacity Efficiency:** {capacity_efficiency['capacity_efficiency']:.2%}",
        "",
        f"**Analysis:** {capacity_efficiency['analysis']}",
        "",
        "---",
        "",
        "## 6. Opportunity Cost Analysis",
        "",
        f"**High-Score Blocked Trades (>= 5.0):** {opportunity_cost['high_score_blocked_count']}",
        f"**Avg Score (Blocked):** {opportunity_cost['high_score_blocked_avg_score']:.2f}",
        f"**Avg P&L (Executed):** {opportunity_cost['executed_trades_avg_pnl_pct']:.2%}",
        "",
        "**Blocking Reasons (High-Score):**",
        ""
    ])
    
    for reason, count in opportunity_cost['high_score_blocked_reasons'].items():
        report_lines.append(f"- {reason}: {count}")
    
    report_lines.extend([
        "",
        f"*Note:* {opportunity_cost['opportunity_cost_note']}",
        "",
        "---",
        "",
        "## Recommendations",
        "",
        "Based on this week's analysis:",
        "",
        "1. **Alpha Decay:** " + (
            f"Peak alpha at {alpha_decay['peak_alpha_bin']} - consider tightening exits"
            if alpha_decay['stale_exit_bin'] else "Monitor decay patterns"
        ),
        "",
        "2. **Stealth Flow:** " + (
            "✅ Meeting 100% win rate target - maintain +0.2 boost"
            if stealth_flow['stealth_flow']['meets_target']
            else f"❌ Not meeting target ({stealth_flow['stealth_flow']['win_rate']:.2%}) - review boost logic"
        ),
        "",
        "3. **Liquidity Gate:** " + (
            f"Gate blocking {liquidity_gate['liquidity_gate_blocks']} trades - verify threshold effectiveness"
            if liquidity_gate['liquidity_gate_blocks'] > 0
            else "No liquidity blocks - gate threshold appropriate"
        ),
        "",
        "4. **Capacity:** " + (
            f"Displacement saving {capacity_efficiency['total_trades_saved_by_displacement']} trades - effective"
            if capacity_efficiency['total_trades_saved_by_displacement'] > 0
            else "No displacement activity - capacity not constrained"
        ),
        "",
        "---",
        "",
        f"*Report generated by friday_eow_audit.py*",
        f"*Reference: MEMORY_BANK.md - Specialist Tier Monitoring*"
    ])
    
    return "\n".join(report_lines)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Friday EOW Structural Audit Report")
    parser.add_argument("--date", type=str, help="Friday date to analyze (YYYY-MM-DD), defaults to today/last Friday")
    parser.add_argument("--output", type=str, help="Output file path (defaults to reports/EOW_structural_audit_YYYY-MM-DD.md)")
    
    args = parser.parse_args()
    
    # Parse target date
    friday_date = None
    if args.date:
        try:
            friday_date = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"Invalid date format: {args.date}. Use YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)
    
    # Generate report
    report_markdown = generate_eow_audit(friday_date)
    
    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        # Use Friday date for filename
        if friday_date is None:
            today = datetime.now(timezone.utc)
            days_since_friday = (today.weekday() - 4) % 7
            friday_date = today - timedelta(days=days_since_friday)
        report_date = friday_date.strftime("%Y-%m-%d")
        output_file = REPORTS_DIR / f"EOW_structural_audit_{report_date}.md"
    
    # Write report
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_markdown)
    
    print(f"Friday EOW Structural Audit written to: {output_file}")
    print(f"Report length: {len(report_markdown)} characters")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
