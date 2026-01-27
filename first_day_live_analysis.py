#!/usr/bin/env python3
"""
First-Day Live Trading Analysis
================================
Institutional-grade post-trade analysis for STOCK-BOT's first live trading day.

This script runs DIRECTLY ON THE DROPLET and produces:
- Comprehensive CSV exports for deeper analysis
- Human-readable markdown summary report
- What-if scenario analysis
- Signal, UW, and regime effectiveness analysis

Usage:
    python first_day_live_analysis.py --date 2026-01-27
"""

import json
import csv
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict
import statistics

# Try to import droplet client, but work locally if not available
try:
    from report_data_fetcher import ReportDataFetcher
    HAS_DROPLET_CLIENT = True
except ImportError:
    HAS_DROPLET_CLIENT = False

# Directories
REPORTS_DIR = Path("reports")
EXPORTS_DIR = Path("exports")
REPORTS_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)

# Droplet paths (if running on droplet)
DROPLET_BASE = Path("/root/stock-bot") if Path("/root/stock-bot").exists() else Path(".")
DROPLET_LOGS = DROPLET_BASE / "logs"
DROPLET_STATE = DROPLET_BASE / "state"
DROPLET_DATA = DROPLET_BASE / "data"

# Log files
LOG_FILES = {
    "run": DROPLET_LOGS / "run.jsonl",
    "orders": DROPLET_LOGS / "orders.jsonl",
    "exit": DROPLET_LOGS / "exit.jsonl",
    "system_events": DROPLET_LOGS / "system_events.jsonl",
    "scoring_flow": DROPLET_LOGS / "scoring_flow.jsonl",
    "shadow": DROPLET_LOGS / "shadow.jsonl",
    "attribution": DROPLET_LOGS / "attribution.jsonl",
    "signals": DROPLET_LOGS / "signals.jsonl",
    "gate": DROPLET_LOGS / "gate.jsonl",
}

# State files
STATE_FILES = {
    "market_context_v2": DROPLET_STATE / "market_context_v2.json",
    "regime_posture_state": DROPLET_STATE / "regime_posture_state.json",
    "symbol_risk_features": DROPLET_STATE / "symbol_risk_features.json",
    "trade_universe_v2": DROPLET_STATE / "trade_universe_v2.json",
    "shadow_positions": DROPLET_STATE / "shadow_positions.json",
    "uw_congress_trades": DROPLET_STATE / "uw_congress_trades.json",
    "uw_earnings_calendar": DROPLET_STATE / "uw_earnings_calendar.json",
    "uw_insider_trades": DROPLET_STATE / "uw_insider_trades.json",
    "uw_flow_intraday": DROPLET_STATE / "uw_flow_intraday.json",
    "uw_dark_pool_intraday": DROPLET_STATE / "uw_dark_pool_intraday.json",
}


def parse_timestamp(ts_val: Any) -> Optional[datetime]:
    """Parse various timestamp formats"""
    if not ts_val:
        return None
    try:
        if isinstance(ts_val, (int, float)):
            return datetime.fromtimestamp(ts_val, tz=timezone.utc)
        if isinstance(ts_val, str):
            ts_val = ts_val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(ts_val)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
    except:
        pass
    return None


def load_jsonl(file_path: Path, target_date: datetime) -> List[Dict]:
    """Load and filter JSONL file for target date"""
    records = []
    if not file_path.exists():
        return records
    
    target_date_str = target_date.date().isoformat()
    
    try:
        with file_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    
                    # Try to find timestamp
                    dt = None
                    for ts_field in ["ts", "timestamp", "_ts", "_dt", "entry_ts", "exit_ts", "time"]:
                        ts_val = rec.get(ts_field)
                        if ts_val:
                            dt = parse_timestamp(ts_val)
                            if dt:
                                break
                    
                    # Also check context
                    if not dt and "context" in rec:
                        ctx = rec.get("context", {})
                        for ts_field in ["ts", "timestamp", "entry_ts", "exit_ts"]:
                            ts_val = ctx.get(ts_field)
                            if ts_val:
                                dt = parse_timestamp(ts_val)
                                if dt:
                                    break
                    
                    # Filter by date
                    if dt and dt.date() == target_date.date():
                        rec["_parsed_timestamp"] = dt
                        records.append(rec)
                    # Also include records without timestamp if we're looking for today
                    elif not dt and target_date.date() == datetime.now(timezone.utc).date():
                        records.append(rec)
                        
                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue
    except Exception as e:
        print(f"[WARN] Failed to load {file_path}: {e}", file=sys.stderr)
    
    return records


def load_json_state(file_path: Path) -> Dict:
    """Load JSON state file"""
    if not file_path.exists():
        return {}
    try:
        return json.loads(file_path.read_text())
    except:
        return {}


