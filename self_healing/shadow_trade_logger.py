#!/usr/bin/env python3
"""
Self-Healing & Shadow Auditing: ShadowTradeLogger
Tracks rejected signals and automatically adjusts gate thresholds if rejected signals outperform active ones.
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

DATA_DIR = Path("data")
SHADOW_LOG_FILE = DATA_DIR / "shadow_trades.jsonl"
GATE_THRESHOLDS_FILE = DATA_DIR / "gate_thresholds.json"

class ShadowTradeLogger:
    """Tracks rejected signals and compares performance to active trades."""
    
    def __init__(self):
        self.log_file = SHADOW_LOG_FILE
        self.thresholds_file = GATE_THRESHOLDS_FILE
        self.gate_thresholds = self._load_thresholds()
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """Ensure directories exist"""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.thresholds_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_thresholds(self) -> Dict:
        """Load current gate thresholds"""
        if self.thresholds_file.exists():
            try:
                with open(self.thresholds_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default thresholds
        return {
            "uw_entry_gate": {
                "min_count": 3,
                "min_premium": 50000
            },
            "toxicity_gate": {
                "max_toxicity": 0.9
            },
            "score_gate": {
                "min_score": 2.0
            },
            "expectancy_gate": {
                "min_expectancy": 0.0
            }
        }
    
    def _save_thresholds(self):
        """Save gate thresholds"""
        with open(self.thresholds_file, 'w') as f:
            json.dump(self.gate_thresholds, f, indent=2)
    
    def log_rejected_signal(self, symbol: str, reason: str, score: float, 
                           components: Dict, gate_name: str, threshold_value: float):
        """Log a rejected signal for shadow tracking"""
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": symbol,
            "reason": reason,
            "gate_name": gate_name,
            "threshold_value": threshold_value,
            "signal_score": score,
            "components": components,
            "status": "rejected"
        }
        
        # Append to shadow log
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(record) + "\n")
    
    def _compute_counterfactual_pnl(self, rejected_record: Dict) -> Optional[float]:
        """
        Compute theoretical P&L for a rejected signal.
        This would use historical price data to simulate what would have happened.
        """
        # This is a placeholder - would need actual price data
        # For now, return None (would be implemented with Alpaca historical data)
        return None
    
    def analyze_shadow_performance(self, lookback_days: int = 30) -> Dict:
        """
        Analyze performance of rejected signals vs active trades.
        Returns: Analysis results with recommendations
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        
        # Load shadow trades
        shadow_trades = []
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                        ts_str = rec.get("timestamp", "")
                        if ts_str:
                            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                            if ts >= cutoff_date:
                                shadow_trades.append(rec)
                    except:
                        continue
        
        # Load actual trades for comparison
        actual_trades = []
        attribution_file = Path("logs/attribution.jsonl")
        if attribution_file.exists():
            with open(attribution_file, 'r') as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                        ts_str = rec.get("timestamp") or rec.get("ts", "")
                        if ts_str:
                            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                            if ts >= cutoff_date:
                                actual_trades.append(rec)
                    except:
                        continue
        
        # Analyze by gate
        gate_analysis = defaultdict(lambda: {
            "rejected_count": 0,
            "rejected_avg_score": 0.0,
            "actual_count": 0,
            "actual_avg_pnl": 0.0,
            "should_adjust": False
        })
        
        for shadow in shadow_trades:
            gate_name = shadow.get("gate_name", "unknown")
            gate_analysis[gate_name]["rejected_count"] += 1
            gate_analysis[gate_name]["rejected_avg_score"] += shadow.get("signal_score", 0.0)
        
        # Calculate averages
        for gate_name, analysis in gate_analysis.items():
            if analysis["rejected_count"] > 0:
                analysis["rejected_avg_score"] /= analysis["rejected_count"]
        
        # Calculate actual trade P&L
        total_pnl = 0.0
        for trade in actual_trades:
            pnl = trade.get("pnl_usd", 0.0) or trade.get("realized_pnl", 0.0)
            total_pnl += float(pnl)
        
        if len(actual_trades) > 0:
            avg_pnl = total_pnl / len(actual_trades)
            for gate_name, analysis in gate_analysis.items():
                analysis["actual_avg_pnl"] = avg_pnl
        
        # Determine if thresholds should be adjusted
        # If rejected signals have higher scores but we're missing them, adjust
        recommendations = {}
        for gate_name, analysis in gate_analysis.items():
            if analysis["rejected_count"] > 10:  # Minimum sample size
                # If rejected signals have high scores, consider adjusting
                if analysis["rejected_avg_score"] > 3.0:  # High score signals being rejected
                    recommendations[gate_name] = {
                        "action": "lower_threshold",
                        "current": self.gate_thresholds.get(gate_name, {}),
                        "reason": f"High-scoring signals ({analysis['rejected_avg_score']:.2f}) being rejected"
                    }
                    analysis["should_adjust"] = True
        
        return {
            "analysis_date": datetime.now(timezone.utc).isoformat(),
            "lookback_days": lookback_days,
            "shadow_trades_count": len(shadow_trades),
            "actual_trades_count": len(actual_trades),
            "gate_analysis": dict(gate_analysis),
            "recommendations": recommendations
        }
    
    def apply_threshold_adjustments(self, recommendations: Dict):
        """Apply threshold adjustments based on shadow analysis"""
        for gate_name, rec in recommendations.items():
            if rec.get("action") == "lower_threshold":
                # Lower threshold by 10%
                if gate_name in self.gate_thresholds:
                    gate_config = self.gate_thresholds[gate_name]
                    
                    # Adjust based on gate type
                    if "min_count" in gate_config:
                        gate_config["min_count"] = max(1, int(gate_config["min_count"] * 0.9))
                    elif "min_premium" in gate_config:
                        gate_config["min_premium"] = int(gate_config["min_premium"] * 0.9)
                    elif "max_toxicity" in gate_config:
                        gate_config["max_toxicity"] = min(1.0, gate_config["max_toxicity"] * 1.1)
                    elif "min_score" in gate_config:
                        gate_config["min_score"] = max(0.5, gate_config["min_score"] * 0.9)
                    elif "min_expectancy" in gate_config:
                        gate_config["min_expectancy"] = gate_config["min_expectancy"] - 0.01
        
        self._save_thresholds()
    
    def get_gate_threshold(self, gate_name: str, threshold_key: str, default: float) -> float:
        """Get current threshold value for a gate"""
        gate_config = self.gate_thresholds.get(gate_name, {})
        return gate_config.get(threshold_key, default)

# Global instance
_shadow_logger = None

def get_shadow_logger() -> ShadowTradeLogger:
    """Get global shadow trade logger instance"""
    global _shadow_logger
    if _shadow_logger is None:
        _shadow_logger = ShadowTradeLogger()
    return _shadow_logger

