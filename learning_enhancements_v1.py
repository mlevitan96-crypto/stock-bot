#!/usr/bin/env python3
"""
Learning Enhancements V1 - Pattern Learning Modules

Implements three learning enhancements:
1. Gate Pattern Learning - Learn optimal gate thresholds
2. UW Blocked Entry Learning - Learn from missed opportunities
3. Signal Pattern Learning - Learn best signal combinations

These modules extend the core learning system with pattern recognition.
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict

LOG_DIR = Path("logs")
DATA_DIR = Path("data")
STATE_DIR = Path("state")

# Gate pattern learning state
GATE_PATTERN_STATE = STATE_DIR / "gate_pattern_learning.json"

# UW blocked entry learning state
UW_BLOCKED_STATE = STATE_DIR / "uw_blocked_learning.json"

# Signal pattern learning state
SIGNAL_PATTERN_STATE = STATE_DIR / "signal_pattern_learning.json"


class GatePatternLearner:
    """
    Learns optimal gate thresholds by analyzing which gates block good vs bad trades.
    
    Tracks:
    - Which gates block which types of trades
    - Gate effectiveness (did blocking help or hurt?)
    - Optimal thresholds per gate
    """
    
    def __init__(self):
        self.state_file = GATE_PATTERN_STATE
        self.patterns: Dict[str, Dict] = defaultdict(lambda: {
            "blocks": 0,
            "score_ranges": defaultdict(int),
            "component_patterns": defaultdict(int),
            "outcomes": []  # Will be populated when we correlate with trades
        })
        self.load_state()
    
    def load_state(self):
        """Load gate pattern learning state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.patterns = defaultdict(lambda: {
                        "blocks": 0,
                        "score_ranges": defaultdict(int),
                        "component_patterns": defaultdict(int),
                        "outcomes": []
                    }, data.get("patterns", {}))
            except:
                pass
    
    def save_state(self):
        """Save gate pattern learning state"""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "patterns": dict(self.patterns),
                    "last_update": datetime.now(timezone.utc).isoformat()
                }, f, indent=2)
        except:
            pass
    
    def record_gate_block(self, gate_name: str, symbol: str, score: float, 
                         components: Dict, reason: str):
        """
        Record a gate block event.
        
        Args:
            gate_name: Name of the gate (e.g., "score_below_min", "max_positions")
            symbol: Symbol that was blocked
            score: Composite score at time of block
            components: Signal components
            reason: Blocking reason
        """
        # Validate inputs
        if not gate_name or not isinstance(gate_name, str):
            return
        if not symbol or not isinstance(symbol, str):
            return
        if score is None or not isinstance(score, (int, float)):
            score = 0.0
        if not components or not isinstance(components, dict):
            components = {}
        if not reason or not isinstance(reason, str):
            reason = "unknown"
        
        pattern = self.patterns[gate_name]
        pattern["blocks"] += 1
        
        # Track score ranges
        score_float = float(score)
        if score_float < 1.0:
            pattern["score_ranges"]["0-1"] += 1
        elif score_float < 2.0:
            pattern["score_ranges"]["1-2"] += 1
        elif score_float < 3.0:
            pattern["score_ranges"]["2-3"] += 1
        else:
            pattern["score_ranges"]["3+"] += 1
        
        # Track component patterns (which components were present)
        if components:
            for comp, value in components.items():
                try:
                    if value and isinstance(value, (int, float)) and float(value) > 0:
                        pattern["component_patterns"][comp] += 1
                except (ValueError, TypeError):
                    continue
    
    def get_gate_effectiveness(self, gate_name: str) -> Dict[str, Any]:
        """
        Get effectiveness metrics for a gate.
        
        Returns:
            Dict with effectiveness metrics
        """
        pattern = self.patterns.get(gate_name, {})
        total_blocks = pattern.get("blocks", 0)
        
        if total_blocks == 0:
            return {"gate": gate_name, "blocks": 0, "effectiveness": "unknown"}
        
        # Analyze score distribution
        score_ranges = pattern.get("score_ranges", {})
        low_score_blocks = score_ranges.get("0-1", 0) + score_ranges.get("1-2", 0)
        high_score_blocks = score_ranges.get("2-3", 0) + score_ranges.get("3+", 0)
        
        # Gate is effective if it blocks more low-score than high-score trades
        effectiveness_ratio = low_score_blocks / max(1, high_score_blocks)
        
        return {
            "gate": gate_name,
            "total_blocks": total_blocks,
            "low_score_blocks": low_score_blocks,
            "high_score_blocks": high_score_blocks,
            "effectiveness_ratio": round(effectiveness_ratio, 2),
            "likely_effective": effectiveness_ratio > 1.5,  # Blocks 1.5x more low-score
            "score_distribution": dict(score_ranges)
        }