def get_market_hours(target_date: datetime) -> tuple[datetime, datetime]:
    """Get market open and close times for a date (ET timezone)"""
    # Market opens at 9:30 AM ET, closes at 4:00 PM ET
    # Convert to UTC (ET is UTC-5 in winter, UTC-4 in summer)
    # For simplicity, assume UTC-5 (EST)
    market_open_et = target_date.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close_et = target_date.replace(hour=16, minute=0, second=0, microsecond=0)
    
    # Convert ET to UTC (add 5 hours for EST)
    market_open_utc = market_open_et.replace(tzinfo=timezone(timedelta(hours=-5)))
    market_close_utc = market_close_et.replace(tzinfo=timezone(timedelta(hours=-5)))
    
    return market_open_utc.astimezone(timezone.utc), market_close_utc.astimezone(timezone.utc)


def build_real_trades_dataset(attribution_log: List[Dict], orders_log: List[Dict], 
                              exit_log: List[Dict], target_date: datetime) -> List[Dict]:
    """Build canonical real trades dataset"""
    trades = []
    
    # Group attribution records by trade_id
    trades_by_id = defaultdict(dict)
    for rec in attribution_log:
        if rec.get("type") != "attribution":
            continue
        trade_id = rec.get("trade_id", "")
        if not trade_id or trade_id.startswith("open_"):
            continue
        
        symbol = rec.get("symbol", "")
        if not symbol:
            continue
        
        # Parse entry time
        entry_time = rec.get("_parsed_timestamp")
        if not entry_time:
            # Try to parse from ts or timestamp field
            entry_time = parse_timestamp(rec.get("ts") or rec.get("timestamp"))
        
        if trade_id not in trades_by_id:
            trades_by_id[trade_id] = {
                "symbol": symbol,
                "trade_id": trade_id,
            }
        
        # Update with attribution data
        trades_by_id[trade_id].update({
            "realized_pnl": float(rec.get("pnl_usd", 0)),
            "realized_pnl_pct": float(rec.get("pnl_pct", 0)),
            "entry_time": entry_time,
            "entry_score": rec.get("context", {}).get("entry_score", 0.0),
            "regime_at_entry": rec.get("context", {}).get("market_regime", "UNKNOWN"),
            "close_reason": rec.get("context", {}).get("close_reason", "UNKNOWN"),
        })
    
    # Enrich with order data
    orders_by_symbol = defaultdict(list)
    for order in orders_log:
        symbol = order.get("symbol", "")
        if symbol:
            orders_by_symbol[symbol].append(order)
    
    # Enrich with exit data
    exits_by_symbol = defaultdict(list)
    for exit_rec in exit_log:
        symbol = exit_rec.get("symbol", "")
        if symbol:
            exits_by_symbol[symbol].append(exit_rec)
    
    # Build final trades list
    for trade_id, trade_data in trades_by_id.items():
        symbol = trade_data["symbol"]
        
        # Find entry order
        entry_order = None
        for order in orders_by_symbol.get(symbol, []):
            if order.get("side") in ["buy", "long"] and order.get("status") == "filled":
                entry_order = order
                break
        
        # Find exit order
        exit_order = None
        for order in orders_by_symbol.get(symbol, []):
            if order.get("side") in ["sell", "close"] and order.get("status") == "filled":
                exit_order = order
                break
        
        # Find exit event
        exit_event = None
        for exit_rec in exits_by_symbol.get(symbol, []):
            exit_event = exit_rec
            break
        
        trade = {
            "symbol": symbol,
            "side": entry_order.get("side", "buy") if entry_order else "buy",
            "qty": float(entry_order.get("qty", 0)) if entry_order else 0,
            "entry_time": trade_data.get("entry_time"),
            "exit_time": parse_timestamp(exit_order.get("ts")) if exit_order else None,
            "entry_price": float(entry_order.get("filled_avg_price", 0)) if entry_order else 0,
            "exit_price": float(exit_order.get("filled_avg_price", 0)) if exit_order else 0,
            "realized_pnl": trade_data.get("realized_pnl", 0),
            "unrealized_pnl": 0,  # Would need current price
            "mfe": 0,  # Would need price history
            "mae": 0,  # Would need price history
            "regime_at_entry": trade_data.get("regime_at_entry", "UNKNOWN"),
            "regime_at_exit": exit_event.get("regime", "UNKNOWN") if exit_event else "UNKNOWN",
            "entry_score": trade_data.get("entry_score", 0.0),
            "close_reason": trade_data.get("close_reason", "UNKNOWN"),
        }
        
        trades.append(trade)
    
    return trades


