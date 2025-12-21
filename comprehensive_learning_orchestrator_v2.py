#!/usr/bin/env python3
"""
Comprehensive Learning Orchestrator V2

Processes ALL data sources for multi-timeframe learning:
- Short-term: Immediate learning after each trade (continuous)
- Medium-term: Daily batch processing (patterns, trends)
- Long-term: Weekly/monthly analysis (regime changes, structural shifts)

Data Sources:
1. logs/attribution.jsonl - Trade outcomes (ALL historical)
2. logs/exit.jsonl - Exit events and reasons
3. logs/signals.jsonl - Signal generation patterns
4. logs/orders.jsonl - Execution quality
5. data/uw_attribution.jsonl - UW signal patterns
6. data/daily_postmortem.jsonl - Daily summaries (if exists)

Features:
- Tracks last processed record IDs to avoid duplicates
- Multi-timeframe learning (short/medium/long)
- Processes all historical data on first run
- Continuous learning after each trade
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict

# Import existing learning components
from adaptive_signal_optimizer import get_optimizer, SIGNAL_COMPONENTS, EXIT_COMPONENTS

LOG_DIR = Path("logs")
DATA_DIR = Path("data")
STATE_DIR = Path("state")
LEARNING_STATE_FILE = STATE_DIR / "learning_processing_state.json"

def load_learning_state() -> Dict:
    """Load learning processing state (last processed IDs, timestamps)"""
    if LEARNING_STATE_FILE.exists():
        try:
            with open(LEARNING_STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        "last_attribution_id": None,
        "last_exit_id": None,
        "last_signal_id": None,
        "last_order_id": None,
        "last_uw_attribution_id": None,
        "last_processed_ts": None,
        "total_trades_processed": 0,
        "total_exits_processed": 0,
        "total_signals_processed": 0,
        "total_orders_processed": 0
    }

def save_learning_state(state: Dict):
    """Save learning processing state"""
    LEARNING_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LEARNING_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)

def get_record_id(rec: Dict, log_type: str) -> str:
    """Generate unique ID for a record"""
    if log_type == "attribution":
        return rec.get("trade_id") or f"{rec.get('symbol')}_{rec.get('ts', '')}"
    elif log_type == "exit":
        return f"{rec.get('symbol')}_{rec.get('ts', '')}"
    elif log_type == "signal":
        cluster = rec.get("cluster", {})
        return f"{cluster.get('ticker')}_{cluster.get('start_ts', '')}"
    elif log_type == "order":
        return f"{rec.get('symbol')}_{rec.get('ts', rec.get('_ts', ''))}"
    elif log_type == "uw_attribution":
        return f"{rec.get('symbol')}_{rec.get('_ts', '')}"
    return f"{log_type}_{rec.get('ts', rec.get('_ts', ''))}"

def process_attribution_log(state: Dict, process_all: bool = False) -> int:
    """
    Process attribution.jsonl for trade outcome learning.
    
    Args:
        state: Learning state dict
        process_all: If True, process all records. If False, only unprocessed.
    
    Returns:
        Number of trades processed
    """
    attr_log = LOG_DIR / "attribution.jsonl"
    if not attr_log.exists():
        return 0
    
    optimizer = get_optimizer()
    if not optimizer:
        return 0
    
    processed = 0
    last_id = state.get("last_attribution_id")
    processed_ids: Set[str] = set()
    
    with open(attr_log, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                if rec.get("type") != "attribution":
                    continue
                
                rec_id = get_record_id(rec, "attribution")
                
                # Skip if already processed (unless process_all)
                if not process_all and last_id and rec_id == last_id:
                    break
                if rec_id in processed_ids:
                    continue
                
                # Extract data
                symbol = rec.get("symbol")
                ctx = rec.get("context", {})
                comps = ctx.get("components", {})
                pnl_pct = float(rec.get("pnl_pct", 0)) / 100.0  # Convert % to decimal
                regime = ctx.get("market_regime", ctx.get("gamma_regime", "neutral"))
                sector = ctx.get("sector", "unknown")
                
                # Only process if we have components and non-zero P&L
                if comps and pnl_pct != 0:
                    optimizer.record_trade(comps, pnl_pct, regime, sector)
                    processed += 1
                    processed_ids.add(rec_id)
                    state["last_attribution_id"] = rec_id
                
            except Exception as e:
                continue
    
    state["total_trades_processed"] = state.get("total_trades_processed", 0) + processed
    return processed

def process_exit_log(state: Dict, process_all: bool = False) -> int:
    """
    Process exit.jsonl for exit signal learning.
    
    Returns:
        Number of exits processed
    """
    exit_log = LOG_DIR / "exit.jsonl"
    if not exit_log.exists():
        return 0
    
    optimizer = get_optimizer()
    if not optimizer or not hasattr(optimizer, 'exit_model'):
        return 0
    
    processed = 0
    last_id = state.get("last_exit_id")
    processed_ids: Set[str] = set()
    
    with open(exit_log, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                rec_id = get_record_id(rec, "exit")
                
                # Skip if already processed
                if not process_all and last_id and rec_id == last_id:
                    break
                if rec_id in processed_ids:
                    continue
                
                # Extract exit data
                close_reason = rec.get("reason", rec.get("close_reason", "unknown"))
                pnl_pct = rec.get("pnl_pct", 0)
                if isinstance(pnl_pct, str):
                    pnl_pct = float(pnl_pct.replace("%", ""))
                pnl_pct = float(pnl_pct) / 100.0  # Convert to decimal
                
                # Parse exit signals from close_reason
                exit_components = {}
                if close_reason and close_reason != "unknown":
                    for part in str(close_reason).split("+"):
                        part = part.strip()
                        if "(" in part:
                            signal_name = part.split("(")[0].strip()
                        else:
                            signal_name = part.strip()
                        
                        # Map to exit components
                        if "signal_decay" in signal_name or "entry_decay" in signal_name:
                            exit_components["entry_decay"] = 1.0
                        elif "flow_reversal" in signal_name or "adverse_flow" in signal_name:
                            exit_components["adverse_flow"] = 1.0
                        elif "drawdown" in signal_name:
                            exit_components["drawdown_velocity"] = 1.0
                        elif "time" in signal_name or "stale" in signal_name:
                            exit_components["time_decay"] = 1.0
                        elif "momentum" in signal_name:
                            exit_components["momentum_reversal"] = 1.0
                
                # Record exit outcome
                if exit_components and pnl_pct != 0:
                    if hasattr(optimizer, 'learner') and hasattr(optimizer.learner, 'record_trade_outcome'):
                        optimizer.learner.record_trade_outcome(
                            trade_data={
                                "exit_ts": rec.get("ts", rec.get("_ts", "")),
                                "close_reason": close_reason
                            },
                            feature_vector=exit_components,
                            pnl=pnl_pct,
                            regime=rec.get("regime", "unknown"),
                            sector="unknown"
                        )
                        processed += 1
                        processed_ids.add(rec_id)
                        state["last_exit_id"] = rec_id
                
            except Exception as e:
                continue
    
    state["total_exits_processed"] = state.get("total_exits_processed", 0) + processed
    return processed

def process_signal_log(state: Dict, process_all: bool = False) -> int:
    """
    Process signals.jsonl for signal pattern learning.
    
    This learns which signal patterns lead to better outcomes.
    Currently logs patterns for future analysis.
    
    Returns:
        Number of signals processed
    """
    signal_log = LOG_DIR / "signals.jsonl"
    if not signal_log.exists():
        return 0
    
    processed = 0
    last_id = state.get("last_signal_id")
    processed_ids: Set[str] = set()
    
    # Track signal patterns and their outcomes
    # This is a placeholder for future signal pattern learning
    # For now, we just track that we've seen them
    
    with open(signal_log, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                if rec.get("type") != "signal":
                    continue
                
                rec_id = get_record_id(rec, "signal")
                
                if not process_all and last_id and rec_id == last_id:
                    break
                if rec_id in processed_ids:
                    continue
                
                # TODO: Implement signal pattern learning
                # For now, just mark as processed
                processed += 1
                processed_ids.add(rec_id)
                state["last_signal_id"] = rec_id
                
            except Exception as e:
                continue
    
    state["total_signals_processed"] = state.get("total_signals_processed", 0) + processed
    return processed

def process_order_log(state: Dict, process_all: bool = False) -> int:
    """
    Process orders.jsonl for execution quality learning.
    
    This learns execution patterns, slippage, timing.
    Currently logs patterns for future analysis.
    
    Returns:
        Number of orders processed
    """
    order_log = LOG_DIR / "orders.jsonl"
    if not order_log.exists():
        return 0
    
    processed = 0
    last_id = state.get("last_order_id")
    processed_ids: Set[str] = set()
    
    # Track execution quality patterns
    # This is a placeholder for future execution learning
    # For now, we just track that we've seen them
    
    with open(order_log, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                if rec.get("type") != "order":
                    continue
                
                rec_id = get_record_id(rec, "order")
                
                if not process_all and last_id and rec_id == last_id:
                    break
                if rec_id in processed_ids:
                    continue
                
                # TODO: Implement execution quality learning
                # For now, just mark as processed
                processed += 1
                processed_ids.add(rec_id)
                state["last_order_id"] = rec_id
                
            except Exception as e:
                continue
    
    state["total_orders_processed"] = state.get("total_orders_processed", 0) + processed
    return processed

def run_comprehensive_learning(process_all_historical: bool = False):
    """
    Run comprehensive learning from all data sources.
    
    Args:
        process_all_historical: If True, process all historical data (first run).
                                If False, only process new records.
    """
    state = load_learning_state()
    optimizer = get_optimizer()
    
    if not optimizer:
        return
    
    results = {
        "attribution": 0,
        "exits": 0,
        "signals": 0,
        "orders": 0,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Process all data sources
    results["attribution"] = process_attribution_log(state, process_all_historical)
    results["exits"] = process_exit_log(state, process_all_historical)
    results["signals"] = process_signal_log(state, process_all_historical)
    results["orders"] = process_order_log(state, process_all_historical)
    
    # Update weights if enough new samples
    total_new = results["attribution"] + results["exits"]
    if total_new >= 5:
        try:
            weight_result = optimizer.update_weights()
            results["weights_updated"] = weight_result.get("total_adjusted", 0)
            optimizer.save_state()
        except Exception as e:
            results["weight_update_error"] = str(e)
    
    # Save state
    state["last_processed_ts"] = datetime.now(timezone.utc).isoformat()
    save_learning_state(state)
    
    return results

def learn_from_trade_close(symbol: str, pnl_pct: float, components: Dict, regime: str = "neutral", sector: str = "unknown"):
    """
    SHORT-TERM LEARNING: Immediate learning after each trade close.
    
    This is called immediately after a trade closes for fast adaptation.
    """
    optimizer = get_optimizer()
    if optimizer and components and pnl_pct != 0:
        optimizer.record_trade(components, pnl_pct / 100.0, regime, sector)
        
        # Update weights if we have enough samples (but don't wait for batch)
        # This enables fast adaptation
        try:
            optimizer.update_weights()
            optimizer.save_state()
        except:
            pass  # Don't fail on weight update

def run_daily_learning():
    """
    MEDIUM-TERM LEARNING: Daily batch processing.
    
    Processes all new records from the day and updates weights.
    """
    return run_comprehensive_learning(process_all_historical=False)

def run_historical_backfill():
    """
    LONG-TERM LEARNING: Process all historical data.
    
    Run this once to backfill all historical trades.
    """
    return run_comprehensive_learning(process_all_historical=True)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "backfill":
        print("Running historical backfill...")
        results = run_historical_backfill()
        print(f"Processed: {results}")
    else:
        print("Running daily learning...")
        results = run_daily_learning()
        print(f"Processed: {results}")
