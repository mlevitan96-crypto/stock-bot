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
5. data/uw_attribution.jsonl - UW signal patterns (including blocked entries)
6. state/blocked_trades.jsonl - Blocked trades (counterfactual learning)
7. logs/gate.jsonl - Gate blocking events
8. data/daily_postmortem.jsonl - Daily summaries (if exists)

Full Learning Cycle:
Signal → Trade Decision → Learn → Review → Update → Trade
- Signal: All signals generated
- Trade Decision: Taken trades, blocked trades, missed opportunities
- Learn: Process all outcomes (actual and counterfactual)
- Review: Analyze patterns, performance, missed opportunities
- Update: Adjust weights, thresholds, criteria
- Trade: Apply learnings to next cycle

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
        "last_blocked_trade_id": None,
        "last_gate_id": None,
        "last_uw_blocked_id": None,
        "last_processed_ts": None,
        "total_trades_processed": 0,
        "total_trades_learned_from": 0,
        "total_exits_processed": 0,
        "total_signals_processed": 0,
        "total_orders_processed": 0,
        "total_blocked_processed": 0,
        "total_gates_processed": 0,
        "total_uw_blocked_processed": 0
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
    elif log_type == "blocked_trade":
        return f"{rec.get('symbol')}_{rec.get('timestamp', '')}"
    elif log_type == "gate":
        return f"{rec.get('symbol', '')}_{rec.get('ts', rec.get('_ts', ''))}"
    return f"{log_type}_{rec.get('ts', rec.get('_ts', ''))}"