def build_shadow_trades_dataset(shadow_log: List[Dict], shadow_positions: Dict, 
                                target_date: datetime) -> List[Dict]:
    """Build canonical shadow trades dataset"""
    trades = []
    
    # Process shadow log
    for rec in shadow_log:
        if rec.get("type") != "shadow_trade":
            continue
        
        symbol = rec.get("symbol", "")
        if not symbol:
            continue
        
        trade = {
            "symbol": symbol,
            "side": rec.get("side", "buy"),
            "qty": float(rec.get("qty", 0)),
            "entry_time": rec.get("_parsed_timestamp"),
            "exit_time": parse_timestamp(rec.get("exit_ts")),
            "entry_price": float(rec.get("entry_price", 0)),
            "exit_price": float(rec.get("exit_price", 0)),
            "realized_pnl_shadow": float(rec.get("pnl", 0)),
            "mfe_shadow": float(rec.get("mfe", 0)),
            "mae_shadow": float(rec.get("mae", 0)),
            "regime_at_entry": rec.get("regime_at_entry", "UNKNOWN"),
            "regime_at_exit": rec.get("regime_at_exit", "UNKNOWN"),
        }
        
        trades.append(trade)
    
    # Also process shadow_positions.json if it exists
    if shadow_positions:
        positions = shadow_positions.get("positions", {})
        for symbol, pos_data in positions.items():
            entry_time = parse_timestamp(pos_data.get("entry_time"))
            if entry_time and entry_time.date() == target_date.date():
                trade = {
                    "symbol": symbol,
                    "side": pos_data.get("direction", "buy"),
                    "qty": float(pos_data.get("qty", 0)),
                    "entry_time": entry_time,
                    "exit_time": parse_timestamp(pos_data.get("close_time")),
                    "entry_price": float(pos_data.get("entry_price", 0)),
                    "exit_price": float(pos_data.get("current_price", 0)),
                    "realized_pnl_shadow": float(pos_data.get("realized_pnl", 0)),
                    "mfe_shadow": float(pos_data.get("max_profit_pct", 0)),
                    "mae_shadow": float(pos_data.get("max_loss_pct", 0)),
                    "regime_at_entry": pos_data.get("regime_at_entry", "UNKNOWN"),
                    "regime_at_exit": pos_data.get("regime_at_exit", "UNKNOWN"),
                }
                trades.append(trade)
    
    return trades


def build_signals_and_scores_dataset(signals_log: List[Dict], scoring_flow_log: List[Dict],
                                     market_context: Dict, symbol_risk: Dict,
                                     regime_posture: Dict, target_date: datetime) -> List[Dict]:
    """Build canonical signals and scores dataset"""
    records = []
    
    # Process signals
    for signal in signals_log:
        cluster = signal.get("cluster", {})
        symbol = cluster.get("ticker") or cluster.get("symbol") or signal.get("symbol", "")
        if not symbol:
            continue
        
        ts = signal.get("_parsed_timestamp")
        if not ts:
            continue
        
        # Get scores
        v1_score = cluster.get("v1_score", 0.0)
        v2_score = cluster.get("composite_score") or cluster.get("v2_score") or cluster.get("score", 0.0)
        composite_version = cluster.get("composite_version", "v2")
        
        # Get UW features
        uw_data = cluster.get("uw", {})
        uw_flow_strength = uw_data.get("flow_strength", 0.0)
        dark_pool_bias = uw_data.get("dark_pool_bias", 0.0)
        
        # Get risk features
        risk_data = symbol_risk.get(symbol, {})
        realized_vol_20d = risk_data.get("realized_vol_20d", 0.0)
        beta_vs_spy = risk_data.get("beta_vs_spy", 0.0)
        
        # Get regime and posture
        regime_label = regime_posture.get("current_regime", "UNKNOWN")
        posture = regime_posture.get("posture", "NEUTRAL")
        
        record = {
            "symbol": symbol,
            "ts": ts.isoformat() if ts else "",
            "v1_score": v1_score,
            "v2_score": v2_score,
            "composite_version_used": composite_version,
            "uw_flow_strength": uw_flow_strength,
            "dark_pool_bias": dark_pool_bias,
            "realized_vol_20d": realized_vol_20d,
            "beta_vs_spy": beta_vs_spy,
            "posture": posture,
            "regime_label": regime_label,
        }
        
        records.append(record)
    
    return records


def build_gates_and_blocks_dataset(gate_log: List[Dict], system_events_log: List[Dict],
                                   target_date: datetime) -> List[Dict]:
    """Build canonical gates and blocks dataset"""
    records = []
    
    # Process gate events
    for gate in gate_log:
        symbol = gate.get("symbol", "")
        if not symbol:
            continue
        
        ts = gate.get("_parsed_timestamp")
        if not ts:
            continue
        
        record = {
            "symbol": symbol,
            "ts": ts.isoformat() if ts else "",
            "gate_type": gate.get("gate_type") or gate.get("type", "unknown"),
            "reason": gate.get("reason") or gate.get("block_reason", "unknown"),
            "score_at_gate": gate.get("score", 0.0),
            "posture_at_gate": gate.get("posture", "UNKNOWN"),
            "regime_label": gate.get("regime", "UNKNOWN"),
            "event_source": "gate.blocked",
        }
        
        records.append(record)
    
    # Process system events for missed candidates
    for event in system_events_log:
        event_type = event.get("event_type") or event.get("type", "")
        if event_type not in ["decision.missed_candidate", "gate.blocked"]:
            continue
        
        symbol = event.get("symbol", "")
        if not symbol:
            continue
        
        ts = event.get("_parsed_timestamp")
        if not ts:
            continue
        
        record = {
            "symbol": symbol,
            "ts": ts.isoformat() if ts else "",
            "gate_type": event_type,
            "reason": event.get("reason", "unknown"),
            "score_at_gate": event.get("score", 0.0),
            "posture_at_gate": event.get("posture", "UNKNOWN"),
            "regime_label": event.get("regime", "UNKNOWN"),
            "event_source": event_type,
        }
        
        records.append(record)
    
    return records