class UWBlockedEntryLearner:
    """
    Learns from UW blocked entries (decision="rejected").
    
    Tracks:
    - Which signal combinations were blocked
    - Signal strength patterns in blocked entries
    - Component patterns in blocked entries
    """
    
    def __init__(self):
        self.state_file = UW_BLOCKED_STATE
        self.patterns: Dict[str, Dict] = defaultdict(lambda: {
            "blocked_count": 0,
            "score_distribution": defaultdict(int),
            "component_patterns": defaultdict(lambda: {"count": 0, "avg_value": 0.0}),
            "sentiment_patterns": defaultdict(int)
        })
        self.load_state()
    
    def load_state(self):
        """Load UW blocked entry learning state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.patterns = defaultdict(lambda: {
                        "blocked_count": 0,
                        "score_distribution": defaultdict(int),
                        "component_patterns": defaultdict(lambda: {"count": 0, "avg_value": 0.0}),
                        "sentiment_patterns": defaultdict(int)
                    }, data.get("patterns", {}))
            except:
                pass
    
    def save_state(self):
        """Save UW blocked entry learning state"""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "patterns": dict(self.patterns),
                    "last_update": datetime.now(timezone.utc).isoformat()
                }, f, indent=2)
        except:
            pass
    
    def record_blocked_entry(self, symbol: str, score: float, components: Dict,
                            flow_sentiment: str, dark_pool_sentiment: str, 
                            insider_sentiment: str):
        """
        Record a blocked UW entry.
        
        Args:
            symbol: Symbol that was blocked
            score: Composite score
            components: Signal components
            flow_sentiment: Flow sentiment
            dark_pool_sentiment: Dark pool sentiment
            insider_sentiment: Insider sentiment
        """
        # Validate inputs
        if not symbol or not isinstance(symbol, str):
            return
        if score is None or not isinstance(score, (int, float)):
            score = 0.0
        if not components or not isinstance(components, dict):
            components = {}
        if not flow_sentiment or not isinstance(flow_sentiment, str):
            flow_sentiment = "unknown"
        if not dark_pool_sentiment or not isinstance(dark_pool_sentiment, str):
            dark_pool_sentiment = "unknown"
        if not insider_sentiment or not isinstance(insider_sentiment, str):
            insider_sentiment = "unknown"
        
        # Track by symbol pattern
        pattern = self.patterns[symbol]
        pattern["blocked_count"] += 1
        
        # Track score distribution
        score_float = float(score)
        if score_float < 0.3:
            pattern["score_distribution"]["0-0.3"] += 1
        elif score_float < 0.5:
            pattern["score_distribution"]["0.3-0.5"] += 1
        elif score_float < 0.7:
            pattern["score_distribution"]["0.5-0.7"] += 1
        else:
            pattern["score_distribution"]["0.7+"] += 1
        
        # Track component patterns
        if components:
            for comp, value in components.items():
                try:
                    if value is not None and value != 0:
                        value_float = float(value)
                        comp_pattern = pattern["component_patterns"][comp]
                        comp_pattern["count"] += 1
                        # Update running average
                        current_avg = comp_pattern["avg_value"]
                        count = comp_pattern["count"]
                        comp_pattern["avg_value"] = ((current_avg * (count - 1)) + value_float) / count
                except (ValueError, TypeError):
                    continue
        
        # Track sentiment alignment
        sentiments = [s for s in [flow_sentiment, dark_pool_sentiment, insider_sentiment] if s and s != "unknown"]
        aligned = len(set(sentiments)) == 1 if sentiments else False
        pattern["sentiment_patterns"]["aligned" if aligned else "mixed"] += 1
    
    def get_blocked_patterns(self) -> Dict[str, Any]:
        """
        Get analysis of blocked entry patterns.
        
        Returns:
            Dict with pattern analysis
        """
        total_blocked = sum(p["blocked_count"] for p in self.patterns.values())
        
        # Find most common component patterns
        all_components = defaultdict(int)
        for pattern in self.patterns.values():
            for comp, comp_data in pattern["component_patterns"].items():
                all_components[comp] += comp_data["count"]
        
        top_components = sorted(all_components.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_blocked_entries": total_blocked,
            "unique_symbols_blocked": len(self.patterns),
            "top_blocked_components": [{"component": c, "count": count} for c, count in top_components],
            "symbols": {sym: {
                "blocked_count": p["blocked_count"],
                "avg_score_range": max(p["score_distribution"].items(), key=lambda x: x[1])[0] if p["score_distribution"] else "unknown"
            } for sym, p in list(self.patterns.items())[:20]}  # Top 20
        }


class SignalPatternLearner:
    """
    Learns which signal patterns lead to better trade outcomes.
    
    Correlates signals.jsonl with attribution.jsonl to find:
    - Best signal combinations
    - Signal timing patterns
    - Signal strength correlations with outcomes
    """
    
    def __init__(self):
        self.state_file = SIGNAL_PATTERN_STATE
        self.patterns: Dict[str, Dict] = defaultdict(lambda: {
            "signal_count": 0,
            "trades_resulting": 0,
            "wins": 0,
            "losses": 0,
            "total_pnl": 0.0,
            "component_combinations": defaultdict(lambda: {"count": 0, "wins": 0, "pnl": 0.0})
        })
        self.signal_to_trade_map: Dict[str, List[str]] = defaultdict(list)  # signal_id -> [trade_ids]
        self.load_state()
    
    def load_state(self):
        """Load signal pattern learning state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.patterns = defaultdict(lambda: {
                        "signal_count": 0,
                        "trades_resulting": 0,
                        "wins": 0,
                        "losses": 0,
                        "total_pnl": 0.0,
                        "component_combinations": defaultdict(lambda: {"count": 0, "wins": 0, "pnl": 0.0})
                    }, data.get("patterns", {}))
                    self.signal_to_trade_map = defaultdict(list, data.get("signal_to_trade_map", {}))
            except:
                pass
    
    def save_state(self):
        """Save signal pattern learning state"""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "patterns": dict(self.patterns),
                    "signal_to_trade_map": dict(self.signal_to_trade_map),
                    "last_update": datetime.now(timezone.utc).isoformat()
                }, f, indent=2)
        except:
            pass
    
    def record_signal(self, signal_id: str, symbol: str, components: Dict, score: float):
        """
        Record a signal generation event.
        
        Args:
            signal_id: Unique signal ID
            symbol: Symbol
            components: Signal components
            score: Composite score
        """
        # Validate inputs
        if not signal_id or not isinstance(signal_id, str):
            return
        if not symbol or not isinstance(symbol, str):
            return
        if not components or not isinstance(components, dict):
            components = {}
        if score is None or not isinstance(score, (int, float)):
            score = 0.0
        
        pattern = self.patterns[symbol]
        pattern["signal_count"] += 1
        
        # Track component combinations (which components appear together)
        if components:
            try:
                active_components = []
                for c, v in components.items():
                    try:
                        if v is not None and isinstance(v, (int, float)) and float(v) > 0:
                            active_components.append(c)
                    except (ValueError, TypeError):
                        continue
                
                if active_components:
                    comp_key = "+".join(sorted(active_components)[:5])  # Limit to first 5 for key
                    pattern["component_combinations"][comp_key]["count"] += 1
            except Exception:
                pass
    
    def correlate_with_trade(self, signal_id: str, trade_id: str, pnl_pct: float):
        """
        Correlate a signal with its resulting trade outcome.
        
        Args:
            signal_id: Signal ID
            trade_id: Trade ID from attribution
            pnl_pct: P&L percentage
        """
        # Map signal to trade
        self.signal_to_trade_map[signal_id].append(trade_id)
        
        # Find which symbol this signal was for (need to look it up)
        # For now, we'll update patterns when we process trades
    
    def update_pattern_with_outcome(self, symbol: str, components: Dict, pnl_pct: float):
        """
        Update pattern statistics with trade outcome.
        
        Args:
            symbol: Symbol
            components: Signal components
            pnl_pct: P&L percentage
        """
        # Validate inputs
        if not symbol or not isinstance(symbol, str):
            return
        if not components or not isinstance(components, dict):
            components = {}
        if pnl_pct is None or not isinstance(pnl_pct, (int, float)):
            return
        
        pattern = self.patterns.get(symbol, {})
        pattern["trades_resulting"] += 1
        
        pnl_float = float(pnl_pct)
        if pnl_float > 0:
            pattern["wins"] += 1
        else:
            pattern["losses"] += 1
        
        pattern["total_pnl"] += pnl_float
        
        # Update component combination outcomes
        if components:
            try:
                active_components = []
                for c, v in components.items():
                    try:
                        if v is not None and isinstance(v, (int, float)) and float(v) > 0:
                            active_components.append(c)
                    except (ValueError, TypeError):
                        continue
                
                if active_components:
                    comp_key = "+".join(sorted(active_components)[:5])
                    comp_pattern = pattern["component_combinations"][comp_key]
                    if pnl_float > 0:
                        comp_pattern["wins"] += 1
                    comp_pattern["pnl"] += pnl_float
            except Exception:
                pass
    
    def get_best_patterns(self, min_samples: int = 5) -> List[Dict[str, Any]]:
        """
        Get best performing signal patterns.
        
        Args:
            min_samples: Minimum number of trades to consider
        
        Returns:
            List of best patterns sorted by win rate and P&L
        """
        best_patterns = []
        
        for symbol, pattern in self.patterns.items():
            trades = pattern["trades_resulting"]
            if trades < min_samples:
                continue
            
            wins = pattern["wins"]
            win_rate = wins / trades if trades > 0 else 0.0
            avg_pnl = pattern["total_pnl"] / trades if trades > 0 else 0.0
            
            # Find best component combinations
            for comp_key, comp_data in pattern["component_combinations"].items():
                if comp_data["count"] >= min_samples:
                    comp_win_rate = comp_data["wins"] / comp_data["count"] if comp_data["count"] > 0 else 0.0
                    comp_avg_pnl = comp_data["pnl"] / comp_data["count"] if comp_data["count"] > 0 else 0.0
                    
                    best_patterns.append({
                        "symbol": symbol,
                        "components": comp_key,
                        "trades": comp_data["count"],
                        "win_rate": round(comp_win_rate, 3),
                        "avg_pnl": round(comp_avg_pnl, 4),
                        "total_pnl": round(comp_data["pnl"], 4)
                    })
        
        # Sort by win rate and avg P&L
        best_patterns.sort(key=lambda x: (x["win_rate"], x["avg_pnl"]), reverse=True)
        return best_patterns[:20]  # Top 20


# Global instances
_gate_learner: Optional[GatePatternLearner] = None
_uw_blocked_learner: Optional[UWBlockedEntryLearner] = None
_signal_learner: Optional[SignalPatternLearner] = None

def get_gate_learner() -> GatePatternLearner:
    """Get or create gate pattern learner instance"""
    global _gate_learner
    if _gate_learner is None:
        _gate_learner = GatePatternLearner()
    return _gate_learner

def get_uw_blocked_learner() -> UWBlockedEntryLearner:
    """Get or create UW blocked entry learner instance"""
    global _uw_blocked_learner
    if _uw_blocked_learner is None:
        _uw_blocked_learner = UWBlockedEntryLearner()
    return _uw_blocked_learner

def get_signal_learner() -> SignalPatternLearner:
    """Get or create signal pattern learner instance"""
    global _signal_learner
    if _signal_learner is None:
        _signal_learner = SignalPatternLearner()
    return _signal_learner
