#!/usr/bin/env python3
"""
Adaptive Signal Weight Optimization System (V1.0)

Continuous signal weight tuning with directional conviction engine.
Replaces binary signal activation with adaptive multipliers (0.25x-2.5x).

Architecture:
1. SignalWeightModel - Continuous weight bands for all 11+ signal components
2. DirectionalConvictionEngine - Aggregates bullish/bearish into net long/short conviction
3. ExitSignalModel - Separate adaptive weights for exit decisions
4. LearningOrchestrator - Bayesian updates with EWMA smoothing and anti-overfitting

Integration:
- Reads from Feature Store (data/feature_store.jsonl)
- Persists state to state/signal_weights.json
- Exports live weights for uw_composite_v2.py consumption
"""

import json
import math
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import time
from dataclasses import dataclass, field, asdict

STATE_DIR = Path("state")
DATA_DIR = Path("data")
WEIGHTS_STATE_FILE = STATE_DIR / "signal_weights.json"
FEATURE_STORE_FILE = DATA_DIR / "feature_store.jsonl"
LEARNING_LOG_FILE = DATA_DIR / "weight_learning.jsonl"

SIGNAL_COMPONENTS = [
    "options_flow",
    "dark_pool", 
    "insider",
    "iv_term_skew",
    "smile_slope",
    "whale_persistence",
    "event_alignment",
    "temporal_motif",
    "toxicity_penalty",
    "regime_modifier",
    "congress",
    "shorts_squeeze",
    "institutional",
    "market_tide",
    "calendar_catalyst",
    "etf_flow",
    "greeks_gamma",
    "ftd_pressure",
    "iv_rank",
    "oi_change",
    "squeeze_score",
]

EXIT_COMPONENTS = [
    "entry_decay",
    "adverse_flow",
    "drawdown_velocity",
    "time_decay",
    "momentum_reversal",
    "volume_exhaustion",
    "support_break",
]

@dataclass
class WeightBand:
    """Continuous weight band with adaptive multiplier"""
    min_weight: float = 0.25
    max_weight: float = 2.5
    neutral: float = 1.0
    current: float = 1.0
    ewma_performance: float = 0.5
    sample_count: int = 0
    wins: int = 0
    losses: int = 0
    total_pnl: float = 0.0
    last_updated: int = 0
    
    def get_effective_weight(self, base_weight: float) -> float:
        """Apply multiplier to base weight"""
        return base_weight * self.current
    
    def clamp(self, value: float) -> float:
        """Clamp value within band limits"""
        return max(self.min_weight, min(self.max_weight, value))


@dataclass
class SignalReading:
    """Individual signal reading with polarity"""
    component: str
    raw_value: float
    polarity: int
    confidence: float = 1.0
    
    @property
    def directional_value(self) -> float:
        return self.raw_value * self.polarity * self.confidence


