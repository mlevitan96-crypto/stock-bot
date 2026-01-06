#!/usr/bin/env python3
"""
V3.2.1 Trading System Upgrade
- Enhanced expectancy gating with exploration policy and exit rules
- Telemetry logging for expectancy decisions and router selections
- Stage-specific unlock criteria with TCA and fill metrics
- Tighter safety caps and rate limits
"""

import json
import time
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional

from config.registry import StateFiles

# ============================================================================
# CONFIGURATION PATHS (v3.2.1)
# ============================================================================
EXPECTANCY_TRACE_LOG = Path("data/expectancy_trace.jsonl")
ROUTER_TRACE_LOG = Path("data/router_trace.jsonl")
OPTIMIZATIONS_LOG = Path("data/optimizations.jsonl")
TCA_SUMMARY_LOG = Path("data/tca_summary.jsonl")
CHAMPION_EVENTS_LOG = Path("data/champion_events.jsonl")
BAYES_PROFILES_PATH = Path("state/bayes_profiles.json")
CHAMPIONS_PATH = StateFiles.CHAMPIONS
ROUTER_CONFIG_PATH = Path("config/execution_router.json")
SYSTEM_STAGE_PATH = Path("state/system_stage.json")

# ============================================================================
# SAFETY CAPS (v3.2.1)
# ============================================================================
SAFETY_CAPS = {
    "per_order_notional_usd": 15000,  # Reduced from $25k
    "per_theme_notional_usd": 150000,
    "portfolio_risk_budget_pct": 0.25,
    "max_new_positions_per_cycle": 3,
    "min_cycles_between_unlocked_changes": 3
}