def build_counter_signals_and_exits_dataset(system_events_log: List[Dict], exit_log: List[Dict],
                                            target_date: datetime) -> List[Dict]:
    """Build canonical counter-signals and exits dataset"""
    records = []
    
    # Process counter-signal events
    for event in system_events_log:
        event_type = event.get("event_type") or event.get("type", "")
        if "counter_signal" not in event_type.lower():
            continue
        
        symbol = event.get("symbol", "")
        if not symbol:
            continue
        
        ts = event.get("_parsed_timestamp")
        if not ts:
            continue
        
        record = {
            "symbol": symbol,
            "ts": ts.isoformat() if ts else "",
            "event_type": event_type,
            "details": json.dumps(event.get("details", {})),
            "regime_label": event.get("regime", "UNKNOWN"),
        }
        
        records.append(record)
    
    # Process exit events
    for exit_rec in exit_log:
        symbol = exit_rec.get("symbol", "")
        if not symbol:
            continue
        
        ts = exit_rec.get("_parsed_timestamp")
        if not ts:
            continue
        
        exit_type = exit_rec.get("exit_type") or exit_rec.get("type", "unknown")
        if "close_position" in exit_type.lower() and "failed" in exit_type.lower():
            record = {
                "symbol": symbol,
                "ts": ts.isoformat() if ts else "",
                "event_type": exit_type,
                "details": json.dumps(exit_rec.get("details", {})),
                "regime_label": exit_rec.get("regime", "UNKNOWN"),
            }
            records.append(record)
    
    return records


def build_universe_membership_dataset(trade_universe: Dict, symbol_risk: Dict,
                                     target_date: datetime) -> List[Dict]:
    """Build canonical universe membership dataset"""
    records = []
    
    universe_symbols = set(trade_universe.get("universe", []))
    
    # Get all symbols from risk features
    all_symbols = set(symbol_risk.keys())
    all_symbols.update(universe_symbols)
    
    # Calculate ranks (simplified - would need full data for proper ranking)
    vol_values = {s: symbol_risk.get(s, {}).get("realized_vol_20d", 0) for s in all_symbols}
    beta_values = {s: symbol_risk.get(s, {}).get("beta_vs_spy", 0) for s in all_symbols}
    
    # Sort and assign ranks
    vol_ranked = sorted(vol_values.items(), key=lambda x: x[1], reverse=True)
    beta_ranked = sorted(beta_values.items(), key=lambda x: abs(x[1]), reverse=True)
    
    vol_ranks = {symbol: rank + 1 for rank, (symbol, _) in enumerate(vol_ranked)}
    beta_ranks = {symbol: rank + 1 for rank, (symbol, _) in enumerate(beta_ranked)}
    
    for symbol in all_symbols:
        record = {
            "symbol": symbol,
            "in_v2_universe": symbol in universe_symbols,
            "vol_rank": vol_ranks.get(symbol, 0),
            "beta_rank": beta_ranks.get(symbol, 0),
            "uw_flow_rank": 0,  # Would need UW flow data
            "dark_pool_rank": 0,  # Would need dark pool data
        }
        records.append(record)
    
    return records


def save_csv(data: List[Dict], filepath: Path):
    """Save data to CSV file"""
    if not data:
        # Create empty file with headers
        with filepath.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[])
            writer.writeheader()
        return
    
    fieldnames = list(data[0].keys())
    with filepath.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def analyze_real_vs_shadow(real_trades: List[Dict], shadow_trades: List[Dict]) -> Dict:
    """Compare real vs shadow trades"""
    real_symbols = {t["symbol"] for t in real_trades}
    shadow_symbols = {t["symbol"] for t in shadow_trades}
    
    overlap_symbols = real_symbols & shadow_symbols
    real_only_symbols = real_symbols - shadow_symbols
    shadow_only_symbols = shadow_symbols - real_symbols
    
    # Calculate PnL
    total_real_pnl = sum(t.get("realized_pnl", 0) for t in real_trades)
    total_shadow_pnl = sum(t.get("realized_pnl_shadow", 0) for t in shadow_trades)
    
    # Per-symbol comparison
    real_pnl_by_symbol = defaultdict(float)
    for t in real_trades:
        real_pnl_by_symbol[t["symbol"]] += t.get("realized_pnl", 0)
    
    shadow_pnl_by_symbol = defaultdict(float)
    for t in shadow_trades:
        shadow_pnl_by_symbol[t["symbol"]] += t.get("realized_pnl_shadow", 0)
    
    comparison_data = []
    for symbol in sorted(overlap_symbols | real_only_symbols | shadow_only_symbols):
        comparison_data.append({
            "symbol": symbol,
            "real_pnl": real_pnl_by_symbol.get(symbol, 0),
            "shadow_pnl": shadow_pnl_by_symbol.get(symbol, 0),
            "delta_pnl": real_pnl_by_symbol.get(symbol, 0) - shadow_pnl_by_symbol.get(symbol, 0),
            "in_real": symbol in real_symbols,
            "in_shadow": symbol in shadow_symbols,
        })
    
    return {
        "total_real_pnl": total_real_pnl,
        "total_shadow_pnl": total_shadow_pnl,
        "delta_pnl": total_real_pnl - total_shadow_pnl,
        "overlap_symbols": len(overlap_symbols),
        "real_only_symbols": len(real_only_symbols),
        "shadow_only_symbols": len(shadow_only_symbols),
        "comparison_data": comparison_data,
    }