class SignalWeightModel:
    """
    Manages continuous weight bands for all signal components.
    Weights range from 0.25x (heavily penalized) to 2.5x (heavily boosted).
    """
    
    DEFAULT_BASE_WEIGHTS = {
        "options_flow": 2.4,
        "dark_pool": 1.3,
        "insider": 0.5,
        "iv_term_skew": 0.6,
        "smile_slope": 0.35,
        "whale_persistence": 0.7,
        "event_alignment": 0.4,
        "temporal_motif": 0.5,
        "toxicity_penalty": -0.9,  # MUST be negative - this is a PENALTY that reduces scores
        "regime_modifier": 0.3,
        "congress": 0.9,
        "shorts_squeeze": 0.7,
        "institutional": 0.5,
        "market_tide": 0.4,
        "calendar_catalyst": 0.45,
        "etf_flow": 0.3,
        "greeks_gamma": 0.4,
        "ftd_pressure": 0.3,
        "iv_rank": 0.2,
        "oi_change": 0.35,
        "squeeze_score": 0.2,
    }
    
    def __init__(self):
        self.base_weights = self.DEFAULT_BASE_WEIGHTS.copy()
        self.weight_bands: Dict[str, WeightBand] = {}
        self._init_bands()
        
    def _init_bands(self):
        """Initialize weight bands for all components"""
        for component in SIGNAL_COMPONENTS:
            self.weight_bands[component] = WeightBand(
                min_weight=0.25,
                max_weight=2.5,
                neutral=1.0,
                current=1.0
            )
    
    def get_effective_weight(self, component: str) -> float:
        """Get current effective weight for a component"""
        base = self.base_weights.get(component, 0.5)
        band = self.weight_bands.get(component)
        if band:
            return band.get_effective_weight(base)
        return base
    
    def get_all_effective_weights(self) -> Dict[str, float]:
        """Get all current effective weights"""
        return {c: self.get_effective_weight(c) for c in SIGNAL_COMPONENTS}
    
    def get_multipliers(self) -> Dict[str, float]:
        """Get current multipliers for all components"""
        return {c: self.weight_bands[c].current for c in SIGNAL_COMPONENTS if c in self.weight_bands}
    
    def update_multiplier(self, component: str, new_multiplier: float):
        """Update a component's multiplier within its band"""
        if component in self.weight_bands:
            band = self.weight_bands[component]
            band.current = band.clamp(new_multiplier)
            band.last_updated = int(time.time())
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        return {
            "base_weights": self.base_weights,
            "weight_bands": {k: asdict(v) for k, v in self.weight_bands.items()},
            "updated_at": int(time.time())
        }
    
    def from_dict(self, data: Dict):
        """Deserialize from dictionary"""
        if "base_weights" in data:
            self.base_weights.update(data["base_weights"])
        if "weight_bands" in data:
            for k, v in data["weight_bands"].items():
                if k in self.weight_bands:
                    for field_name, field_val in v.items():
                        if hasattr(self.weight_bands[k], field_name):
                            setattr(self.weight_bands[k], field_name, field_val)


class DirectionalConvictionEngine:
    """
    Aggregates all signal readings into a unified directional conviction.
    Produces net long/short score with confidence intervals.
    """
    
    def __init__(self, weight_model: SignalWeightModel):
        self.weight_model = weight_model
        self.regime_dampeners = {
            "high_volatility": 0.8,
            "low_liquidity": 0.7,
            "mixed_signals": 0.6,
            "strong_trend": 1.2,
            "neutral": 1.0
        }
        self.toxicity_threshold = 0.3
        
    def compute_conviction(self, 
                          signals: List[SignalReading],
                          regime: str = "neutral") -> Dict[str, Any]:
        """
        Compute net directional conviction from all signals.
        
        Returns:
            {
                "net_conviction": float (-10 to +10, negative=short, positive=long),
                "bullish_evidence": float,
                "bearish_evidence": float,
                "confidence": float (0-1),
                "signal_agreement": float (0-1),
                "dominant_signals": list,
                "conflicting_signals": list,
                "regime_adjustment": float
            }
        """
        bullish_evidence = 0.0
        bearish_evidence = 0.0
        bullish_signals = []
        bearish_signals = []
        neutral_signals = []
        
        for signal in signals:
            effective_weight = self.weight_model.get_effective_weight(signal.component)
            weighted_value = abs(signal.raw_value) * effective_weight * signal.confidence
            
            if signal.polarity > 0:
                bullish_evidence += weighted_value
                bullish_signals.append((signal.component, weighted_value))
            elif signal.polarity < 0:
                bearish_evidence += weighted_value
                bearish_signals.append((signal.component, weighted_value))
            else:
                neutral_signals.append((signal.component, weighted_value))
        
        regime_mult = self.regime_dampeners.get(regime, 1.0)
        
        net_conviction = (bullish_evidence - bearish_evidence) * regime_mult
        
        total_evidence = bullish_evidence + bearish_evidence
        if total_evidence > 0:
            signal_agreement = abs(bullish_evidence - bearish_evidence) / total_evidence
        else:
            signal_agreement = 0.0
        
        if signal_agreement < self.toxicity_threshold:
            toxicity_penalty = (self.toxicity_threshold - signal_agreement) * 0.5
            net_conviction *= (1.0 - toxicity_penalty)
        
        confidence = min(1.0, signal_agreement * (1 + len(signals) / 20))
        
        bullish_signals.sort(key=lambda x: x[1], reverse=True)
        bearish_signals.sort(key=lambda x: x[1], reverse=True)
        
        dominant = bullish_signals[:3] if net_conviction > 0 else bearish_signals[:3]
        conflicting = bearish_signals[:2] if net_conviction > 0 else bullish_signals[:2]
        
        return {
            "net_conviction": round(net_conviction, 4),
            "bullish_evidence": round(bullish_evidence, 4),
            "bearish_evidence": round(bearish_evidence, 4),
            "confidence": round(confidence, 4),
            "signal_agreement": round(signal_agreement, 4),
            "dominant_signals": [s[0] for s in dominant],
            "conflicting_signals": [s[0] for s in conflicting],
            "regime_adjustment": regime_mult,
            "direction": "LONG" if net_conviction > 0 else ("SHORT" if net_conviction < 0 else "NEUTRAL"),
            "strength": abs(net_conviction)
        }
    
    def should_enter(self, conviction_result: Dict, threshold: float = 2.5) -> Tuple[bool, str]:
        """Determine if conviction is strong enough for entry"""
        net = conviction_result["net_conviction"]
        conf = conviction_result["confidence"]
        agreement = conviction_result["signal_agreement"]
        
        if abs(net) < threshold:
            return False, f"conviction_too_weak({abs(net):.2f}<{threshold})"
        
        if conf < 0.4:
            return False, f"confidence_too_low({conf:.2f})"
        
        if agreement < 0.3:
            return False, f"signals_conflicting({agreement:.2f})"
        
        direction = "LONG" if net > 0 else "SHORT"
        return True, f"entry_approved_{direction}(conv={net:.2f},conf={conf:.2f})"