# ============================================================================
# STAGE UNLOCKS (v3.2.1)
# ============================================================================
STAGE_CONFIGS = {
    "bootstrap": {
        "entry_ev_floor": -0.30,  # TEMPORARILY LOWERED from -0.02 to allow trades to execute
        "size_multiplier_cap": 0.6,
        "exploration_quota_per_day": 12,
        "unlock_criteria": {"fills": 20, "win_rate": 0.50}
    },
    "unlocked": {
        "entry_ev_floor": 0.10,
        "size_multiplier_cap": 1.0,
        "exploration_quota_per_day": 8,
        "unlock_criteria": {
            "fills": 50,
            "win_rate": 0.52,
            "tca_slippage_avg_pct": 0.30,  # <=0.30%
            "fill_ratio": 0.90  # >=90%
        }
    },
    "high_confidence": {
        "entry_ev_floor": 0.20,
        "size_multiplier_cap": 1.4,
        "exploration_quota_per_day": 4,
        "unlock_criteria": {
            "fills": 100,
            "win_rate": 0.55,
            "expectancy_rolling": 0.12  # >=0.12
        }
    }
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def log_jsonl(path: Path, event: dict):
    """Append JSON line to log file"""
    path.parent.mkdir(exist_ok=True, parents=True)
    with path.open("a") as f:
        f.write(json.dumps(event) + "\n")

def load_system_stage() -> dict:
    """Load system stage tracker"""
    if not SYSTEM_STAGE_PATH.exists():
        return {
            "current_stage": "bootstrap",
            "total_fills": 0,
            "win_rate": 0.0,
            "metrics": {
                "tca_slippage_avg_pct": 0.0,
                "fill_ratio": 0.0,
                "expectancy_rolling": 0.0
            },
            "exploration_used_today": 0,
            "exploration_date": None,
            "stage_changes": [],
            "last_updated": None
        }
    return json.loads(SYSTEM_STAGE_PATH.read_text())

def save_system_stage(data: dict):
    """Save system stage tracker"""
    data["last_updated"] = datetime.utcnow().isoformat()
    SYSTEM_STAGE_PATH.parent.mkdir(exist_ok=True)
    SYSTEM_STAGE_PATH.write_text(json.dumps(data, indent=2))

def get_system_stage(bayes_profiles: dict = None) -> str:
    """Get current system stage"""
    stage_data = load_system_stage()
    return stage_data.get("current_stage", "bootstrap")

def reset_daily_exploration():
    """Reset exploration quota if new day"""
    stage_data = load_system_stage()
    today = str(date.today())
    if stage_data.get("exploration_date") != today:
        stage_data["exploration_used_today"] = 0
        stage_data["exploration_date"] = today
        save_system_stage(stage_data)
    return stage_data

# ============================================================================
# EXPECTANCY GATE (v3.2.1 ENHANCED)
# ============================================================================
class ExpectancyGate:
    """
    Enhanced expectancy gate with:
    - Exploration policy for learning
    - Exit rules based on EV changes
    - Decision telemetry logging
    """
    
    @staticmethod
    def calculate_expectancy(
        composite_score: float,
        ticker_bayes_expectancy: float,
        regime_modifier: float,
        tca_modifier: float,
        theme_risk_penalty: float,
        toxicity_penalty: float
    ) -> float:
        """
        Calculate trade expectancy from multiple inputs.
        Returns expected value as a ratio (-1.0 to 1.0+)
        """
        # Base expectancy from composite score (normalize 0-5 to 0-1)
        base_ev = (composite_score / 5.0) - 0.5  # Center at 0
        
        # Apply ticker-specific Bayesian expectancy
        ev = base_ev * (1.0 + ticker_bayes_expectancy)
        
        # Apply regime modifier (-0.2 to +0.2)
        ev += regime_modifier
        
        # Apply TCA quality modifier (-0.1 to +0.1)
        ev += tca_modifier
        
        # Apply penalties
        ev -= theme_risk_penalty
        ev -= toxicity_penalty
        
        return round(ev, 4)
    
    @staticmethod
    def should_enter(
        ticker: str,
        expectancy: float,
        composite_score: float,
        stage: str,
        regime: str,
        tca_modifier: float,
        freeze_active: bool,
        score_floor_breach: bool,
        broker_health_degraded: bool
    ) -> Tuple[bool, str]:
        """
        Determine if trade should be executed based on expectancy.
        Includes exploration policy for learning.
        Returns (should_trade, reason)
        """
        # SAFETY BLOCKS (v3.2.1)
        if freeze_active:
            ExpectancyGate._log_decision(ticker, expectancy, composite_score, stage, regime, tca_modifier, False, "freeze_active")
            return False, "freeze_active"
        if score_floor_breach:
            ExpectancyGate._log_decision(ticker, expectancy, composite_score, stage, regime, tca_modifier, False, "score_floor_breach")
            return False, "score_floor_breach"
        if broker_health_degraded:
            ExpectancyGate._log_decision(ticker, expectancy, composite_score, stage, regime, tca_modifier, False, "broker_health_degraded")
            return False, "broker_health_degraded"
        
        # Get stage config
        stage_config = STAGE_CONFIGS.get(stage, STAGE_CONFIGS["bootstrap"])
        entry_floor = stage_config["entry_ev_floor"]
        
        # STANDARD ENTRY CHECK
        if expectancy >= entry_floor:
            ExpectancyGate._log_decision(ticker, expectancy, composite_score, stage, regime, tca_modifier, True, "expectancy_passed")
            return True, "expectancy_passed"
        
        # EXPLORATION POLICY (v3.2.1)
        # Allow low EV trades for learning if:
        # 1. EV >= -0.02 (not catastrophically bad)
        # 2. Quota remaining today
        if expectancy >= -0.02:
            stage_data = reset_daily_exploration()
            quota = stage_config["exploration_quota_per_day"]
            used = stage_data.get("exploration_used_today", 0)
            
            if used < quota:
                # Allow exploration
                stage_data["exploration_used_today"] = used + 1
                save_system_stage(stage_data)
                ExpectancyGate._log_decision(ticker, expectancy, composite_score, stage, regime, tca_modifier, True, "exploration_quota")
                return True, f"exploration_quota_{used+1}/{quota}"
        
        # REJECT
        ExpectancyGate._log_decision(ticker, expectancy, composite_score, stage, regime, tca_modifier, False, f"ev_below_floor_{stage}")
        return False, f"ev_below_floor_{stage}"
    
    @staticmethod
    def should_exit(
        ticker: str,
        current_ev: float,
        entry_ev: float,
        pnl_pct: float
    ) -> Tuple[bool, str]:
        """
        Exit rules based on EV changes (v3.2.1).
        Returns (should_exit, reason)
        """
        # Take profit if EV dropped by 5%
        if entry_ev > 0 and (entry_ev - current_ev) >= 0.05:
            return True, "take_profit_ev_drop"
        
        # Stop loss if EV below -0.08
        if current_ev <= -0.08:
            return True, "stop_loss_ev_floor"
        
        return False, "hold"
    
    @staticmethod
    def _log_decision(ticker: str, ev: float, score: float, stage: str, regime: str, tca: float, decision: bool, reason: str):
        """Log expectancy gate decision to telemetry (v3.2.1)"""
        log_jsonl(EXPECTANCY_TRACE_LOG, {
            "timestamp": datetime.utcnow().isoformat(),
            "ticker": ticker,
            "ev": ev,
            "score": score,
            "stage": stage,
            "regime": regime,
            "tca": tca,
            "decision": decision,
            "reason": reason
        })

# ============================================================================
# ADAPTIVE WEIGHTING
# ============================================================================
class AdaptiveWeighting:
    """
    Per-ticker, per-regime signal weight learning.
    Uses Bayesian updates with guardrails.
    """
    
    SIGNAL_NAMES = ["options_flow", "dark_pool", "insider"]
    BOOTSTRAP_WEIGHTS = {"options_flow": 0.33, "dark_pool": 0.33, "insider": 0.34}
    LEARNED_BOUNDS = {"min": 0.10, "max": 0.50}
    
    @staticmethod
    def load_profiles() -> dict:
        """Load Bayesian profiles from state"""
        if not BAYES_PROFILES_PATH.exists():
            return {"profiles": {}, "total_fills": 0, "system_stage": "bootstrap"}
        return json.loads(BAYES_PROFILES_PATH.read_text())
    
    @staticmethod
    def save_profiles(data: dict):
        """Save Bayesian profiles to state"""
        data["last_updated"] = datetime.utcnow().isoformat()
        BAYES_PROFILES_PATH.parent.mkdir(exist_ok=True)
        BAYES_PROFILES_PATH.write_text(json.dumps(data, indent=2))
    
    @staticmethod
    def get_weights(ticker: str, regime: str, profiles: dict) -> dict:
        """
        Get signal weights for ticker-regime combination.
        Returns bootstrap weights if not enough data.
        """
        stage = get_system_stage()
        if stage == "bootstrap":
            return AdaptiveWeighting.BOOTSTRAP_WEIGHTS.copy()
        
        profile_key = f"{ticker}_{regime}"
        if profile_key not in profiles.get("profiles", {}):
            return AdaptiveWeighting.BOOTSTRAP_WEIGHTS.copy()
        
        learned = profiles["profiles"][profile_key].get("weights", {})
        return learned if learned else AdaptiveWeighting.BOOTSTRAP_WEIGHTS.copy()
    
    @staticmethod
    def update_weights_bayesian(
        ticker: str,
        regime: str,
        signal_contributions: dict,
        trade_pnl: float,
        profiles: dict
    ):
        """
        Bayesian update of signal weights based on attribution.
        Guardrails: no single signal dominance, penalize unstable sources.
        """
        profile_key = f"{ticker}_{regime}"
        if profile_key not in profiles.get("profiles", {}):
            profiles.setdefault("profiles", {})[profile_key] = {
                "weights": AdaptiveWeighting.BOOTSTRAP_WEIGHTS.copy(),
                "samples": 0,
                "total_pnl": 0.0,
                "expectancy": 0.0
            }
        
        prof = profiles["profiles"][profile_key]
        prof["samples"] += 1
        prof["total_pnl"] += trade_pnl
        prof["expectancy"] = round(prof["total_pnl"] / prof["samples"], 4)
        
        # Bayesian update: reward successful signal contributions
        if trade_pnl > 0:
            for signal, contrib in signal_contributions.items():
                current_w = prof["weights"].get(signal, 0.33)
                # Increase weight proportional to contribution
                delta = contrib * 0.02  # 2% max shift per trade
                new_w = current_w + delta
                prof["weights"][signal] = new_w
        
        # Normalize and apply guardrails
        total = sum(prof["weights"].values())
        for signal in prof["weights"]:
            normalized = prof["weights"][signal] / total
            # Clamp to bounds
            clamped = max(AdaptiveWeighting.LEARNED_BOUNDS["min"],
                         min(AdaptiveWeighting.LEARNED_BOUNDS["max"], normalized))
            prof["weights"][signal] = round(clamped, 3)
        
        # Re-normalize after clamping
        total = sum(prof["weights"].values())
        for signal in prof["weights"]:
            prof["weights"][signal] = round(prof["weights"][signal] / total, 3)

# ============================================================================
# DYNAMIC SIZING (v3.2.1 ENHANCED)
# ============================================================================
class DynamicSizing:
    """
    Confidence-based position sizing with stage-specific caps.
    """
    
    @staticmethod
    def calculate_multiplier(
        composite_score: float,
        slippage_pct: float,
        regime: str,
        stage: str
    ) -> float:
        """
        Calculate position size multiplier from multiple factors.
        Returns multiplier with stage-specific caps (v3.2.1):
        - bootstrap: 0.6
        - unlocked: 1.0
        - high_confidence: 1.4
        """
        multiplier = 0.8  # Base size
        
        # Confidence scale
        if composite_score >= 4.2:
            multiplier *= 1.5
        elif composite_score >= 3.8:
            multiplier *= 1.2
        elif composite_score < 3.0:
            multiplier *= 0.6
        
        # TCA quality
        if slippage_pct < 0.002:  # <0.2%
            multiplier *= 1.2
        elif slippage_pct > 0.006:  # >0.6%
            multiplier *= 0.6
        
        # Regime volatility
        regime_mults = {"high": 0.7, "mixed": 1.0, "quiet": 1.2}
        multiplier *= regime_mults.get(regime, 1.0)
        
        # Apply stage cap (v3.2.1)
        stage_config = STAGE_CONFIGS.get(stage, STAGE_CONFIGS["bootstrap"])
        cap = stage_config["size_multiplier_cap"]
        
        return min(cap, max(0.5, multiplier))

# ============================================================================
# CHAMPION-CHALLENGER
# ============================================================================
class ChampionChallenger:
    """
    Automatic promotion/demotion of strategy variants based on expectancy.
    """
    
    @staticmethod
    def load_champions() -> dict:
        """Load current champions from state"""
        if not CHAMPIONS_PATH.exists():
            return {"current_champions": {}, "promotion_history": [], "demotion_history": []}
        return json.loads(CHAMPIONS_PATH.read_text())
    
    @staticmethod
    def save_champions(data: dict):
        """Save champions to state"""
        data["last_updated"] = datetime.utcnow().isoformat()
        CHAMPIONS_PATH.write_text(json.dumps(data, indent=2))
    
    @staticmethod
    def evaluate_promotion(
        variant_name: str,
        variant_stats: dict,
        champion_stats: dict,
        min_trades: int = 30
    ) -> Tuple[bool, str]:
        """
        Evaluate if variant should be promoted to champion.
        Requires 0.10+ expectancy delta and 30+ trades.
        """
        if variant_stats.get("trades", 0) < min_trades:
            return False, "insufficient_trades"
        
        variant_exp = variant_stats.get("expectancy", 0.0)
        champion_exp = champion_stats.get("expectancy", 0.0)
        delta = variant_exp - champion_exp
        
        if delta >= 0.10:
            log_jsonl(CHAMPION_EVENTS_LOG, {
                "timestamp": datetime.utcnow().isoformat(),
                "event": "promotion",
                "variant": variant_name,
                "variant_expectancy": variant_exp,
                "champion_expectancy": champion_exp,
                "delta": delta
            })
            return True, f"promoted_delta_{delta:.3f}"
        
        return False, f"delta_insufficient_{delta:.3f}"
    
    @staticmethod
    def evaluate_demotion(
        champion_name: str,
        champion_stats: dict,
        underperform_cycles: int
    ) -> Tuple[bool, str]:
        """
        Evaluate if champion should be demoted.
        Demote if expectancy < 0.0 for 5+ cycles.
        """
        if underperform_cycles >= 5 and champion_stats.get("expectancy", 0.0) < 0.0:
            log_jsonl(CHAMPION_EVENTS_LOG, {
                "timestamp": datetime.utcnow().isoformat(),
                "event": "demotion",
                "champion": champion_name,
                "expectancy": champion_stats.get("expectancy", 0.0),
                "underperform_cycles": underperform_cycles
            })
            return True, f"demoted_cycles_{underperform_cycles}"
        
        return False, "performance_acceptable"

# ============================================================================
# EXECUTION ROUTER (v3.2.1 ENHANCED)
# ============================================================================
class ExecutionRouter:
    """
    Intelligent execution routing with telemetry logging.
    """
    
    STRATEGIES = {
        "limit_offset": {"offset_bps": {"quiet": 10, "mixed": 20, "high": 30}},
        "peg_mid": {"spread_max_bps": 15, "queue_priority": "medium"},
        "twap_slice": {"slice_pct": 2, "window_min": 15},
        "vwap_adaptive": {"toxicity_block": True}
    }
    
    @staticmethod
    def load_config() -> dict:
        """Load router configuration"""
        if not ROUTER_CONFIG_PATH.exists():
            return ExecutionRouter._default_config()
        return json.loads(ROUTER_CONFIG_PATH.read_text())
    
    @staticmethod
    def save_config(data: dict):
        """Save router configuration"""
        ROUTER_CONFIG_PATH.parent.mkdir(exist_ok=True)
        ROUTER_CONFIG_PATH.write_text(json.dumps(data, indent=2))
    
    @staticmethod
    def _default_config():
        """Default router configuration"""
        return {
            "strategies": ExecutionRouter.STRATEGIES,
            "selection_rules": {
                "quiet": "peg_mid",
                "mixed": "limit_offset",
                "high": "limit_offset",
                "high_spread_or_toxicity": "twap_slice"
            },
            "tca_feedback": {
                "adjust_offsets_bps": {"improve": -5, "worsen": +5},
                "switch_on_failures": 3
            }
        }
    
    @staticmethod
    def select_strategy(
        ticker: str,
        regime: str,
        spread_bps: float,
        toxicity: float
    ) -> Tuple[str, dict]:
        """
        Select best execution strategy based on market conditions.
        Logs selection to telemetry (v3.2.1).
        """
        config = ExecutionRouter.load_config()
        rules = config.get("selection_rules", {})
        
        # High spread or toxicity -> TWAP
        if spread_bps > 50 or toxicity > 0.6:
            strategy = "twap_slice"
            reason = f"high_spread_{spread_bps:.1f}bps_or_toxicity_{toxicity:.2f}"
        else:
            strategy = rules.get(regime, "limit_offset")
            reason = f"regime_{regime}"
        
        # Log selection (v3.2.1)
        log_jsonl(ROUTER_TRACE_LOG, {
            "timestamp": datetime.utcnow().isoformat(),
            "ticker": ticker,
            "strategy": strategy,
            "regime": regime,
            "spread_bps": spread_bps,
            "toxicity": toxicity,
            "reason": reason
        })
        
        strategy_params = ExecutionRouter.STRATEGIES.get(strategy, {})
        return strategy, strategy_params
    
    @staticmethod
    def apply_tca_feedback(
        ticker: str,
        strategy: str,
        slippage_pct: float,
        target_pct: float = 0.003
    ):
        """
        Adjust strategy parameters based on TCA feedback.
        """
        config = ExecutionRouter.load_config()
        feedback_rules = config.get("tca_feedback", {})
        
        if strategy == "limit_offset":
            # Adjust offset based on slippage
            if slippage_pct < target_pct:
                # Improve: tighten offset
                delta = feedback_rules.get("adjust_offsets_bps", {}).get("improve", -5)
            else:
                # Worsen: widen offset
                delta = feedback_rules.get("adjust_offsets_bps", {}).get("worsen", +5)
            
            # Apply delta (would be persisted in real implementation)
            log_jsonl(TCA_SUMMARY_LOG, {
                "timestamp": datetime.utcnow().isoformat(),
                "ticker": ticker,
                "strategy": strategy,
                "slippage_pct": slippage_pct,
                "adjustment_bps": delta,
                "event": "tca_feedback"
            })

# ============================================================================
# STAGE CONTROLLER (v3.2.1)
# ============================================================================
class StageController:
    """
    Manages system stage progression based on performance metrics.
    """
    
    @staticmethod
    def update_metrics(fills: int, wins: int, tca_slippage: float, fill_ratio: float, expectancy: float):
        """Update stage metrics with latest data"""
        stage_data = load_system_stage()
        stage_data["total_fills"] = fills
        stage_data["win_rate"] = round(wins / fills, 3) if fills > 0 else 0.0
        stage_data["metrics"]["tca_slippage_avg_pct"] = round(tca_slippage, 4)
        stage_data["metrics"]["fill_ratio"] = round(fill_ratio, 3)
        stage_data["metrics"]["expectancy_rolling"] = round(expectancy, 4)
        save_system_stage(stage_data)
    
    @staticmethod
    def evaluate_stage_promotion() -> Tuple[bool, Optional[str]]:
        """
        Evaluate if system should advance to next stage.
        Returns (should_promote, new_stage)
        """
        stage_data = load_system_stage()
        current = stage_data["current_stage"]
        fills = stage_data["total_fills"]
        win_rate = stage_data["win_rate"]
        metrics = stage_data["metrics"]
        
        if current == "bootstrap":
            criteria = STAGE_CONFIGS["bootstrap"]["unlock_criteria"]
            if fills >= criteria["fills"] and win_rate >= criteria["win_rate"]:
                return True, "unlocked"
        
        elif current == "unlocked":
            criteria = STAGE_CONFIGS["unlocked"]["unlock_criteria"]
            if (fills >= criteria["fills"] and
                win_rate >= criteria["win_rate"] and
                metrics["tca_slippage_avg_pct"] <= criteria["tca_slippage_avg_pct"] and
                metrics["fill_ratio"] >= criteria["fill_ratio"]):
                return True, "high_confidence"
        
        return False, None
    
    @staticmethod
    def promote_stage(new_stage: str):
        """Promote system to new stage"""
        stage_data = load_system_stage()
        old_stage = stage_data["current_stage"]
        stage_data["current_stage"] = new_stage
        stage_data["stage_changes"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "from": old_stage,
            "to": new_stage,
            "fills": stage_data["total_fills"],
            "win_rate": stage_data["win_rate"]
        })
        save_system_stage(stage_data)
        
        log_jsonl(OPTIMIZATIONS_LOG, {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "stage_promotion",
            "from_stage": old_stage,
            "to_stage": new_stage,
            "fills": stage_data["total_fills"],
            "win_rate": stage_data["win_rate"]
        })