def analyze_what_if_blocked_and_missed(gates_and_blocks: List[Dict], counter_signals: List[Dict],
                                      target_date: datetime, orders_log: List[Dict]) -> List[Dict]:
    """
    Analyze what-if scenarios for blocked and missed candidates.
    
    For each blocked/missed candidate:
    - What if we had entered at that time?
    - What if we exited at EOD?
    - What if we exited at first counter-signal?
    
    Note: This requires price data which may not be available.
    We'll use order prices as a proxy where available.
    """
    what_if_data = []
    
    # Get EOD time
    _, market_close = get_market_hours(target_date)
    
    # Build counter-signal timeline by symbol
    counter_by_symbol = defaultdict(list)
    for cs in counter_signals:
        symbol = cs.get("symbol", "")
        if symbol:
            ts = parse_timestamp(cs.get("ts"))
            if ts:
                counter_by_symbol[symbol].append(ts)
    
    # Get price data from orders (entry prices for symbols)
    entry_prices_by_symbol = {}
    for order in orders_log:
        symbol = order.get("symbol", "")
        if symbol and order.get("side") in ["buy", "long"]:
            price = order.get("filled_avg_price") or order.get("limit_price")
            if price and symbol not in entry_prices_by_symbol:
                entry_prices_by_symbol[symbol] = float(price)
    
    # Analyze each blocked/missed candidate
    for block in gates_and_blocks:
        symbol = block.get("symbol", "")
        if not symbol:
            continue
        
        entry_ts = parse_timestamp(block.get("ts"))
        if not entry_ts:
            continue
        
        score = block.get("score_at_gate", 0.0)
        reason = block.get("reason", "unknown")
        gate_type = block.get("gate_type", "unknown")
        
        # Find first counter-signal after entry
        first_counter_ts = None
        for cs_ts in sorted(counter_by_symbol.get(symbol, [])):
            if cs_ts > entry_ts:
                first_counter_ts = cs_ts
                break
        
        # Get entry price (use order price if available, otherwise estimate from score)
        entry_price = entry_prices_by_symbol.get(symbol, 100.0)  # Default estimate
        
        # Estimate exit prices (would need actual price data)
        # For now, we'll use placeholder values
        eod_exit_price = entry_price  # Would need actual EOD price
        counter_exit_price = entry_price  # Would need actual price at counter-signal
        
        # Calculate what-if PnL (simplified - assumes long position)
        # In reality, would need to know direction and actual prices
        eod_pnl_pct = 0.0  # Would be: ((eod_exit_price - entry_price) / entry_price) * 100
        counter_pnl_pct = 0.0  # Would be: ((counter_exit_price - entry_price) / entry_price) * 100
        
        what_if_data.append({
            "symbol": symbol,
            "entry_ts": entry_ts.isoformat() if entry_ts else "",
            "score": score,
            "reason": reason,
            "gate_type": gate_type,
            "entry_price_estimate": entry_price,
            "eod_exit_price_estimate": eod_exit_price,
            "counter_exit_price_estimate": counter_exit_price,
            "eod_pnl_pct_estimate": eod_pnl_pct,
            "counter_pnl_pct_estimate": counter_pnl_pct,
            "first_counter_ts": first_counter_ts.isoformat() if first_counter_ts else "",
            "note": "Price estimates - requires actual price data for accurate what-if analysis",
        })
    
    return what_if_data


