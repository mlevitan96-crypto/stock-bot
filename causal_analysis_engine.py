#!/usr/bin/env python3
"""
Causal Analysis Engine - Deep Learning & Reasoning System

Answers the "WHY" behind wins and losses, not just "what happened".

Analyzes:
1. Market conditions (regime, volatility, time of day)
2. Feature combinations (which signals work together)
3. Context patterns (what conditions lead to success/failure)
4. Root cause investigation (deep dive into losing trades)

This enables PREDICTIVE understanding, not just reactive adjustments.
"""

import json
import math
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import statistics

STATE_DIR = Path("state")
DATA_DIR = Path("data")
LOGS_DIR = Path("logs")

ATTRIBUTION_LOG = LOGS_DIR / "attribution.jsonl"
CAUSAL_ANALYSIS_STATE = STATE_DIR / "causal_analysis_state.json"
CAUSAL_INSIGHTS = DATA_DIR / "causal_insights.jsonl"

class CausalAnalysisEngine:
    """
    Deep learning system that investigates WHY signals win or lose.
    
    Goes beyond simple win/loss tracking to understand:
    - What market conditions favor each signal
    - Which feature combinations are predictive
    - What patterns lead to success vs failure
    - Root causes of underperformance
    """
    
    def __init__(self):
        self.state_file = CAUSAL_ANALYSIS_STATE
        self.insights_file = CAUSAL_INSIGHTS
        self.state = self._load_state()
        
        # Analysis dimensions
        self.context_dimensions = [
            "market_regime",      # RISK_ON, RISK_OFF, NEUTRAL, MIXED
            "volatility_regime",  # LOW_VOL, NORMAL_VOL, HIGH_VOL
            "time_of_day",       # PRE_MARKET, OPEN, MID_DAY, CLOSE, AFTER_HOURS
            "day_of_week",       # MONDAY, TUESDAY, etc.
            "sector",            # TECH, FINANCE, ENERGY, etc.
            "market_trend",      # BULLISH, BEARISH, SIDEWAYS
            "iv_rank",           # LOW (<30), MEDIUM (30-70), HIGH (>70)
            "flow_magnitude",    # LOW, MEDIUM, HIGH
            "signal_strength",   # WEAK, MODERATE, STRONG
        ]
        
    def _load_state(self) -> Dict:
        """Load analysis state"""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except:
                pass
        return {
            "trade_contexts": {},  # trade_id -> context
            "component_patterns": {},  # component -> {context -> {wins, losses, pnl}}
            "feature_combinations": {},  # combination_hash -> {wins, losses, pnl}
            "root_cause_analysis": {},  # component -> {failure_patterns: [], success_patterns: []}
            "last_analysis_ts": 0
        }
    
    def _save_state(self):
        """Save analysis state"""
        self.state_file.parent.mkdir(exist_ok=True)
        with self.state_file.open("w") as f:
            json.dump(self.state, f, indent=2)
    
    def extract_trade_context(self, trade: Dict) -> Dict[str, Any]:
        """
        Extract full context for a trade.
        
        This is the foundation - we need to capture EVERYTHING that might explain why it won/lost.
        """
        context = trade.get("context", {})
        components = context.get("components", {})
        
        # Market regime
        market_regime = context.get("market_regime", "unknown")
        
        # Time-based context
        entry_ts = trade.get("ts", "")
        if isinstance(entry_ts, str):
            try:
                entry_dt = datetime.fromisoformat(entry_ts.replace("Z", "+00:00"))
            except:
                entry_dt = datetime.now(timezone.utc)
        else:
            entry_dt = datetime.fromtimestamp(entry_ts, tz=timezone.utc)
        
        hour = entry_dt.hour
        if hour < 9 or hour >= 16:
            time_of_day = "AFTER_HOURS"
        elif hour == 9:
            time_of_day = "OPEN"
        elif hour >= 15:
            time_of_day = "CLOSE"
        else:
            time_of_day = "MID_DAY"
        
        day_of_week = entry_dt.strftime("%A").upper()
        
        # Signal characteristics
        entry_score = context.get("entry_score", 0.0)
        if entry_score < 2.5:
            signal_strength = "WEAK"
        elif entry_score < 3.5:
            signal_strength = "MODERATE"
        else:
            signal_strength = "STRONG"
        
        # Flow magnitude (handle both "flow" and "options_flow" names)
        flow_comp = components.get("flow") or components.get("options_flow")
        if isinstance(flow_comp, dict):
            flow_conv = flow_comp.get("conviction", 0.0)
        elif isinstance(flow_comp, (int, float)):
            flow_conv = float(flow_comp)
        else:
            flow_conv = 0.0
        if flow_conv < 0.3:
            flow_magnitude = "LOW"
        elif flow_conv < 0.7:
            flow_magnitude = "MEDIUM"
        else:
            flow_magnitude = "HIGH"
        
        # IV rank (if available)
        iv_rank = context.get("iv_rank", 50)
        if iv_rank < 30:
            iv_regime = "LOW"
        elif iv_rank > 70:
            iv_regime = "HIGH"
        else:
            iv_regime = "MEDIUM"
        
        # Volatility regime (infer from context or use default)
        volatility_regime = context.get("volatility_regime", "NORMAL_VOL")
        
        # Market trend (infer from flow sentiment)
        flow_comp = components.get("flow") or components.get("options_flow")
        if isinstance(flow_comp, dict):
            flow_sentiment = flow_comp.get("sentiment", "NEUTRAL")
        else:
            flow_sentiment = "NEUTRAL"
        if flow_sentiment in ("BULLISH", "VERY_BULLISH"):
            market_trend = "BULLISH"
        elif flow_sentiment in ("BEARISH", "VERY_BEARISH"):
            market_trend = "BEARISH"
        else:
            market_trend = "SIDEWAYS"
        
        # Sector (if available)
        sector = context.get("sector", "UNKNOWN")
        
        return {
            "market_regime": market_regime,
            "volatility_regime": volatility_regime,
            "time_of_day": time_of_day,
            "day_of_week": day_of_week,
            "sector": sector,
            "market_trend": market_trend,
            "iv_rank": iv_regime,
            "flow_magnitude": flow_magnitude,
            "signal_strength": signal_strength,
            "entry_score": entry_score,
            "hour": hour,
        }
    
    def analyze_trade(self, trade: Dict):
        """
        Analyze a single trade to understand WHY it won or lost.
        
        Stores context and patterns for later deep analysis.
        """
        trade_id = trade.get("trade_id", "")
        if not trade_id or trade_id.startswith("open_"):
            return
        
        pnl_usd = trade.get("pnl_usd", 0.0)
        pnl_pct = trade.get("pnl_pct", 0.0) if "pnl_pct" in trade else (pnl_usd / 100.0)  # Rough estimate
        win = pnl_usd > 0
        
        context = self.extract_trade_context(trade)
        components = trade.get("context", {}).get("components", {})
        
        # V4.1: Normalize component names to match SIGNAL_COMPONENTS
        # Attribution data may use "flow" but we need "options_flow"
        normalized_components = self._normalize_component_names(components)
        
        # Store trade context
        self.state["trade_contexts"][trade_id] = {
            "context": context,
            "pnl_usd": pnl_usd,
            "pnl_pct": pnl_pct,
            "win": win,
            "components": normalized_components,
            "ts": trade.get("ts", "")
        }
        
        # Analyze each component in context
        for comp_name, comp_value in normalized_components.items():
            if comp_name not in self.state["component_patterns"]:
                self.state["component_patterns"][comp_name] = {}
            
            # Create context key (combination of relevant dimensions)
            context_key = self._create_context_key(context, comp_name)
            
            if context_key not in self.state["component_patterns"][comp_name]:
                self.state["component_patterns"][comp_name][context_key] = {
                    "wins": 0,
                    "losses": 0,
                    "total_pnl": 0.0,
                    "samples": []
                }
            
            pattern = self.state["component_patterns"][comp_name][context_key]
            if win:
                pattern["wins"] += 1
            else:
                pattern["losses"] += 1
            pattern["total_pnl"] += pnl_pct
            pattern["samples"].append({
                "trade_id": trade_id,
                "pnl_pct": pnl_pct,
                "value": comp_value,
                "context": context
            })
            
            # Keep only last 100 samples per pattern (prevent memory bloat)
            if len(pattern["samples"]) > 100:
                pattern["samples"] = pattern["samples"][-100:]
        
        # Analyze feature combinations
        self._analyze_feature_combinations(trade, context, win, pnl_pct)
    
    def _create_context_key(self, context: Dict, component: str) -> str:
        """
        Create a context key that captures relevant conditions for this component.
        
        Different components may be sensitive to different conditions.
        """
        # Base context (always include)
        key_parts = [
            f"regime:{context.get('market_regime', 'unknown')}",
            f"time:{context.get('time_of_day', 'unknown')}",
        ]
        
        # Component-specific context
        if component in ("options_flow", "dark_pool", "institutional"):
            # Flow signals sensitive to market trend and flow magnitude
            key_parts.append(f"trend:{context.get('market_trend', 'unknown')}")
            key_parts.append(f"flow_mag:{context.get('flow_magnitude', 'unknown')}")
        
        if component in ("iv_term_skew", "iv_rank", "smile_slope"):
            # IV signals sensitive to volatility regime
            key_parts.append(f"iv_regime:{context.get('iv_rank', 'unknown')}")
            key_parts.append(f"vol_regime:{context.get('volatility_regime', 'unknown')}")
        
        if component in ("congress", "insider", "institutional"):
            # Insider signals may be sector-sensitive
            key_parts.append(f"sector:{context.get('sector', 'unknown')}")
        
        return "|".join(key_parts)
    
    def _analyze_feature_combinations(self, trade: Dict, context: Dict, win: bool, pnl_pct: float):
        """Analyze which combinations of features lead to wins/losses"""
        components = trade.get("context", {}).get("components", {})
        # Normalize component names for combination analysis
        components = self._normalize_component_names(components)
        
        # Find active features (non-zero values)
        active_features = [name for name, value in components.items() 
                          if value and (isinstance(value, (int, float)) and value != 0 or 
                                       isinstance(value, dict) and any(v != 0 for v in value.values() if isinstance(v, (int, float))))]
        
        if len(active_features) < 2:
            return  # Need at least 2 features for combination analysis
        
        # Create combination signature (sorted for consistency)
        combination = tuple(sorted(active_features))
        combo_key = "&".join(combination)
        
        if combo_key not in self.state["feature_combinations"]:
            self.state["feature_combinations"][combo_key] = {
                "features": combination,
                "wins": 0,
                "losses": 0,
                "total_pnl": 0.0,
                "contexts": [],
                "samples": []
            }
        
        combo = self.state["feature_combinations"][combo_key]
        if win:
            combo["wins"] += 1
        else:
            combo["losses"] += 1
        combo["total_pnl"] += pnl_pct
        combo["contexts"].append(context)
        combo["samples"].append({
            "trade_id": trade.get("trade_id", ""),
            "pnl_pct": pnl_pct,
            "win": win
        })
        
        # Keep last 50 samples
        if len(combo["samples"]) > 50:
            combo["samples"] = combo["samples"][-50:]
            combo["contexts"] = combo["contexts"][-50:]
    
    def investigate_component(self, component: str) -> Dict[str, Any]:
        """
        Deep investigation: WHY does this component win or lose?
        
        Returns root cause analysis with specific conditions that lead to success/failure.
        """
        if component not in self.state["component_patterns"]:
            return {"error": f"No data for component: {component}"}
        
        patterns = self.state["component_patterns"][component]
        
        # Analyze each context pattern
        success_patterns = []
        failure_patterns = []
        
        for context_key, pattern in patterns.items():
            wins = pattern["wins"]
            losses = pattern["losses"]
            total = wins + losses
            
            if total < 3:  # Need minimum samples
                continue
            
            win_rate = wins / total if total > 0 else 0
            avg_pnl = pattern["total_pnl"] / total if total > 0 else 0
            
            # Success pattern: high win rate AND positive P&L
            # V4.1: Lower threshold to find more patterns (was 0.6, now 0.55)
            if win_rate >= 0.55 and avg_pnl > 0.005:
                success_patterns.append({
                    "context": context_key,
                    "win_rate": win_rate,
                    "avg_pnl": avg_pnl,
                    "samples": total,
                    "conditions": self._parse_context_key(context_key)
                })
            
            # Failure pattern: low win rate OR negative P&L
            if win_rate < 0.4 or avg_pnl < -0.01:
                failure_patterns.append({
                    "context": context_key,
                    "win_rate": win_rate,
                    "avg_pnl": avg_pnl,
                    "samples": total,
                    "conditions": self._parse_context_key(context_key)
                })
        
        # Sort by impact (samples * |avg_pnl|)
        success_patterns.sort(key=lambda x: x["samples"] * abs(x["avg_pnl"]), reverse=True)
        failure_patterns.sort(key=lambda x: x["samples"] * abs(x["avg_pnl"]), reverse=True)
        
        # Analyze feature combinations involving this component
        relevant_combos = []
        for combo_key, combo in self.state["feature_combinations"].items():
            if component in combo["features"]:
                total = combo["wins"] + combo["losses"]
                if total >= 3:
                    win_rate = combo["wins"] / total
                    avg_pnl = combo["total_pnl"] / total
                    relevant_combos.append({
                        "combination": combo["features"],
                        "win_rate": win_rate,
                        "avg_pnl": avg_pnl,
                        "samples": total
                    })
        
        relevant_combos.sort(key=lambda x: x["samples"] * abs(x["avg_pnl"]), reverse=True)
        
        return {
            "component": component,
            "success_patterns": success_patterns[:5],  # Top 5
            "failure_patterns": failure_patterns[:5],  # Top 5
            "feature_combinations": relevant_combos[:5],  # Top 5
            "total_contexts": len(patterns),
            "analysis_ts": datetime.now(timezone.utc).isoformat()
        }
    
    def _parse_context_key(self, context_key: str) -> Dict[str, str]:
        """Parse context key into readable conditions"""
        conditions = {}
        for part in context_key.split("|"):
            if ":" in part:
                key, value = part.split(":", 1)
                conditions[key] = value
        return conditions
    
    def _normalize_component_names(self, components: Dict) -> Dict:
        """
        Normalize component names from attribution format to SIGNAL_COMPONENTS format.
        
        Handles:
        - "flow" -> "options_flow"
        - "iv_skew" -> "iv_term_skew"
        - "smile" -> "smile_slope"
        - Components stored as dicts (extract value)
        """
        from adaptive_signal_optimizer import SIGNAL_COMPONENTS
        
        # Component name mapping (from attribution format to SIGNAL_COMPONENTS)
        name_map = {
            "flow": "options_flow",
            "iv_skew": "iv_term_skew",
            "smile": "smile_slope",
            "whale": "whale_persistence",
            "event": "event_alignment",
            "regime": "regime_modifier",
            "calendar": "calendar_catalyst",
            "motif_bonus": "temporal_motif",
            # Direct matches (no change needed)
            "dark_pool": "dark_pool",
            "insider": "insider",
            "toxicity_penalty": "toxicity_penalty",
            "congress": "congress",
            "shorts_squeeze": "shorts_squeeze",
            "institutional": "institutional",
            "market_tide": "market_tide",
            "greeks_gamma": "greeks_gamma",
            "ftd_pressure": "ftd_pressure",
            "iv_rank": "iv_rank",
            "oi_change": "oi_change",
            "etf_flow": "etf_flow",
            "squeeze_score": "squeeze_score",
        }
        
        normalized = {}
        
        for comp_name, comp_value in components.items():
            # Handle components stored as dicts (e.g., {"flow": {"conviction": 0.5}})
            if isinstance(comp_value, dict):
                # Extract numeric value from dict
                if "conviction" in comp_value:
                    value = comp_value.get("conviction", 0.0)
                elif "value" in comp_value:
                    value = comp_value.get("value", 0.0)
                else:
                    # Try to find first numeric value
                    value = next((v for v in comp_value.values() if isinstance(v, (int, float))), 0.0)
            else:
                value = comp_value if isinstance(comp_value, (int, float)) else 0.0
            
            # Map component name
            mapped_name = name_map.get(comp_name, comp_name)
            
            # Only include if it's a valid SIGNAL_COMPONENT
            if mapped_name in SIGNAL_COMPONENTS:
                normalized[mapped_name] = value
        
        return normalized
    
    def generate_insights(self) -> Dict[str, Any]:
        """
        Generate actionable insights: WHY signals win/lose and WHEN to use them.
        
        This is the key output - tells us not just what happened, but WHY and WHEN.
        """
        insights = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "component_insights": {},
            "feature_combination_insights": {},
            "recommendations": []
        }
        
        # Analyze each component
        from adaptive_signal_optimizer import SIGNAL_COMPONENTS
        
        for component in SIGNAL_COMPONENTS:
            investigation = self.investigate_component(component)
            if "error" not in investigation:
                insights["component_insights"][component] = investigation
                
                # Generate recommendations
                if investigation["success_patterns"]:
                    top_success = investigation["success_patterns"][0]
                    insights["recommendations"].append({
                        "component": component,
                        "type": "USE_WHEN",
                        "condition": top_success["conditions"],
                        "reason": f"Win rate: {top_success['win_rate']:.1%}, Avg P&L: {top_success['avg_pnl']:.2%}",
                        "confidence": min(top_success["samples"] / 10.0, 1.0)
                    })
                
                if investigation["failure_patterns"]:
                    top_failure = investigation["failure_patterns"][0]
                    insights["recommendations"].append({
                        "component": component,
                        "type": "AVOID_WHEN",
                        "condition": top_failure["conditions"],
                        "reason": f"Win rate: {top_failure['win_rate']:.1%}, Avg P&L: {top_failure['avg_pnl']:.2%}",
                        "confidence": min(top_failure["samples"] / 10.0, 1.0)
                    })
        
        # Analyze feature combinations
        for combo_key, combo in list(self.state["feature_combinations"].items())[:20]:
            total = combo["wins"] + combo["losses"]
            if total >= 5:
                win_rate = combo["wins"] / total
                avg_pnl = combo["total_pnl"] / total
                
                if win_rate >= 0.65 or avg_pnl > 0.02:
                    insights["feature_combination_insights"][combo_key] = {
                        "features": combo["features"],
                        "win_rate": win_rate,
                        "avg_pnl": avg_pnl,
                        "samples": total,
                        "recommendation": "PROMISING_COMBINATION"
                    }
                elif win_rate < 0.35 or avg_pnl < -0.02:
                    insights["feature_combination_insights"][combo_key] = {
                        "features": combo["features"],
                        "win_rate": win_rate,
                        "avg_pnl": avg_pnl,
                        "samples": total,
                        "recommendation": "AVOID_COMBINATION"
                    }
        
        # Save insights
        self.insights_file.parent.mkdir(exist_ok=True)
        with self.insights_file.open("a") as f:
            f.write(json.dumps(insights) + "\n")
        
        return insights
    
    def process_all_trades(self, limit: Optional[int] = None):
        """Process all historical trades for causal analysis"""
        if not ATTRIBUTION_LOG.exists():
            return {"processed": 0, "error": "attribution.jsonl not found"}
        
        processed = 0
        with ATTRIBUTION_LOG.open("r") as f:
            for line in f:
                if limit and processed >= limit:
                    break
                
                if not line.strip():
                    continue
                
                try:
                    trade = json.loads(line)
                    if trade.get("type") == "attribution":
                        trade_id = trade.get("trade_id", "")
                        if trade_id and not trade_id.startswith("open_"):
                            self.analyze_trade(trade)
                            processed += 1
                except Exception as e:
                    continue
        
        self._save_state()
        return {"processed": processed}
    
    def answer_why(self, component: str, question: str = "why_underperforming") -> Dict[str, Any]:
        """
        Answer specific questions about component performance.
        
        Questions:
        - "why_underperforming": Why is this component losing?
        - "when_works_best": When does this component work best?
        - "what_conditions_fail": What conditions cause failures?
        """
        investigation = self.investigate_component(component)
        
        if "error" in investigation:
            return investigation
        
        if question == "why_underperforming":
            if not investigation["failure_patterns"]:
                return {
                    "component": component,
                    "answer": "No clear failure patterns identified yet. Need more data.",
                    "patterns": []
                }
            
            top_failure = investigation["failure_patterns"][0]
            conditions = top_failure["conditions"]
            
            answer_parts = [f"{component} underperforms when:"]
            for key, value in conditions.items():
                answer_parts.append(f"  - {key}: {value}")
            answer_parts.append(f"\nEvidence: {top_failure['samples']} trades, {top_failure['win_rate']:.1%} win rate, {top_failure['avg_pnl']:.2%} avg P&L")
            
            return {
                "component": component,
                "answer": "\n".join(answer_parts),
                "failure_patterns": investigation["failure_patterns"][:3],
                "recommendation": f"Avoid using {component} when: {', '.join(f'{k}={v}' for k, v in conditions.items())}"
            }
        
        elif question == "when_works_best":
            if not investigation["success_patterns"]:
                return {
                    "component": component,
                    "answer": "No clear success patterns identified yet. Need more data.",
                    "patterns": []
                }
            
            top_success = investigation["success_patterns"][0]
            conditions = top_success["conditions"]
            
            answer_parts = [f"{component} works best when:"]
            for key, value in conditions.items():
                answer_parts.append(f"  - {key}: {value}")
            answer_parts.append(f"\nEvidence: {top_success['samples']} trades, {top_success['win_rate']:.1%} win rate, {top_success['avg_pnl']:.2%} avg P&L")
            
            return {
                "component": component,
                "answer": "\n".join(answer_parts),
                "success_patterns": investigation["success_patterns"][:3],
                "recommendation": f"Use {component} when: {', '.join(f'{k}={v}' for k, v in conditions.items())}"
            }
        
        elif question == "what_conditions_fail":
            return {
                "component": component,
                "failure_conditions": investigation["failure_patterns"],
                "summary": f"Found {len(investigation['failure_patterns'])} failure patterns"
            }
        
        return {"error": f"Unknown question: {question}"}