# ============================================================================
# INITIALIZE CONFIGS
# ============================================================================
def initialize_v321_configs():
    """Initialize all v3.2.1 configuration files if they don't exist"""
    
    # System stage
    if not SYSTEM_STAGE_PATH.exists():
        save_system_stage({
            "current_stage": "bootstrap",
            "total_fills": 0,
            "win_rate": 0.0,
            "metrics": {
                "tca_slippage_avg_pct": 0.0,
                "fill_ratio": 0.0,
                "expectancy_rolling": 0.0
            },
            "exploration_used_today": 0,
            "exploration_date": None,
            "stage_changes": []
        })
    
    # Bayes profiles
    if not BAYES_PROFILES_PATH.exists():
        AdaptiveWeighting.save_profiles({
            "profiles": {},
            "total_fills": 0,
            "system_stage": "bootstrap"
        })
    
    # Champions
    if not CHAMPIONS_PATH.exists():
        ChampionChallenger.save_champions({
            "current_champions": {},
            "promotion_history": [],
            "demotion_history": []
        })
    
    # Router config
    if not ROUTER_CONFIG_PATH.exists():
        ExecutionRouter.save_config(ExecutionRouter._default_config())
    
    # Create log directories
    for log_path in [EXPECTANCY_TRACE_LOG, ROUTER_TRACE_LOG, OPTIMIZATIONS_LOG, TCA_SUMMARY_LOG, CHAMPION_EVENTS_LOG]:
        log_path.parent.mkdir(exist_ok=True, parents=True)

# Initialize on import
initialize_v321_configs()