def analyze_what_if_exits(real_trades: List[Dict], counter_signals: List[Dict],
                          target_date: datetime) -> List[Dict]:
    """
    Analyze what-if scenarios for actual exits.
    
    For each real exit:
    - Compare actual exit vs exit at next counter-signal
    - Compare actual exit vs exit at EOD
    - Compute delta PnL
    """
    what_if_data = []
    
    # Get EOD time
    _, market_close = get_market_hours(target_date)
    
    # Build counter-signal timeline by symbol
    counter_by_symbol = defaultdict(list)
    for cs in counter_signals:
        symbol = cs.get("symbol", "")
        if symbol:
            ts = parse_timestamp(cs.get("ts"))
            if ts:
                counter_by_symbol[symbol].append(ts)
    
    # Analyze each real trade
    for trade in real_trades:
        symbol = trade.get("symbol", "")
        if not symbol:
            continue
        
        entry_time = trade.get("entry_time")
        exit_time = trade.get("exit_time")
        entry_price = trade.get("entry_price", 0)
        exit_price = trade.get("exit_price", 0)
        actual_pnl = trade.get("realized_pnl", 0)
        
        if not entry_time or not exit_time:
            continue
        
        entry_ts = parse_timestamp(entry_time) if isinstance(entry_time, str) else entry_time
        exit_ts = parse_timestamp(exit_time) if isinstance(exit_time, str) else exit_time
        
        if not entry_ts or not exit_ts:
            continue
        
        # Find next counter-signal after actual exit
        next_counter_ts = None
        for cs_ts in sorted(counter_by_symbol.get(symbol, [])):
            if cs_ts > exit_ts:
                next_counter_ts = cs_ts
                break
        
        # Estimate prices (would need actual price data)
        counter_exit_price = exit_price  # Would need actual price at counter-signal
        eod_exit_price = exit_price  # Would need actual EOD price
        
        # Calculate what-if PnL
        # In reality, would need actual prices
        counter_pnl = 0.0  # Would be: (counter_exit_price - entry_price) * qty
        eod_pnl = 0.0  # Would be: (eod_exit_price - entry_price) * qty
        
        delta_counter = counter_pnl - actual_pnl
        delta_eod = eod_pnl - actual_pnl
        
        what_if_data.append({
            "symbol": symbol,
            "entry_time": entry_ts.isoformat() if entry_ts else "",
            "actual_exit_time": exit_ts.isoformat() if exit_ts else "",
            "actual_exit_price": exit_price,
            "actual_pnl": actual_pnl,
            "next_counter_ts": next_counter_ts.isoformat() if next_counter_ts else "",
            "counter_exit_price_estimate": counter_exit_price,
            "eod_exit_price_estimate": eod_exit_price,
            "counter_pnl_estimate": counter_pnl,
            "eod_pnl_estimate": eod_pnl,
            "delta_vs_counter": delta_counter,
            "delta_vs_eod": delta_eod,
            "note": "Price estimates - requires actual price data for accurate what-if analysis",
        })
    
    return what_if_data