class ExitSignalModel:
    """
    Separate adaptive weights for exit/sell decisions.
    Tracks different signals than entry model.
    """
    
    DEFAULT_EXIT_WEIGHTS = {
        "entry_decay": 1.0,
        "adverse_flow": 1.2,
        "drawdown_velocity": 1.5,
        "time_decay": 0.8,
        "momentum_reversal": 1.3,
        "volume_exhaustion": 0.9,
        "support_break": 1.4,
    }
    
    def __init__(self):
        self.base_weights = self.DEFAULT_EXIT_WEIGHTS.copy()
        self.weight_bands: Dict[str, WeightBand] = {}
        self._init_bands()
        
    def _init_bands(self):
        """Initialize weight bands for exit components"""
        for component in EXIT_COMPONENTS:
            self.weight_bands[component] = WeightBand(
                min_weight=0.25,
                max_weight=2.5,
                neutral=1.0,
                current=1.0
            )
    
    def compute_exit_urgency(self, 
                            position_data: Dict,
                            current_signals: Dict) -> Dict[str, Any]:
        """
        Compute exit urgency score based on position state and current signals.
        
        Args:
            position_data: {
                "entry_score": float,
                "current_pnl_pct": float,
                "age_hours": float,
                "high_water_pct": float,
                "entry_signals": dict
            }
            current_signals: Current market signals
            
        Returns:
            {
                "exit_urgency": float (0-10, higher = exit sooner),
                "primary_reason": str,
                "contributing_factors": list,
                "recommendation": "HOLD" | "REDUCE" | "EXIT"
            }
        """
        urgency = 0.0
        factors = []
        
        entry_score = position_data.get("entry_score", 3.0)
        current_pnl = position_data.get("current_pnl_pct", 0.0)
        age_hours = position_data.get("age_hours", 0.0)
        high_water = position_data.get("high_water_pct", current_pnl)
        
        if entry_score > 0:
            current_score = current_signals.get("composite_score", entry_score)
            decay_ratio = current_score / entry_score
            if decay_ratio < 0.7:
                decay_contrib = (1 - decay_ratio) * self._get_weight("entry_decay")
                urgency += decay_contrib
                factors.append(f"entry_decay({decay_ratio:.2f})")
        
        flow_reversal = current_signals.get("flow_reversal", False)
        if flow_reversal:
            adverse_contrib = 2.0 * self._get_weight("adverse_flow")
            urgency += adverse_contrib
            factors.append("adverse_flow_detected")
        
        drawdown = high_water - current_pnl
        if drawdown > 3.0:
            dd_velocity = drawdown / max(1, age_hours / 24)
            dd_contrib = min(3.0, dd_velocity * 0.5) * self._get_weight("drawdown_velocity")
            urgency += dd_contrib
            factors.append(f"drawdown({drawdown:.1f}%,vel={dd_velocity:.2f})")
        
        if age_hours > 72:
            time_contrib = min(2.0, (age_hours - 72) / 48) * self._get_weight("time_decay")
            urgency += time_contrib
            factors.append(f"time_decay({age_hours:.0f}h)")
        
        momentum = current_signals.get("momentum", 0)
        entry_direction = position_data.get("direction", "LONG")
        if (entry_direction == "LONG" and momentum < -0.5) or \
           (entry_direction == "SHORT" and momentum > 0.5):
            mom_contrib = abs(momentum) * self._get_weight("momentum_reversal")
            urgency += mom_contrib
            factors.append(f"momentum_reversal({momentum:.2f})")
        
        if current_pnl < -5.0:
            urgency += 2.0
            factors.append(f"loss_limit({current_pnl:.1f}%)")
        
        if urgency >= 6.0:
            recommendation = "EXIT"
        elif urgency >= 3.0:
            recommendation = "REDUCE"
        else:
            recommendation = "HOLD"
        
        primary = factors[0] if factors else "none"
        
        return {
            "exit_urgency": round(min(10.0, urgency), 2),
            "primary_reason": primary,
            "contributing_factors": factors,
            "recommendation": recommendation
        }
    
    def _get_weight(self, component: str) -> float:
        """Get effective weight for exit component"""
        base = self.base_weights.get(component, 1.0)
        band = self.weight_bands.get(component)
        if band:
            return band.get_effective_weight(base)
        return base
    
    def to_dict(self) -> Dict:
        return {
            "base_weights": self.base_weights,
            "weight_bands": {k: asdict(v) for k, v in self.weight_bands.items()}
        }
    
    def from_dict(self, data: Dict):
        if "base_weights" in data:
            self.base_weights.update(data["base_weights"])
        if "weight_bands" in data:
            for k, v in data["weight_bands"].items():
                if k in self.weight_bands:
                    for field_name, field_val in v.items():
                        if hasattr(self.weight_bands[k], field_name):
                            setattr(self.weight_bands[k], field_name, field_val)