def process_attribution_log(state: Dict, process_all_historical: bool = False) -> int:
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
    seen_last_id = False  # Track if we've seen the last processed record
    
    with open(attr_log, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                if rec.get("type") != "attribution":
                    continue
                
                rec_id = get_record_id(rec, "attribution")
                
                # If process_all=False, only process records after last_id
                if not process_all_historical and last_id:
                    if rec_id == last_id:
                        # Found last processed record, process everything after this
                        seen_last_id = True
                        continue  # Skip the last_id record itself
                    elif not seen_last_id:
                        # Haven't found last_id yet, skip this record
                        continue
                
                if rec_id in processed_ids:
                    continue
                
                # Extract data
                symbol = rec.get("symbol")
                ctx = rec.get("context", {})
                
                # Try multiple ways to get components
                comps = ctx.get("components", {})
                if not comps:
                    # Try direct on record
                    comps = rec.get("components", {})
                
                pnl_pct = float(rec.get("pnl_pct", 0)) / 100.0  # Convert % to decimal
                regime = ctx.get("market_regime", ctx.get("gamma_regime", "neutral"))
                sector = ctx.get("sector", "unknown")
                
                # Always mark as processed to avoid re-processing
                processed_ids.add(rec_id)
                state["last_attribution_id"] = rec_id
                
                # Only learn from trades with components and non-zero P&L
                # But still mark all trades as processed
                if comps and pnl_pct != 0:
                    optimizer.record_trade(comps, pnl_pct, regime, sector)
                    processed += 1
                    
                    # Correlate with signal patterns for signal pattern learning
                    try:
                        from learning_enhancements_v1 import get_signal_learner
                        signal_learner = get_signal_learner()
                        signal_learner.update_pattern_with_outcome(
                            symbol=symbol,
                            components=comps,
                            pnl_pct=pnl_pct * 100.0  # Convert back to percentage
                        )
                    except:
                        pass
                elif not comps:
                    # Log that we skipped due to missing components
                    pass  # Could log this if needed
                elif pnl_pct == 0:
                    # Zero P&L trades - still valuable but don't affect learning much
                    # Could process these with pnl_pct = 0.0 if we want to track them
                    pass
                
            except Exception as e:
                continue
    
    # Update last processed ID (most recent record seen)
    if processed_ids:
        all_ids = sorted(processed_ids)
        state["last_attribution_id"] = all_ids[-1]
    
    # Save signal learner state
    try:
        from learning_enhancements_v1 import get_signal_learner
        signal_learner = get_signal_learner()
        signal_learner.save_state()
    except:
        pass
    
    # Count unique records processed
    # If process_all=True, count all records in file
    # If process_all=False, only count new records (those after last_id)
    if process_all_historical:
        # Count total unique records in file
        total_in_file = 0
        total_learnable = 0
        with open(attr_log, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        rec = json.loads(line)
                        if rec.get("type") == "attribution":
                            total_in_file += 1
                            # Count learnable trades (those with components and non-zero P&L)
                            ctx = rec.get("context", {})
                            comps = ctx.get("components", {}) or rec.get("components", {})
                            pnl_pct = float(rec.get("pnl_pct", 0))
                            if comps and pnl_pct != 0:
                                total_learnable += 1
                    except:
                        pass
        state["total_trades_processed"] = total_in_file
        state["total_trades_learned_from"] = total_learnable
    else:
        # Only count new records processed in this run
        new_records = len(processed_ids)
        if new_records > 0:
            current_total = state.get("total_trades_processed", 0)
            state["total_trades_processed"] = current_total + new_records
            # Add to learned from count
            current_learned = state.get("total_trades_learned_from", 0)
            state["total_trades_learned_from"] = current_learned + processed
    
    return processed

def process_exit_log(state: Dict, process_all_historical: bool = False) -> int:
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
    seen_last_id = False
    
    with open(exit_log, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                rec_id = get_record_id(rec, "exit")
                
                # If process_all=False, only process records after last_id
                if not process_all_historical and last_id:
                    if rec_id == last_id:
                        seen_last_id = True
                        continue
                    elif not seen_last_id:
                        continue
                
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
                
                # Always mark as processed
                processed_ids.add(rec_id)
                state["last_exit_id"] = rec_id
                
                # Record exit outcome if we have exit components
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
                
            except Exception as e:
                continue
    
    # Update last processed ID
    if processed_ids:
        all_ids = sorted(processed_ids)
        state["last_exit_id"] = all_ids[-1]
    
    # Count unique records
    if process_all_historical:
        total_in_file = 0
        with open(exit_log, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    total_in_file += 1
        state["total_exits_processed"] = total_in_file
    else:
        new_records = len(processed_ids)
        if new_records > 0:
            current_total = state.get("total_exits_processed", 0)
            state["total_exits_processed"] = current_total + new_records
    
    return processed

def process_signal_log(state: Dict, process_all_historical: bool = False) -> int:
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
    seen_last_id = False
    
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
                
                if not process_all_historical and last_id:
                    if rec_id == last_id:
                        seen_last_id = True
                        continue
                    elif not seen_last_id:
                        continue
                
                if rec_id in processed_ids:
                    continue
                
                # Extract signal data
                symbol = rec.get("symbol") or rec.get("ticker", "")
                cluster = rec.get("cluster", {})
                components = rec.get("components", {})
                score = float(rec.get("score", rec.get("composite_score", 0.0)))
                
                # Learn from signal pattern
                try:
                    from learning_enhancements_v1 import get_signal_learner
                    signal_learner = get_signal_learner()
                    signal_learner.record_signal(
                        signal_id=rec_id,
                        symbol=symbol,
                        components=components,
                        score=score
                    )
                except ImportError:
                    pass
                except Exception as e:
                    # Don't fail on learning errors
                    pass
                
                processed += 1
                processed_ids.add(rec_id)
                state["last_signal_id"] = rec_id
                
            except Exception as e:
                continue
    
    # Update last processed ID
    if processed_ids:
        all_ids = sorted(processed_ids)
        state["last_signal_id"] = all_ids[-1]
    
    # Save signal learner state
    try:
        from learning_enhancements_v1 import get_signal_learner
        signal_learner = get_signal_learner()
        signal_learner.save_state()
    except:
        pass
    
    # Count unique records
    if process_all_historical:
        total_in_file = 0
        with open(signal_log, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        rec = json.loads(line)
                        if rec.get("type") == "signal":
                            total_in_file += 1
                    except:
                        pass
        state["total_signals_processed"] = total_in_file
    else:
        new_records = len(processed_ids)
        if new_records > 0:
            current_total = state.get("total_signals_processed", 0)
            state["total_signals_processed"] = current_total + new_records
    
    return processed

def process_order_log(state: Dict, process_all_historical: bool = False) -> int:
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
    seen_last_id = False
    
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
                
                if not process_all_historical and last_id:
                    if rec_id == last_id:
                        seen_last_id = True
                        continue
                    elif not seen_last_id:
                        continue
                
                if rec_id in processed_ids:
                    continue
                
                # TODO: Implement execution quality learning
                # For now, just mark as processed
                processed += 1
                processed_ids.add(rec_id)
                state["last_order_id"] = rec_id
                
            except Exception as e:
                continue
    
    # Update last processed ID
    if processed_ids:
        all_ids = sorted(processed_ids)
        state["last_order_id"] = all_ids[-1]
    
    # Count unique records
    if process_all_historical:
        total_in_file = 0
        with open(order_log, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        rec = json.loads(line)
                        if rec.get("type") == "order":
                            total_in_file += 1
                    except:
                        pass
        state["total_orders_processed"] = total_in_file
    else:
        new_records = len(processed_ids)
        if new_records > 0:
            current_total = state.get("total_orders_processed", 0)
            state["total_orders_processed"] = current_total + new_records
    
    return processed

def process_blocked_trades(state: Dict, process_all_historical: bool = False) -> int:
    """
    Process blocked_trades.jsonl for counterfactual learning.
    
    Counterfactual learning: What would have happened if we took blocked trades?
    This helps learn if gates are too strict or too loose.
    
    Returns:
        Number of blocked trades processed
    """
    blocked_log = STATE_DIR / "blocked_trades.jsonl"
    if not blocked_log.exists():
        return 0
    
    optimizer = get_optimizer()
    if not optimizer:
        return 0
    
    processed = 0
    last_id = state.get("last_blocked_trade_id")
    processed_ids: Set[str] = set()
    seen_last_id = False
    
    with open(blocked_log, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                rec_id = f"{rec.get('symbol')}_{rec.get('timestamp', '')}"
                
                if not process_all_historical and last_id:
                    if rec_id == last_id:
                        seen_last_id = True
                        continue
                    elif not seen_last_id:
                        continue
                
                if rec_id in processed_ids:
                    continue
                
                # Extract blocked trade data
                symbol = rec.get("symbol")
                reason = rec.get("reason", "unknown")
                score = rec.get("score", 0.0)
                comps = rec.get("components", {})
                decision_price = rec.get("decision_price", 0.0)
                direction = rec.get("direction", "unknown")
                
                # Always mark as processed
                processed_ids.add(rec_id)
                state["last_blocked_trade_id"] = rec_id
                
                # TODO: Counterfactual analysis - compute theoretical P&L
                # For now, we track blocked trades but don't learn from them yet
                # This requires price data to compute "what if" scenarios
                # Future: Implement counterfactual analyzer to compute theoretical outcomes
                
                processed += 1
                
            except Exception as e:
                continue
    
    # Update last processed ID
    if processed_ids:
        all_ids = sorted(processed_ids)
        state["last_blocked_trade_id"] = all_ids[-1]
    
    # Count unique records
    if process_all_historical:
        total_in_file = 0
        with open(blocked_log, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    total_in_file += 1
        state["total_blocked_processed"] = total_in_file
    else:
        new_records = len(processed_ids)
        if new_records > 0:
            current_total = state.get("total_blocked_processed", 0)
            state["total_blocked_processed"] = current_total + new_records
    
    return processed

def process_gate_events(state: Dict, process_all_historical: bool = False) -> int:
    """
    Process gate.jsonl for gate blocking pattern learning.
    
    This learns which gates are blocking good trades vs bad trades.
    Helps optimize gate thresholds.
    
    Returns:
        Number of gate events processed
    """
    gate_log = LOG_DIR / "gate.jsonl"
    if not gate_log.exists():
        return 0
    
    # Import gate pattern learner
    try:
        from learning_enhancements_v1 import get_gate_learner
        gate_learner = get_gate_learner()
    except ImportError:
        gate_learner = None
    
    processed = 0
    last_id = state.get("last_gate_id")
    processed_ids: Set[str] = set()
    seen_last_id = False
    
    with open(gate_log, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                rec_id = f"{rec.get('symbol', '')}_{rec.get('ts', rec.get('_ts', ''))}"
                
                if not process_all_historical and last_id:
                    if rec_id == last_id:
                        seen_last_id = True
                        continue
                    elif not seen_last_id:
                        continue
                
                if rec_id in processed_ids:
                    continue
                
                # Extract gate information
                symbol = rec.get("symbol", "")
                gate_name = rec.get("gate", rec.get("reason", "unknown"))
                score = float(rec.get("score", 0.0))
                components = rec.get("components", {})
                reason = rec.get("reason", rec.get("gate", "unknown"))
                
                # Learn from gate pattern
                if gate_learner:
                    try:
                        gate_learner.record_gate_block(
                            gate_name=gate_name,
                            symbol=symbol,
                            score=score,
                            components=components,
                            reason=reason
                        )
                    except Exception as e:
                        # Don't fail on learning errors
                        pass
                
                processed += 1
                processed_ids.add(rec_id)
                state["last_gate_id"] = rec_id
                
            except Exception as e:
                continue
    
    # Save gate learner state
    if gate_learner:
        try:
            gate_learner.save_state()
        except:
            pass
    
    # Update last processed ID
    if processed_ids:
        all_ids = sorted(processed_ids)
        state["last_gate_id"] = all_ids[-1]
    
    # Count unique records
    if process_all_historical:
        total_in_file = 0
        with open(gate_log, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    total_in_file += 1
        state["total_gates_processed"] = total_in_file
    else:
        new_records = len(processed_ids)
        if new_records > 0:
            current_total = state.get("total_gates_processed", 0)
            state["total_gates_processed"] = current_total + new_records
    
    return processed

def process_uw_attribution_blocked(state: Dict, process_all_historical: bool = False) -> int:
    """
    Process uw_attribution.jsonl for blocked entry learning.
    
    This learns from UW attribution events where decision="ENTRY_BLOCKED".
    Helps understand which signal combinations were blocked and why.
    
    Returns:
        Number of blocked UW entries processed
    """
    uw_attr_log = DATA_DIR / "uw_attribution.jsonl"
    if not uw_attr_log.exists():
        return 0
    
    processed = 0
    last_id = state.get("last_uw_blocked_id")
    processed_ids: Set[str] = set()
    seen_last_id = False
    
    with open(uw_attr_log, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                
                # Only process blocked entries
                decision = rec.get("decision", "").upper()
                # Check for various blocked decision formats (including "rejected" and "signal")
                # "rejected" means entry was blocked, "signal" means it was just evaluated
                if "BLOCKED" not in decision and "REJECTED" not in decision:
                    continue
                
                rec_id = f"{rec.get('symbol')}_{rec.get('_ts', '')}"
                
                if not process_all_historical and last_id:
                    if rec_id == last_id:
                        seen_last_id = True
                        continue
                    elif not seen_last_id:
                        continue
                
                if rec_id in processed_ids:
                    continue
                
                # Extract blocked entry data
                symbol = rec.get("symbol")
                score = rec.get("score", 0.0)
                components = rec.get("components", {})
                flow_sentiment = rec.get("flow_sentiment", "unknown")
                dark_pool_sentiment = rec.get("dark_pool_sentiment", "unknown")
                insider_sentiment = rec.get("insider_sentiment", "unknown")
                
                # Learn from blocked UW entries
                try:
                    from learning_enhancements_v1 import get_uw_blocked_learner
                    uw_learner = get_uw_blocked_learner()
                    uw_learner.record_blocked_entry(
                        symbol=symbol,
                        score=score,
                        components=components,
                        flow_sentiment=flow_sentiment,
                        dark_pool_sentiment=dark_pool_sentiment,
                        insider_sentiment=insider_sentiment
                    )
                except ImportError:
                    pass
                except Exception as e:
                    # Don't fail on learning errors
                    pass
                
                processed += 1
                processed_ids.add(rec_id)
                
            except Exception as e:
                continue
    
    # Update last processed ID
    if processed_ids:
        all_ids = sorted(processed_ids)
        state["last_uw_blocked_id"] = all_ids[-1]
    
    # Save UW blocked learner state
    try:
        from learning_enhancements_v1 import get_uw_blocked_learner
        uw_learner = get_uw_blocked_learner()
        uw_learner.save_state()
    except:
        pass
    
    # Count unique records
    if process_all_historical:
        total_in_file = 0
        with open(uw_attr_log, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        rec = json.loads(line)
                        decision = rec.get("decision", "").upper()
                        if "BLOCKED" in decision or "REJECTED" in decision:
                            total_in_file += 1
                    except:
                        pass
        state["total_uw_blocked_processed"] = total_in_file
    else:
        new_records = len(processed_ids)
        if new_records > 0:
            current_total = state.get("total_uw_blocked_processed", 0)
            state["total_uw_blocked_processed"] = current_total + new_records
    
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
        "blocked_trades": 0,
        "gate_events": 0,
        "uw_blocked": 0,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Process all data sources - FULL LEARNING CYCLE
    # Signal → Trade Decision → Learn → Review → Update → Trade
    
    # 1. Actual trades (what we did)
    results["attribution"] = process_attribution_log(state, process_all_historical)
    results["exits"] = process_exit_log(state, process_all_historical)
    
    # 2. Blocked trades and missed opportunities (what we didn't do)
    results["blocked_trades"] = process_blocked_trades(state, process_all_historical)
    results["gate_events"] = process_gate_events(state, process_all_historical)
    results["uw_blocked"] = process_uw_attribution_blocked(state, process_all_historical)
    
    # 3. Signal patterns and execution quality
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
    SHORT-TERM LEARNING: Record trade for learning (but don't update weights immediately).
    
    Industry best practice: Batch weight updates to prevent overfitting.
    - Records trade immediately for tracking
    - Updates EWMA in daily batch processing
    - Weight adjustments only in daily batch (with MIN_SAMPLES guard)
    """
    optimizer = get_optimizer()
    if optimizer and components and pnl_pct != 0:
        # Record trade for learning (updates internal tracking)
        optimizer.record_trade(components, pnl_pct / 100.0, regime, sector)
        
        # DO NOT update weights immediately - batch in daily processing
        # This prevents overfitting to noise in individual trades
        # Weight updates happen in run_daily_learning() with proper safeguards

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