def generate_markdown_report(analysis: Dict, target_date: datetime) -> str:
    """Generate comprehensive markdown report"""
    date_str = target_date.date().isoformat()
    
    lines = [
        f"# First-Day Live Trading Review - {date_str}",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"**Analysis Date:** {date_str}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
    ]
    
    # Headline metrics
    real_trades = analysis.get("real_trades", [])
    shadow_trades = analysis.get("shadow_trades", [])
    total_real_pnl = sum(t.get("realized_pnl", 0) for t in real_trades)
    total_shadow_pnl = sum(t.get("realized_pnl_shadow", 0) for t in shadow_trades)
    
    lines.extend([
        f"- **Total Real Trades:** {len(real_trades)}",
        f"- **Total Real PnL:** ${total_real_pnl:.2f}",
        f"- **Total Shadow Trades:** {len(shadow_trades)}",
        f"- **Total Shadow PnL:** ${total_shadow_pnl:.2f}",
        "",
        "### Performance Questions",
        "",
        f"- **Did we beat buy-and-hold?** TBD (requires benchmark calculation)",
        f"- **Did we beat shadow?** {'YES' if total_real_pnl > total_shadow_pnl else 'NO'}",
        f"- **Did v2 behave as intended?** Analysis below",
        "",
        "---",
        "",
        "## Symbol and Universe Behavior",
        "",
    ])
    
    # Top/bottom PnL symbols
    real_pnl_by_symbol = defaultdict(float)
    for t in real_trades:
        real_pnl_by_symbol[t["symbol"]] += t.get("realized_pnl", 0)
    
    sorted_symbols = sorted(real_pnl_by_symbol.items(), key=lambda x: x[1], reverse=True)
    top_10 = sorted_symbols[:10]
    bottom_10 = sorted_symbols[-10:] if len(sorted_symbols) >= 10 else sorted_symbols
    
    lines.append("### Top 10 PnL Symbols (Real)")
    for symbol, pnl in top_10:
        lines.append(f"- {symbol}: ${pnl:.2f}")
    lines.append("")
    
    lines.append("### Bottom 10 PnL Symbols (Real)")
    for symbol, pnl in bottom_10:
        lines.append(f"- {symbol}: ${pnl:.2f}")
    lines.append("")
    
    # Universe analysis
    universe_membership = analysis.get("universe_membership", [])
    v2_universe_count = sum(1 for r in universe_membership if r.get("in_v2_universe"))
    lines.extend([
        f"- **V2 Universe Members:** {v2_universe_count}",
        f"- **Total Symbols Analyzed:** {len(universe_membership)}",
        "",
        "---",
        "",
        "## Signal and UW Effectiveness",
        "",
        "### Signal Effectiveness Summary",
        "",
    ])
    
    # Signal effectiveness
    signals = analysis.get("signals_and_scores", [])
    if signals:
        high_score_trades = [t for t in real_trades if t.get("entry_score", 0) > 3.0]
        low_score_trades = [t for t in real_trades if t.get("entry_score", 0) <= 3.0]
        
        high_score_avg_pnl = statistics.mean([t.get("realized_pnl", 0) for t in high_score_trades]) if high_score_trades else 0
        low_score_avg_pnl = statistics.mean([t.get("realized_pnl", 0) for t in low_score_trades]) if low_score_trades else 0
        
        lines.extend([
            f"- **High Score (>3.0) Trades:** {len(high_score_trades)}, Avg PnL: ${high_score_avg_pnl:.2f}",
            f"- **Low Score (≤3.0) Trades:** {len(low_score_trades)}, Avg PnL: ${low_score_avg_pnl:.2f}",
            "",
        ])
    
    # UW effectiveness (would need to correlate with trades)
    lines.extend([
        "### UW Feature Effectiveness",
        "",
        "Note: Detailed UW feature correlation analysis requires matching signals to trades.",
        "Review exports/signals_and_scores_*.csv for detailed UW feature data.",
        "",
    ])
    
    lines.extend([
        "---",
        "",
        "## Regime and Posture",
        "",
    ])
    
    # Regime analysis
    regime_posture_data = analysis.get("regime_posture", {})
    if regime_posture_data:
        current_regime = regime_posture_data.get("current_regime", "UNKNOWN")
        posture = regime_posture_data.get("posture", "UNKNOWN")
        lines.extend([
            f"- **Current Regime:** {current_regime}",
            f"- **Current Posture:** {posture}",
            "",
        ])
    
    # Regime by trade
    regime_by_trade = defaultdict(list)
    for trade in real_trades:
        regime = trade.get("regime_at_entry", "UNKNOWN")
        regime_by_trade[regime].append(trade)
    
    if regime_by_trade:
        lines.append("### Trades by Regime:")
        for regime, trades in sorted(regime_by_trade.items()):
            avg_pnl = statistics.mean([t.get("realized_pnl", 0) for t in trades]) if trades else 0
            lines.append(f"- **{regime}:** {len(trades)} trades, Avg PnL: ${avg_pnl:.2f}")
        lines.append("")
    
    lines.extend([
        "---",
        "",
        "## Counter-Signals, Blocked, and Missed",
        "",
    ])
    
    # Counter-signals
    counter_signals = analysis.get("counter_signals_and_exits", [])
    counter_detected = sum(1 for r in counter_signals if "detected" in r.get("event_type", "").lower())
    counter_exits = sum(1 for r in counter_signals if "exit_triggered" in r.get("event_type", "").lower())
    
    lines.extend([
        f"- **Counter-Signals Detected:** {counter_detected}",
        f"- **Counter-Signal Exits:** {counter_exits}",
        "",
    ])
    
    # Blocked and missed
    gates_and_blocks = analysis.get("gates_and_blocks", [])
    blocked_count = sum(1 for r in gates_and_blocks if "blocked" in r.get("gate_type", "").lower())
    missed_count = sum(1 for r in gates_and_blocks if "missed" in r.get("gate_type", "").lower())
    
    lines.extend([
        f"- **Blocked Trades:** {blocked_count}",
        f"- **Missed Candidates:** {missed_count}",
        "",
        "---",
        "",
        "## What-If Analysis",
        "",
    ])
    
    # What-if analysis
    what_if_blocked = analysis.get("what_if_blocked", [])
    what_if_exits = analysis.get("what_if_exits", [])
    
    lines.extend([
        "### Blocked and Missed Candidates",
        "",
        f"- **Total Blocked/Missed Analyzed:** {len(what_if_blocked)}",
        "",
        "Note: What-if analysis requires historical price data for accurate calculations.",
        "Current estimates are based on available order prices.",
        "",
        "### Exit What-If Scenarios",
        "",
        f"- **Total Exits Analyzed:** {len(what_if_exits)}",
        "",
        "Note: What-if exit analysis compares actual exits vs hypothetical exits",
        "at counter-signals or EOD. Requires price data for accurate calculations.",
        "",
        "---",
        "",
        "## Actionable Conclusions",
        "",
        "### Recommendations",
        "",
        "1. **Symbol Selection:** Review top/bottom performers for patterns",
        "2. **UW Features:** Analyze correlation between UW features and trade outcomes",
        "3. **Regime/Posture:** Verify regime detection and posture alignment",
        "4. **Exits:** Review exit timing vs counter-signals",
        "5. **Gates:** Evaluate if gates are too tight or too loose",
        "6. **What-If Analysis:** Integrate price data for accurate what-if calculations",
        "",
        "---",
        "",
        f"*Report generated at {datetime.now(timezone.utc).isoformat()}*",
    ])
    
    return "\n".join(lines)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="First-day live trading analysis")
    parser.add_argument("--date", type=str, required=True, help="Date in YYYY-MM-DD format")
    
    args = parser.parse_args()
    
    # Parse target date
    try:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        print(f"Error: Invalid date format. Use YYYY-MM-DD", file=sys.stderr)
        sys.exit(1)
    
    print("=" * 80)
    print(f"FIRST-DAY LIVE TRADING ANALYSIS - {target_date.date()}")
    print("=" * 80)
    print()
    
    # Load data
    print("Loading data from droplet...")
    
    # Try to use ReportDataFetcher if available
    if HAS_DROPLET_CLIENT:
        print("  Using ReportDataFetcher...")
        with ReportDataFetcher(date=args.date) as fetcher:
            attribution_log = fetcher.get_executed_trades()
            exit_log = fetcher.get_exit_events()
            signals_log = fetcher.get_signals()
            orders_log = fetcher.get_orders()
            gate_log = fetcher.get_gate_events()
            shadow_log = fetcher.get_shadow_events()
    else:
        print("  Loading from local files...")
        attribution_log = load_jsonl(LOG_FILES["attribution"], target_date)
        exit_log = load_jsonl(LOG_FILES["exit"], target_date)
        signals_log = load_jsonl(LOG_FILES["signals"], target_date)
        orders_log = load_jsonl(LOG_FILES["orders"], target_date)
        gate_log = load_jsonl(LOG_FILES["gate"], target_date)
        shadow_log = load_jsonl(LOG_FILES["shadow"], target_date)
    
    system_events_log = load_jsonl(LOG_FILES["system_events"], target_date)
    scoring_flow_log = load_jsonl(LOG_FILES["scoring_flow"], target_date)
    
    # Load state files
    print("  Loading state files...")
    market_context = load_json_state(STATE_FILES["market_context_v2"])
    regime_posture = load_json_state(STATE_FILES["regime_posture_state"])
    symbol_risk = load_json_state(STATE_FILES["symbol_risk_features"])
    trade_universe = load_json_state(STATE_FILES["trade_universe_v2"])
    shadow_positions = load_json_state(STATE_FILES["shadow_positions"])
    
    print(f"  Loaded: {len(attribution_log)} attribution, {len(orders_log)} orders, {len(exit_log)} exits")
    print()
    
    # Build canonical datasets
    print("Building canonical datasets...")
    real_trades = build_real_trades_dataset(attribution_log, orders_log, exit_log, target_date)
    shadow_trades = build_shadow_trades_dataset(shadow_log, shadow_positions, target_date)
    signals_and_scores = build_signals_and_scores_dataset(
        signals_log, scoring_flow_log, market_context, symbol_risk, regime_posture, target_date
    )
    gates_and_blocks = build_gates_and_blocks_dataset(gate_log, system_events_log, target_date)
    counter_signals_and_exits = build_counter_signals_and_exits_dataset(
        system_events_log, exit_log, target_date
    )
    universe_membership = build_universe_membership_dataset(trade_universe, symbol_risk, target_date)
    
    print(f"  Built: {len(real_trades)} real trades, {len(shadow_trades)} shadow trades")
    print()
    
    # Analyze
    print("Performing analysis...")
    real_vs_shadow = analyze_real_vs_shadow(real_trades, shadow_trades)
    what_if_blocked = analyze_what_if_blocked_and_missed(
        gates_and_blocks, counter_signals_and_exits, target_date, orders_log
    )
    what_if_exits = analyze_what_if_exits(real_trades, counter_signals_and_exits, target_date)
    
    # Prepare analysis dict
    analysis = {
        "real_trades": real_trades,
        "shadow_trades": shadow_trades,
        "signals_and_scores": signals_and_scores,
        "gates_and_blocks": gates_and_blocks,
        "counter_signals_and_exits": counter_signals_and_exits,
        "universe_membership": universe_membership,
        "real_vs_shadow": real_vs_shadow,
        "what_if_blocked": what_if_blocked,
        "what_if_exits": what_if_exits,
        "regime_posture": regime_posture,
        "market_context": market_context,
        "symbol_risk": symbol_risk,
        "trade_universe": trade_universe,
    }
    
    # Save CSV exports
    print("Saving CSV exports...")
    date_str = target_date.date().isoformat()
    
    save_csv(real_trades, EXPORTS_DIR / f"real_trades_{date_str}.csv")
    save_csv(shadow_trades, EXPORTS_DIR / f"shadow_trades_{date_str}.csv")
    save_csv(signals_and_scores, EXPORTS_DIR / f"signals_and_scores_{date_str}.csv")
    save_csv(gates_and_blocks, EXPORTS_DIR / f"gates_and_blocks_{date_str}.csv")
    save_csv(counter_signals_and_exits, EXPORTS_DIR / f"counter_signals_and_exits_{date_str}.csv")
    save_csv(universe_membership, EXPORTS_DIR / f"universe_membership_{date_str}.csv")
    save_csv(real_vs_shadow["comparison_data"], EXPORTS_DIR / f"real_vs_shadow_pnl_{date_str}.csv")
    save_csv(what_if_blocked, EXPORTS_DIR / f"what_if_blocked_and_missed_{date_str}.csv")
    save_csv(what_if_exits, EXPORTS_DIR / f"what_if_exits_{date_str}.csv")
    
    print(f"  Saved {len(real_trades)} exports")
    print()
    
    # Generate markdown report
    print("Generating markdown report...")
    markdown = generate_markdown_report(analysis, target_date)
    report_file = REPORTS_DIR / f"FIRST_DAY_LIVE_REVIEW_{date_str}.md"
    report_file.write_text(markdown, encoding="utf-8")
    print(f"  Saved: {report_file}")
    print()
    
    # Print summary
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print()
    print("Generated files:")
    print()
    print("Reports:")
    print(f"  - {report_file}")
    print()
    print("Exports:")
    for csv_file in sorted(EXPORTS_DIR.glob(f"*_{date_str}.csv")):
        print(f"  - {csv_file}")
    print()
    print("Suggested next command:")
    print(f"  Download {report_file} and all exports/*_{date_str}.csv for analysis.")
    print()


if __name__ == "__main__":
    main()