class LearningOrchestrator:
    """
    Bayesian learning system for weight optimization.
    Updates weights based on trade outcomes with anti-overfitting guards.
    """
    
    EWMA_ALPHA = 0.15
    MIN_SAMPLES = 30  # Balanced: statistically sound but allows learning with less data (industry standard: 30-50 for early stage, 50-100 for mature)
    LOOKBACK_DAYS = 60  # Increased from 30 to 60 for more stable learning
    UPDATE_STEP = 0.05
    WILSON_Z = 1.96
    MIN_DAYS_BETWEEN_UPDATES = 1  # Allow daily updates for faster learning (will increase to 3 once system matures)
    
    def __init__(self, 
                 entry_model: SignalWeightModel,
                 exit_model: ExitSignalModel):
        self.entry_model = entry_model
        self.exit_model = exit_model
        self.learning_history: List[Dict] = []
        self.component_performance: Dict[str, Dict] = {}
        self.last_weight_update_ts: Optional[int] = None  # Track last update time
        self._init_performance_tracking()
        
    def _init_performance_tracking(self):
        """Initialize performance tracking for all components"""
        for component in SIGNAL_COMPONENTS:
            self.component_performance[component] = {
                "wins": 0,
                "losses": 0,
                "total_pnl": 0.0,
                "ewma_win_rate": 0.5,
                "ewma_pnl": 0.0,
                "contribution_when_win": [],
                "contribution_when_loss": [],
                "sector_performance": {},
                "regime_performance": {}
            }
        for component in EXIT_COMPONENTS:
            self.component_performance[f"exit_{component}"] = {
                "timely_exits": 0,
                "late_exits": 0,
                "false_alarms": 0,
                "ewma_timing": 0.5
            }
    
    def record_trade_outcome(self, 
                            trade_data: Dict,
                            feature_vector: Dict[str, float],
                            pnl: float,
                            regime: str = "neutral",
                            sector: str = "unknown"):
        """
        Record a completed trade for learning.
        
        Args:
            trade_data: Trade metadata (entry_ts, exit_ts, direction, etc.)
            feature_vector: Signal values at entry {component: value}
            pnl: Realized P&L percentage
            regime: Market regime at entry
            sector: Stock sector
        """
        win = pnl > 0
        
        # Track ALL components in feature_vector
        # For learning, we want to track components that were present in the trade
        # Even if value is 0, the component was evaluated and should be counted
        for component, value in feature_vector.items():
            if component not in self.component_performance:
                # Component not in tracking system - skip (shouldn't happen if normalized correctly)
                continue
            
            perf = self.component_performance[component]
            
            # Track component if it was present in the trade (even if value is 0)
            # This ensures we count samples for components that were evaluated
            # Only count as win/loss if value is non-zero (component actually contributed)
            if value != 0:
                # Component contributed - count as win/loss
                if win:
                    perf["wins"] += 1
                    perf["contribution_when_win"].append(value)
                else:
                    perf["losses"] += 1
                    perf["contribution_when_loss"].append(value)
            # If value is 0, component was present but didn't contribute
            # We still want to track that it was evaluated (for sample counting)
            # So we'll count it as a "neutral" sample (no win/loss, but counted)
            # This helps us know which components are being evaluated vs not present at all
            
            perf["total_pnl"] += pnl
            
            total = perf["wins"] + perf["losses"]
            if total > 0:
                new_wr = perf["wins"] / total
                perf["ewma_win_rate"] = self._ewma(perf["ewma_win_rate"], new_wr)
            perf["ewma_pnl"] = self._ewma(perf["ewma_pnl"], pnl)
            
            if sector not in perf["sector_performance"]:
                perf["sector_performance"][sector] = {"wins": 0, "losses": 0, "pnl": 0.0}
            sec_perf = perf["sector_performance"][sector]
            if win:
                sec_perf["wins"] += 1
            else:
                sec_perf["losses"] += 1
            sec_perf["pnl"] += pnl
            
            if regime not in perf["regime_performance"]:
                perf["regime_performance"][regime] = {"wins": 0, "losses": 0, "pnl": 0.0}
            reg_perf = perf["regime_performance"][regime]
            if win:
                reg_perf["wins"] += 1
            else:
                reg_perf["losses"] += 1
            reg_perf["pnl"] += pnl
        
        self.learning_history.append({
            "ts": int(time.time()),
            "pnl": pnl,
            "win": win,
            "regime": regime,
            "sector": sector,
            "features": feature_vector
        })
        
        if len(self.learning_history) > 1000:
            self.learning_history = self.learning_history[-1000:]
    
    def _ewma(self, prev: float, new: float) -> float:
        """Exponentially weighted moving average"""
        return self.EWMA_ALPHA * new + (1 - self.EWMA_ALPHA) * prev
    
    def _wilson_interval(self, wins: int, total: int) -> Tuple[float, float]:
        """Calculate Wilson confidence interval"""
        if total == 0:
            return 0.0, 1.0
        
        z = self.WILSON_Z
        p = wins / total
        
        denom = 1 + (z**2 / total)
        center = p + (z**2 / (2 * total))
        spread = z * math.sqrt((p * (1-p) + (z**2 / (4*total))) / total)
        
        lower = (center - spread) / denom
        upper = (center + spread) / denom
        
        return max(0.0, lower), min(1.0, upper)
    
    def update_weights(self) -> Dict[str, Any]:
        """
        Perform Bayesian weight update based on accumulated performance.
        
        Industry best practice: Batch updates with minimum samples and time between updates.
        
        Returns summary of adjustments made.
        """
        # Check minimum days between updates (prevents overfitting)
        now_ts = int(time.time())
        if self.last_weight_update_ts:
            days_since_update = (now_ts - self.last_weight_update_ts) / 86400
            if days_since_update < self.MIN_DAYS_BETWEEN_UPDATES:
                return {
                    "ts": now_ts,
                    "adjustments": [],
                    "total_adjusted": 0,
                    "skipped": True,
                    "reason": f"too_soon({days_since_update:.1f}d < {self.MIN_DAYS_BETWEEN_UPDATES}d)"
                }
        
        adjustments = []
        
        for component in SIGNAL_COMPONENTS:
            perf = self.component_performance.get(component, {})
            wins = perf.get("wins", 0)
            losses = perf.get("losses", 0)
            total = wins + losses
            
            if total < self.MIN_SAMPLES:
                continue
            
            wilson_low, wilson_high = self._wilson_interval(wins, total)
            ewma_wr = perf.get("ewma_win_rate", 0.5)
            ewma_pnl = perf.get("ewma_pnl", 0.0)
            
            current_mult = self.entry_model.weight_bands[component].current
            new_mult = current_mult
            reason = None
            
            # ADJUST TOWARDS PROFITABILITY: Increase weights for strong performers
            # Both win rate AND P&L must be positive
            if wilson_low > 0.55 and ewma_wr > 0.55 and ewma_pnl > 0:
                new_mult = min(2.5, current_mult + self.UPDATE_STEP)
                reason = f"strong_performer(wilson_low={wilson_low:.3f},ewma={ewma_wr:.3f},pnl={ewma_pnl:.3f})"
            
            # ADJUST AWAY FROM LOSING: Decrease weights for weak performers
            # Low win rate OR negative P&L triggers reduction
            elif wilson_high < 0.45 and ewma_wr < 0.45:
                new_mult = max(0.25, current_mult - self.UPDATE_STEP)
                reason = f"weak_performer(wilson_high={wilson_high:.3f},ewma={ewma_wr:.3f})"
            
            # Also decrease if P&L is negative (even if win rate is borderline)
            # This ensures we move AWAY from losing patterns
            elif ewma_pnl < -0.01 and ewma_wr < 0.50:
                new_mult = max(0.25, current_mult - self.UPDATE_STEP)
                reason = f"negative_pnl(ewma_pnl={ewma_pnl:.3f},ewma_wr={ewma_wr:.3f})"
            
            # Also decrease if win rate is very low (strong signal to reduce)
            elif ewma_wr < 0.40:
                new_mult = max(0.25, current_mult - self.UPDATE_STEP)
                reason = f"very_low_win_rate(ewma={ewma_wr:.3f})"
            
            # Mean reversion for neutral performers
            elif 0.48 <= ewma_wr <= 0.52 and total > self.MIN_SAMPLES * 2:
                decay = (current_mult - 1.0) * 0.1
                new_mult = current_mult - decay
                reason = f"mean_revert(ewma={ewma_wr:.3f})"
            
            if new_mult != current_mult:
                self.entry_model.update_multiplier(component, new_mult)
                band = self.entry_model.weight_bands[component]
                band.sample_count = total
                band.wins = wins
                band.losses = losses
                band.ewma_performance = ewma_wr
                
                adjustments.append({
                    "component": component,
                    "old_mult": round(current_mult, 3),
                    "new_mult": round(new_mult, 3),
                    "reason": reason,
                    "samples": total,
                    "win_rate": round(wins/total, 3) if total > 0 else 0
                })
        
        # Update last update timestamp if we made adjustments
        if adjustments:
            self.last_weight_update_ts = int(time.time())
        
        result = {
            "ts": int(time.time()),
            "adjustments": adjustments,
            "total_adjusted": len(adjustments),
            "current_multipliers": self.entry_model.get_multipliers(),
            "last_update_ts": self.last_weight_update_ts
        }
        
        self._log_learning(result)
        
        return result
    
    def _log_learning(self, result: Dict):
        """Log learning updates to JSONL"""
        try:
            LEARNING_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with LEARNING_LOG_FILE.open("a") as f:
                f.write(json.dumps(result) + "\n")
        except Exception:
            pass
    
    def get_component_report(self) -> Dict[str, Any]:
        """Generate performance report for all components"""
        report = {}
        for component in SIGNAL_COMPONENTS:
            perf = self.component_performance.get(component, {})
            wins = perf.get("wins", 0)
            losses = perf.get("losses", 0)
            total = wins + losses
            
            wilson_low, wilson_high = self._wilson_interval(wins, total)
            
            band = self.entry_model.weight_bands.get(component)
            
            report[component] = {
                "multiplier": band.current if band else 1.0,
                "effective_weight": self.entry_model.get_effective_weight(component),
                "samples": total,
                "win_rate": round(wins/total, 3) if total > 0 else 0,
                "wilson_interval": [round(wilson_low, 3), round(wilson_high, 3)],
                "ewma_win_rate": round(perf.get("ewma_win_rate", 0.5), 3),
                "ewma_pnl": round(perf.get("ewma_pnl", 0.0), 2),
                "status": self._component_status(wilson_low, wilson_high, perf.get("ewma_win_rate", 0.5))
            }
        
        return report
    
    def _component_status(self, wilson_low: float, wilson_high: float, ewma: float) -> str:
        """Determine component health status"""
        if wilson_low > 0.55 and ewma > 0.55:
            return "STRONG"
        elif wilson_high < 0.45 and ewma < 0.45:
            return "WEAK"
        elif wilson_low < 0.4:
            return "UNCERTAIN"
        else:
            return "NEUTRAL"
    
    def to_dict(self) -> Dict:
        return {
            "component_performance": self.component_performance,
            "learning_history_count": len(self.learning_history),
            "last_history_sample": self.learning_history[-1] if self.learning_history else None
        }
    
    def from_dict(self, data: Dict):
        if "component_performance" in data:
            self.component_performance.update(data["component_performance"])