def main():
    """Run causal analysis"""
    engine = CausalAnalysisEngine()
    
    print("="*80)
    print("CAUSAL ANALYSIS ENGINE")
    print("="*80)
    
    # Process all trades
    print("\n1. Processing historical trades...")
    result = engine.process_all_trades()
    print(f"   Processed: {result.get('processed', 0)} trades")
    
    # Generate insights
    print("\n2. Generating insights...")
    insights = engine.generate_insights()
    print(f"   Components analyzed: {len(insights['component_insights'])}")
    print(f"   Recommendations: {len(insights['recommendations'])}")
    
    # Answer key questions
    print("\n3. Answering WHY questions...")
    from adaptive_signal_optimizer import SIGNAL_COMPONENTS
    
    for component in ["options_flow", "dark_pool", "insider"]:  # Top components
        if component in SIGNAL_COMPONENTS:
            print(f"\n   {component.upper()}:")
            why_answer = engine.answer_why(component, "why_underperforming")
            if "answer" in why_answer:
                print(f"   {why_answer['answer']}")
            
            when_answer = engine.answer_why(component, "when_works_best")
            if "answer" in when_answer:
                print(f"   {when_answer['answer']}")
    
    print("\n" + "="*80)
    print("Analysis complete. Insights saved to:", CAUSAL_INSIGHTS)
    print("="*80)


if __name__ == "__main__":
    main()
