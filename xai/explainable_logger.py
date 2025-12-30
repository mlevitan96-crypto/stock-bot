#!/usr/bin/env python3
"""
Explainable AI (XAI) Logger
Records natural-language "Why" sentences for every trade and weight adjustment.
References: HMM Regime, FRED Macro levels, UW Whale clusters, dealer Gamma Walls.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, List, Any

DATA_DIR = Path("data")
EXPLAINABLE_LOG_FILE = DATA_DIR / "explainable_logs.jsonl"

class ExplainableLogger:
    """Records natural language explanations for all trading decisions."""
    
    def __init__(self):
        self.log_file = EXPLAINABLE_LOG_FILE
        self._ensure_dir()
    
    def _ensure_dir(self):
        """Ensure data directory exists"""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _append_log(self, record: Dict):
        """Append record to explainable log"""
        record["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record) + "\n")
    
    def log_trade_entry(self, symbol: str, direction: str, score: float, 
                       components: Dict, regime: str, macro_yield: Optional[float],
                       whale_clusters: Dict, gamma_walls: Optional[Dict],
                       composite_score: float, entry_price: float) -> str:
        """
        Log trade entry with natural language explanation.
        Returns: Natural language "Why" sentence
        """
        # Build explanation components
        why_parts = []
        
        # Regime component
        if regime:
            regime_desc = {
                "RISK_ON": "bullish market regime",
                "RISK_OFF": "bearish market regime",
                "NEUTRAL": "neutral market regime",
                "PANIC": "panic market regime"
            }.get(regime, f"{regime} regime")
            why_parts.append(f"HMM detected {regime_desc}")
        
        # Macro component
        if macro_yield is not None:
            if macro_yield > 5.0:
                why_parts.append(f"FRED Treasury Yields at {macro_yield:.2f}% (high, penalizing growth)")
            elif macro_yield < 3.0:
                why_parts.append(f"FRED Treasury Yields at {macro_yield:.2f}% (low, favoring growth)")
            else:
                why_parts.append(f"FRED Treasury Yields at {macro_yield:.2f}% (neutral)")
        
        # Whale clusters component
        if whale_clusters:
            cluster_count = whale_clusters.get("count", 0)
            cluster_premium = whale_clusters.get("premium_usd", 0)
            if cluster_count > 0:
                why_parts.append(f"UW Whale clusters: {cluster_count} clusters with ${cluster_premium:,.0f} premium")
        
        # Gamma walls component
        if gamma_walls:
            wall_distance = gamma_walls.get("distance_pct", None)
            wall_gamma = gamma_walls.get("gamma_exposure", 0)
            if wall_distance is not None and wall_distance < 0.05:
                why_parts.append(f"Near Gamma Call Wall ({wall_distance*100:.1f}% away, ${wall_gamma:,.0f} exposure)")
        
        # Component scores
        top_components = sorted(
            [(k, v) for k, v in components.items() if v > 0],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        if top_components:
            comp_descs = [f"{name} ({val:.2f})" for name, val in top_components]
            why_parts.append(f"Top signals: {', '.join(comp_descs)}")
        
        # Composite score
        why_parts.append(f"Composite score: {composite_score:.2f}")
        
        # Build final sentence
        why_sentence = f"Entered {direction.upper()} {symbol} because: " + ". ".join(why_parts) + "."
        
        # Log record
        record = {
            "type": "trade_entry",
            "symbol": symbol,
            "direction": direction,
            "entry_price": entry_price,
            "composite_score": composite_score,
            "score": score,
            "regime": regime,
            "macro_yield": macro_yield,
            "whale_clusters": whale_clusters,
            "gamma_walls": gamma_walls,
            "components": components,
            "why": why_sentence
        }
        
        self._append_log(record)
        
        return why_sentence
    
    def log_trade_exit(self, symbol: str, entry_price: float, exit_price: float,
                      pnl_pct: float, hold_minutes: float, exit_reason: str,
                      regime: str, gamma_walls: Optional[Dict]) -> str:
        """
        Log trade exit with natural language explanation.
        Returns: Natural language "Why" sentence
        """
        why_parts = []
        
        # Exit reason
        if "gamma_call_wall" in exit_reason.lower():
            why_parts.append("reached Gamma Call Wall (structural physics exit)")
        elif "liquidity_exhaustion" in exit_reason.lower():
            why_parts.append("bid-side liquidity exhausted (structural physics exit)")
        elif "profit_target" in exit_reason.lower():
            why_parts.append("profit target reached")
        elif "stop_loss" in exit_reason.lower():
            why_parts.append("stop loss triggered")
        elif "time_exit" in exit_reason.lower():
            why_parts.append("maximum hold time reached")
        else:
            why_parts.append(f"exit reason: {exit_reason}")
        
        # Regime
        if regime:
            regime_desc = {
                "RISK_ON": "bullish",
                "RISK_OFF": "bearish",
                "NEUTRAL": "neutral",
                "PANIC": "panic"
            }.get(regime, regime)
            why_parts.append(f"market in {regime_desc} regime")
        
        # P&L
        pnl_desc = "profit" if pnl_pct > 0 else "loss"
        why_parts.append(f"{pnl_desc} of {abs(pnl_pct):.2f}% over {hold_minutes:.0f} minutes")
        
        # Gamma walls at exit
        if gamma_walls:
            wall_distance = gamma_walls.get("distance_pct", None)
            if wall_distance is not None and wall_distance < 0.02:
                why_parts.append(f"exited near Gamma Call Wall ({wall_distance*100:.1f}% away)")
        
        why_sentence = f"Exited {symbol} because: " + ". ".join(why_parts) + "."
        
        record = {
            "type": "trade_exit",
            "symbol": symbol,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl_pct": pnl_pct,
            "hold_minutes": hold_minutes,
            "exit_reason": exit_reason,
            "regime": regime,
            "gamma_walls": gamma_walls,
            "why": why_sentence
        }
        
        self._append_log(record)
        
        return why_sentence
    
    def log_threshold_adjustment(self, symbol: str, base_threshold: float, 
                                adjusted_threshold: float, reason: str, status: Dict) -> str:
        """
        Log threshold adjustment with natural language explanation.
        
        Args:
            symbol: Symbol being evaluated
            base_threshold: Base threshold (e.g., 2.0)
            adjusted_threshold: Adjusted threshold (e.g., 2.5)
            reason: Reason for adjustment
            status: Status dict from SelfHealingThreshold
        
        Returns: Natural language "Why" sentence
        """
        adjustment = adjusted_threshold - base_threshold
        consecutive_losses = status.get("consecutive_losses", 0)
        
        why_sentence = (
            f"Threshold raised from {base_threshold:.1f} to {adjusted_threshold:.1f} "
            f"for {symbol} because last {consecutive_losses} trades were losses. "
            f"Bot is being more cautious to prevent further losses."
        )
        
        record = {
            "type": "threshold_adjustment",
            "symbol": symbol,
            "base_threshold": base_threshold,
            "adjusted_threshold": adjusted_threshold,
            "adjustment": adjustment,
            "reason": reason,
            "consecutive_losses": consecutive_losses,
            "is_activated": status.get("is_activated", False),
            "why_sentence": why_sentence
        }
        
        self._append_log(record)
        return why_sentence
    
    def log_weight_adjustment(self, component: str, old_weight: float, new_weight: float,
                             reason: str, sample_count: int, win_rate: float,
                             regime: str, pnl_contribution: float) -> str:
        """
        Log weight adjustment with natural language explanation.
        Returns: Natural language "Why" sentence
        """
        why_parts = []
        
        # Adjustment direction
        if new_weight > old_weight:
            direction = "increased"
            change_pct = ((new_weight - old_weight) / old_weight) * 100
        elif new_weight < old_weight:
            direction = "decreased"
            change_pct = ((old_weight - new_weight) / old_weight) * 100
        else:
            direction = "maintained"
            change_pct = 0.0
        
        why_parts.append(f"{direction} weight from {old_weight:.2f} to {new_weight:.2f} ({change_pct:+.1f}%)")
        
        # Reason
        if "thompson" in reason.lower():
            why_parts.append("Thompson Sampling optimization")
        elif "wilson" in reason.lower():
            why_parts.append("Wilson confidence interval exceeded 95%")
        elif "sample" in reason.lower():
            why_parts.append(f"minimum sample size reached ({sample_count} trades)")
        
        # Performance metrics
        why_parts.append(f"win rate: {win_rate*100:.1f}% from {sample_count} samples")
        
        if pnl_contribution != 0:
            pnl_desc = "positive" if pnl_contribution > 0 else "negative"
            why_parts.append(f"{pnl_desc} P&L contribution: {pnl_contribution:.2f}%")
        
        # Regime context
        if regime:
            regime_desc = {
                "RISK_ON": "bullish",
                "RISK_OFF": "bearish",
                "NEUTRAL": "neutral",
                "PANIC": "panic"
            }.get(regime, regime)
            why_parts.append(f"regime: {regime_desc}")
        
        why_sentence = f"Adjusted {component} weight because: " + ". ".join(why_parts) + "."
        
        record = {
            "type": "weight_adjustment",
            "component": component,
            "old_weight": old_weight,
            "new_weight": new_weight,
            "reason": reason,
            "sample_count": sample_count,
            "win_rate": win_rate,
            "regime": regime,
            "pnl_contribution": pnl_contribution,
            "why": why_sentence
        }
        
        self._append_log(record)
        
        return why_sentence
    
    def get_recent_logs(self, limit: int = 100, log_type: Optional[str] = None) -> List[Dict]:
        """Get recent explainable logs"""
        if not self.log_file.exists():
            return []
        
        logs = []
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        rec = json.loads(line)
                        if log_type is None or rec.get("type") == log_type:
                            logs.append(rec)
                    except:
                        continue
        
        # Return most recent first
        return logs[-limit:][::-1]
    
    def get_trade_explanations(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get trade explanations (entries and exits) - filters out test symbols"""
        logs = self.get_recent_logs(limit * 2)
        trade_logs = [log for log in logs if log.get("type") in ("trade_entry", "trade_exit")]
        
        # CRITICAL: Filter out test symbols (TEST, FAKE, etc.)
        trade_logs = [log for log in trade_logs if log.get("symbol") and "TEST" not in str(log.get("symbol", "")).upper()]
        
        if symbol:
            trade_logs = [log for log in trade_logs if log.get("symbol") == symbol]
        
        return trade_logs[:limit]
    
    def get_weight_explanations(self, component: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get weight adjustment explanations"""
        logs = self.get_recent_logs(limit * 2)
        weight_logs = [log for log in logs if log.get("type") == "weight_adjustment"]
        
        if component:
            weight_logs = [log for log in weight_logs if log.get("component") == component]
        
        return weight_logs[:limit]

# Global instance
_explainable_logger = None

def get_explainable_logger() -> ExplainableLogger:
    """Get global explainable logger instance"""
    global _explainable_logger
    if _explainable_logger is None:
        _explainable_logger = ExplainableLogger()
    return _explainable_logger