class AdaptiveSignalOptimizer:
    """
    Main facade combining all optimization components.
    Single entry point for the trading bot.
    """
    
    def __init__(self):
        self.entry_weights = SignalWeightModel()
        self.conviction_engine = DirectionalConvictionEngine(self.entry_weights)
        self.exit_model = ExitSignalModel()
        self.learner = LearningOrchestrator(self.entry_weights, self.exit_model)
        self._load_state()
    
    def _load_state(self):
        """Load persisted state"""
        try:
            if WEIGHTS_STATE_FILE.exists():
                data = json.loads(WEIGHTS_STATE_FILE.read_text())
                if "entry_weights" in data:
                    self.entry_weights.from_dict(data["entry_weights"])
                if "exit_model" in data:
                    self.exit_model.from_dict(data["exit_model"])
                if "learner" in data:
                    self.learner.from_dict(data["learner"])
                self._state_loaded = True
                self._state_load_ts = int(time.time())
            else:
                self._state_loaded = False
                self._state_load_ts = 0
        except Exception as e:
            self._state_loaded = False
            self._state_load_ts = 0
            self._log_error("load_state", str(e))
    
    def save_state(self):
        """Persist current state"""
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                "entry_weights": self.entry_weights.to_dict(),
                "exit_model": self.exit_model.to_dict(),
                "learner": self.learner.to_dict(),
                "saved_at": int(time.time()),
                "saved_dt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            }
            WEIGHTS_STATE_FILE.write_text(json.dumps(data, indent=2))
            return True
        except Exception as e:
            self._log_error("save_state", str(e))
            return False
    
    def _log_error(self, operation: str, error: str):
        """Log errors for debugging"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            log_file = DATA_DIR / "optimizer_errors.jsonl"
            with open(log_file, "a") as f:
                f.write(json.dumps({
                    "ts": int(time.time()),
                    "operation": operation,
                    "error": error
                }) + "\n")
        except Exception:
            pass
    
    def is_state_loaded(self) -> bool:
        """Check if state was successfully loaded"""
        return getattr(self, "_state_loaded", False)
    
    def has_learned_weights(self) -> bool:
        """Check if any weights have been adjusted from defaults"""
        for component in SIGNAL_COMPONENTS:
            if component in self.entry_weights.weight_bands:
                band = self.entry_weights.weight_bands[component]
                if band.current != 1.0 or band.sample_count > 0:
                    return True
        return False
    
    def compute_entry_conviction(self, 
                                 signal_readings: Dict[str, Tuple[float, int]],
                                 regime: str = "neutral") -> Dict[str, Any]:
        """
        Compute entry conviction from raw signal readings.
        
        Args:
            signal_readings: {component: (value, polarity)} where polarity is -1/0/+1
            regime: Current market regime
            
        Returns:
            Conviction result with recommendation
        """
        readings = []
        for component, (value, polarity) in signal_readings.items():
            readings.append(SignalReading(
                component=component,
                raw_value=value,
                polarity=polarity
            ))
        
        conviction = self.conviction_engine.compute_conviction(readings, regime)
        should_enter, reason = self.conviction_engine.should_enter(conviction)
        
        conviction["should_enter"] = should_enter
        conviction["entry_reason"] = reason
        conviction["effective_weights"] = self.entry_weights.get_all_effective_weights()
        
        return conviction
    
    def compute_exit_urgency(self, 
                            position_data: Dict,
                            current_signals: Dict) -> Dict[str, Any]:
        """
        Compute exit urgency for a position.
        
        Returns exit recommendation with urgency score.
        """
        return self.exit_model.compute_exit_urgency(position_data, current_signals)
    
    def record_trade(self,
                    feature_vector: Dict[str, float],
                    pnl: float,
                    regime: str = "neutral",
                    sector: str = "unknown",
                    trade_data: Optional[Dict] = None):
        """Record a completed trade for learning"""
        self.learner.record_trade_outcome(
            trade_data or {},
            feature_vector,
            pnl,
            regime,
            sector
        )
    
    def update_weights(self) -> Dict[str, Any]:
        """Trigger weight update from learning"""
        result = self.learner.update_weights()
        self.save_state()
        return result
    
    def get_report(self) -> Dict[str, Any]:
        """Get comprehensive optimization report"""
        return {
            "entry_multipliers": self.entry_weights.get_multipliers(),
            "effective_weights": self.entry_weights.get_all_effective_weights(),
            "component_performance": self.learner.get_component_report(),
            "learning_samples": len(self.learner.learning_history)
        }
    
    def get_weights_for_composite(self) -> Dict[str, float]:
        """
        Export weights in format compatible with uw_composite_v2.py
        This is the bridge between the optimizer and existing scoring.
        """
        return self.entry_weights.get_all_effective_weights()
    
    def get_multipliers_only(self) -> Dict[str, float]:
        """
        Export ONLY the adaptive multipliers (0.25x-2.5x) without base weights.
        Use this for downstream modules (sizing, gating) that need to scale
        their own calculations without double-counting base weights.
        """
        return self.entry_weights.get_multipliers()


_optimizer_instance: Optional[AdaptiveSignalOptimizer] = None

def get_optimizer() -> AdaptiveSignalOptimizer:
    """Get singleton optimizer instance"""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = AdaptiveSignalOptimizer()
    return _optimizer_instance


if __name__ == "__main__":
    optimizer = get_optimizer()
    
    test_signals = {
        "options_flow": (0.8, 1),
        "dark_pool": (0.5, 1),
        "congress": (0.3, 1),
        "shorts_squeeze": (0.6, 1),
        "institutional": (0.2, -1),
        "market_tide": (0.4, 1),
    }
    
    conviction = optimizer.compute_entry_conviction(test_signals, regime="neutral")
    print("=== Entry Conviction Test ===")
    print(json.dumps(conviction, indent=2))
    
    position = {
        "entry_score": 4.0,
        "current_pnl_pct": -2.5,
        "age_hours": 96,
        "high_water_pct": 3.0,
        "direction": "LONG"
    }
    current = {
        "composite_score": 2.5,
        "flow_reversal": False,
        "momentum": -0.3
    }
    
    exit_result = optimizer.compute_exit_urgency(position, current)
    print("\n=== Exit Urgency Test ===")
    print(json.dumps(exit_result, indent=2))
    
    print("\n=== Component Report ===")
    report = optimizer.get_report()
    print(f"Learning samples: {report['learning_samples']}")
    print(f"Entry multipliers: {report['entry_multipliers']}")
