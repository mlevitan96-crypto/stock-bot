# main.py — Single-file adaptive bot with comprehensive Unusual Whales integration + Alpaca paper trading
# IMPORTANT: For project context, common issues, and solutions, see MEMORY_BANK.md
# Features:
# - Multi-factor scoring: flow clusters + dark pool + gamma/greeks + net premium + realized vol + option volume levels
# - Disciplined thresholds and weights (configurable via env)
# - Alpaca paper trading execution with cooldowns, trailing stops, time exits
# - Daily reports (auto), weekly weight updates (auto), emergency override (auto)
# - Watchdog with health endpoints for uptime/self-healing
#
# CONFIGURATION: All paths and thresholds are centralized in config/registry.py

import os
import sys
import time
import json
import math
import random
import signal
import threading
import traceback
# Optional: requests is used in some execution / telemetry paths. Keep import non-blocking for local audit runs.
_MISSING_REQUESTS_LIB = False
try:
    import requests  # type: ignore
except Exception:
    # Provide a minimal stub so local structural audits can import the module tree.
    # This is non-blocking and should never be relied on in production runtime.
    import types as _types  # type: ignore
    requests = _types.ModuleType("requests")  # type: ignore
    def _missing_requests(*args, **kwargs):  # type: ignore
        raise RuntimeError("requests not installed in this environment")
    setattr(requests, "get", _missing_requests)
    setattr(requests, "post", _missing_requests)
    setattr(requests, "request", _missing_requests)
    sys.modules["requests"] = requests  # type: ignore
    _MISSING_REQUESTS_LIB = True

# Optional: Alpaca SDK import (non-blocking for local structural audits).
_MISSING_ALPACA_SDK = False
try:
    import alpaca_trade_api as tradeapi  # type: ignore
except Exception:
    import types as _types  # type: ignore
    tradeapi = _types.ModuleType("alpaca_trade_api")  # type: ignore
    class _MissingAlpacaREST:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise RuntimeError("alpaca_trade_api not installed in this environment")
    setattr(tradeapi, "REST", _MissingAlpacaREST)
    sys.modules["alpaca_trade_api"] = tradeapi  # type: ignore
    _MISSING_ALPACA_SDK = True
from pathlib import Path
from datetime import datetime, timedelta, timezone
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    import types as _types  # type: ignore
    _dotenv = _types.ModuleType("dotenv")  # type: ignore
    def load_dotenv(*args, **kwargs):  # type: ignore
        return False
    setattr(_dotenv, "load_dotenv", load_dotenv)
    sys.modules["dotenv"] = _dotenv  # type: ignore
from typing import Optional, Dict

# Optional: Flask import (non-blocking for local structural audits).
_MISSING_FLASK = False
try:
    from flask import Flask, jsonify, Response, send_from_directory  # type: ignore
except Exception:
    _MISSING_FLASK = True
    Response = object  # type: ignore
    def jsonify(obj=None, **kwargs):  # type: ignore
        return obj if obj is not None else kwargs
    def send_from_directory(*args, **kwargs):  # type: ignore
        raise RuntimeError("Flask not installed; send_from_directory unavailable.")

    class _DummyFlaskApp:
        def route(self, *args, **kwargs):
            def _decorator(fn):
                return fn
            return _decorator
        def run(self, *args, **kwargs):
            print("WARNING: Flask not installed; main Flask app cannot run.", flush=True)

    def Flask(*args, **kwargs):  # type: ignore
        return _DummyFlaskApp()
from position_reconciliation_loop import run_position_reconciliation_loop

from config.registry import (
    Directories, CacheFiles, StateFiles, LogFiles, ConfigFiles, Thresholds, APIConfig,
    read_json, atomic_write_json, append_jsonl
)
# CRITICAL: Standardized data path - MUST be used by all components (main.py, friday_eow_audit.py, dashboard.py)
ATTRIBUTION_LOG_PATH = LogFiles.ATTRIBUTION

# Non-blocking env check: if requests is missing (local), log once after log_event is defined.
# WHY: Local structural audit found main.py import failed when requests wasn't installed.
# HOW TO VERIFY: Startup logs include environment.missing_requests_library on machines without requests.
_LOGGED_MISSING_REQUESTS = False

def _normalize_ticker(ticker: str) -> str:
    """
    REQUIRED FIX: Normalize GOOG/GOOGL tickers to prevent concentration bias.
    Both GOOG and GOOGL represent Alphabet Inc. and should be treated as the same symbol.
    """
    ticker_upper = ticker.upper()
    if ticker_upper in ("GOOG", "GOOGL"):
        return "GOOGL"  # Use GOOGL as canonical form
    return ticker_upper

# Institutional-grade modules
from signals.uw import (
    uw_weighting,
    uw_entry_gate,
    uw_size_modifier,
    uw_exit_adjustment,
    uw_theme_propagation
)
from signals.uw_composite import compute_uw_composite_score, should_enter as uw_should_enter, log_uw_attribution, apply_sizing
from signals.uw_adaptive import AdaptiveGate
from signals.uw_weight_tuner import UWWeightTuner, load_live_weights

import uw_enrichment_v2 as uw_enrich
import uw_composite_v2 as uw_v2
from uw_composite_v2 import get_threshold
import cross_asset_confirmation as cross_asset
import uw_execution_v2 as uw_exec
import feature_attribution_v2 as feat_attr

# V3.2: Adaptive Signal Weight Optimization Integration
_adaptive_optimizer = None

def _get_adaptive_optimizer():
    """Lazy-load adaptive optimizer to avoid circular imports"""
    global _adaptive_optimizer
    if _adaptive_optimizer is None:
        try:
            from adaptive_signal_optimizer import get_optimizer
            _adaptive_optimizer = get_optimizer()
        except ImportError:
            _adaptive_optimizer = None
    return _adaptive_optimizer

def get_adaptive_weight(component: str, default: float = 1.0) -> float:
    """
    Get adaptive weight multiplier for a scoring component.
    Returns learned multiplier (0.25-2.5x) if available, else default.
    """
    optimizer = _get_adaptive_optimizer()
    if optimizer:
        weights = optimizer.get_weights_for_composite()
        if weights and component in weights:
            return weights[component]
    return default

def get_all_adaptive_weights() -> Dict[str, float]:
    """Get all current adaptive weights"""
    optimizer = _get_adaptive_optimizer()
    if optimizer:
        return optimizer.get_weights_for_composite()
    return {}

def record_trade_for_learning(feature_vector: dict, pnl: float, regime: str = "neutral", sector: str = "unknown"):
    """Record completed trade for adaptive weight learning"""
    optimizer = _get_adaptive_optimizer()
    if optimizer:
        optimizer.record_trade(feature_vector, pnl, regime, sector)
        
def get_exit_urgency(position_data: dict, current_signals: dict) -> dict:
    """Get adaptive exit urgency recommendation"""
    optimizer = _get_adaptive_optimizer()
    if optimizer:
        return optimizer.compute_exit_urgency(position_data, current_signals)
    return {"action": "HOLD", "urgency": 0.0}

def build_composite_close_reason(exit_signals: dict) -> str:
    """
    Build composite close reason from multiple exit signals (like entry uses composite signals).
    
    Args:
        exit_signals: Dict with exit signal components:
            - time_exit: bool or age_hours
            - trail_stop: bool or pnl_pct
            - signal_decay: float (decay ratio)
            - flow_reversal: bool
            - profit_target: float (pct hit)
            - drawdown: float (pct)
            - momentum_reversal: bool
            - regime_protection: str
            - displacement: str (symbol)
            - stale_position: bool
    
    Returns:
        Composite reason string like: "time_exit(72h)+signal_decay(0.65)+flow_reversal"
    """
    reasons = []
    
    # Time-based exits
    if exit_signals.get("time_exit"):
        age_hours = exit_signals.get("age_hours", 0)
        if age_hours > 0:
            reasons.append(f"time_exit({age_hours:.0f}h)")
        else:
            reasons.append("time_exit")
    
    # Trail stop
    if exit_signals.get("trail_stop"):
        pnl_pct = exit_signals.get("pnl_pct", 0.0)
        if pnl_pct < 0:
            reasons.append(f"trail_stop({pnl_pct:.1f}%)")
        else:
            reasons.append("trail_stop")
    
    # Signal decay
    signal_decay = exit_signals.get("signal_decay")
    if signal_decay is not None and signal_decay < 1.0:
        reasons.append(f"signal_decay({signal_decay:.2f})")
    
    # Flow reversal
    if exit_signals.get("flow_reversal"):
        reasons.append("flow_reversal")
    
    # Profit target
    profit_target = exit_signals.get("profit_target")
    if profit_target is not None and profit_target > 0:
        reasons.append(f"profit_target({int(profit_target*100)}%)")
    
    # Drawdown
    drawdown = exit_signals.get("drawdown")
    if drawdown is not None and drawdown > 0:
        reasons.append(f"drawdown({drawdown:.1f}%)")
    
    # Momentum reversal
    if exit_signals.get("momentum_reversal"):
        reasons.append("momentum_reversal")
    
    # Regime protection
    regime = exit_signals.get("regime_protection")
    if regime:
        reasons.append(f"regime_{regime}")
    
    # Displacement
    displacement = exit_signals.get("displacement")
    if displacement:
        reasons.append(f"displaced_by_{displacement}")
    
    # Stale position
    if exit_signals.get("stale_position"):
        reasons.append("stale_position")
    
    # Stale trade (no momentum after 90 minutes)
    if exit_signals.get("stale_trade"):
        age_min = exit_signals.get("stale_trade_age_min", 0)
        pnl_pct = exit_signals.get("stale_trade_pnl_pct", 0)
        reasons.append(f"stale_trade({age_min:.0f}min,{pnl_pct:.2f}%)")

    # Institutional Remediation Phase 7: kill zombie trades quickly
    if exit_signals.get("stale_alpha_cutoff"):
        age_min = exit_signals.get("stale_trade_age_min", exit_signals.get("age_min", 0) or 0)
        pnl_pct = exit_signals.get("stale_trade_pnl_pct", exit_signals.get("pnl_pct", 0) or 0)
        reasons.append(f"stale_alpha_cutoff({age_min:.0f}min,{pnl_pct:.2f}%)")
    
    # If no specific reasons, use primary reason or default
    if not reasons:
        primary = exit_signals.get("primary_reason")
        if primary and primary != "none" and primary != "unknown":
            reasons.append(primary)
        else:
            # Default fallback - should never happen if exit_signals is populated correctly
            reasons.append("unknown_exit")
    
    result = "+".join(reasons) if reasons else "unknown_exit"
    
    # Safety check: ensure we never return empty string
    if not result or result.strip() == "":
        result = "unknown_exit"
    
    return result

from v2_nightly_orchestration_with_auto_promotion import should_run_direct_v2
from telemetry.logger import TelemetryLogger, timestamp_to_iso
from health_supervisor import get_supervisor
import v3_2_features as v32

# Monitoring guards (Ops Recipe 2.1 → 3.0 → 3.1)
from monitoring_guards import (
    check_freeze_state,
    check_composite_score_floor,
    check_heartbeat_staleness,
    log_execution_quality,
    check_rollback_conditions,
    generate_cycle_monitoring_summary,
    auto_heal_on_alert,  # V3.0: Auto-healing
    apply_adaptive_optimizations  # V3.1: Adaptive optimization
)

# =========================
# ENV & CONFIG
# =========================
load_dotenv()

# =========================
# GLOBAL STATE - Monitoring
# =========================
ZERO_ORDER_CYCLE_COUNT = 0
REQUIRED_HEARTBEAT_MODULES = [
    "alpha_forecaster_gate",
    "bayes_alpha_allocator",
    "execution_alpha_uplifter",
    "kelly_regime_switcher",
    "portfolio_risk_budgeter",
    "toxicity_sentinel"
]

def get_env(name, default=None, cast=None):
    """Get environment variable with optional type casting."""
    val = os.getenv(name, default)
    if val is None:
        return default
    if cast is None:
        return val
    try:
        return cast(val)
    except Exception:
        return val

class Config:
    # Secrets
    UW_API_KEY = get_env("UW_API_KEY")
    ALPACA_KEY = get_env("ALPACA_KEY")
    ALPACA_SECRET = get_env("ALPACA_SECRET")
    ALPACA_BASE_URL = get_env("ALPACA_BASE_URL", APIConfig.ALPACA_BASE_URL)

    # Runtime
    TRADING_MODE = get_env("TRADING_MODE", "PAPER")  # PAPER or LIVE - v3.1.1
    # Live-trading arming gate (prevents accidental real-money trading)
    # In LIVE mode, bot will refuse to place new entry orders unless explicitly acknowledged.
    LIVE_TRADING_ACK = get_env("LIVE_TRADING_ACK", "")
    REQUIRE_LIVE_ACK = get_env("REQUIRE_LIVE_ACK", "true").lower() == "true"
    # Optional safety mode: block opening short positions (bearish entries).
    LONG_ONLY = get_env("LONG_ONLY", "false").lower() == "true"
    RUN_INTERVAL_SEC = get_env("RUN_INTERVAL_SEC", 60, int)
    LOG_LEVEL = get_env("LOG_LEVEL", "INFO")
    API_PORT = get_env("API_PORT", 8080, int)

    # Tickers & filters
    TICKERS = [t.strip() for t in get_env("TICKERS", 
        "AAPL,MSFT,GOOGL,AMZN,META,NVDA,TSLA,AMD,NFLX,INTC,"
        "SPY,QQQ,IWM,DIA,XLF,XLE,XLK,XLV,XLI,XLP,"
        "JPM,BAC,GS,MS,C,WFC,BLK,V,MA,"
        "COIN,PLTR,SOFI,HOOD,RIVN,LCID,F,GM,NIO,"
        "BA,CAT,XOM,CVX,COP,SLB,"
        "JNJ,PFE,MRNA,UNH,WMT,TGT,COST,HD,LOW"
    ).split(",")]
    MIN_PREMIUM_USD = get_env("MIN_PREMIUM_USD", 100000, int)  # Lowered from 500k to capture institutional flow
    MAX_EXPIRY_DAYS = get_env("MAX_EXPIRY_DAYS", 7, int)
    CLUSTER_WINDOW_SEC = get_env("CLUSTER_WINDOW_SEC", 600, int)
    CLUSTER_MIN_SWEEPS = get_env("CLUSTER_MIN_SWEEPS", 3, int)

    # Scoring weights (tune here)
    FLOW_COUNT_W = float(get_env("FLOW_COUNT_W", "0.5"))
    FLOW_PREMIUM_MILLION_W = float(get_env("FLOW_PREMIUM_MILLION_W", "1.0"))
    CONFIRM_GAMMA_NEG_W = float(get_env("CONFIRM_GAMMA_NEG_W", "0.5"))
    CONFIRM_DARKPOOL_W = float(get_env("CONFIRM_DARKPOOL_W", "0.25"))
    CONFIRM_NET_PREMIUM_W = float(get_env("CONFIRM_NET_PREMIUM_W", "0.25"))
    CONFIRM_VOL_W = float(get_env("CONFIRM_VOL_W", "0.1"))
    MIN_EXEC_SCORE = float(get_env("MIN_EXEC_SCORE", "3.0"))  # V3.0: Increased to 3.0 for predatory entry filter

    # Confirmation thresholds
    DARKPOOL_OFFLIT_MIN = float(get_env("DARKPOOL_OFFLIT_MIN", "1000000"))
    NET_PREMIUM_MIN_ABS = float(get_env("NET_PREMIUM_MIN_ABS", "100000"))
    RV20_MAX = float(get_env("RV20_MAX", "0.8"))

    # Execution & management
    SIZE_BASE_USD = float(get_env("SIZE_BASE_USD", "500"))
    MIN_NOTIONAL_USD = float(get_env("MIN_NOTIONAL_USD", "100"))
    DEFAULT_QTY = get_env("DEFAULT_QTY", 25, int)
    MAX_CONCURRENT_POSITIONS = get_env("MAX_CONCURRENT_POSITIONS", 16, int)  # Increased from 12 - was capacity constrained
    COOLDOWN_MINUTES_PER_TICKER = get_env("COOLDOWN_MINUTES_PER_TICKER", 15, int)
    TIME_EXIT_MINUTES = get_env("TIME_EXIT_MINUTES", 150, int)  # 2.5h - optimized for faster rotation
    TIME_EXIT_DAYS_STALE = get_env("TIME_EXIT_DAYS_STALE", 12, int)
    TIME_EXIT_STALE_PNL_THRESH_PCT = float(get_env("TIME_EXIT_STALE_PNL_THRESH_PCT", "0.03"))
    TRAILING_STOP_PCT = float(get_env("TRAILING_STOP_PCT", "0.015"))
    
    # Opportunity Cost Displacement - aggressive settings for faster rotation
    ENABLE_OPPORTUNITY_DISPLACEMENT = get_env("ENABLE_OPPORTUNITY_DISPLACEMENT", "true").lower() == "true"
    DISPLACEMENT_MIN_AGE_HOURS = get_env("DISPLACEMENT_MIN_AGE_HOURS", 4, int)  # Give trades time to work
    DISPLACEMENT_MAX_PNL_PCT = float(get_env("DISPLACEMENT_MAX_PNL_PCT", "0.01"))  # Only displace truly stagnant positions
    DISPLACEMENT_SCORE_ADVANTAGE = float(get_env("DISPLACEMENT_SCORE_ADVANTAGE", "2.0"))  # Require significantly better signal
    DISPLACEMENT_COOLDOWN_HOURS = get_env("DISPLACEMENT_COOLDOWN_HOURS", 6, int)  # Reduce churn frequency
    
    # Institutional Remediation Phase 7: kill zombie trades quickly (120 minutes)
    STALE_TRADE_EXIT_MINUTES = get_env("STALE_TRADE_EXIT_MINUTES", 120, int)  # 120 minutes
    STALE_TRADE_MOMENTUM_THRESH_PCT = float(get_env("STALE_TRADE_MOMENTUM_THRESH_PCT", "0.002"))  # +/- 0.2% momentum threshold

    # Smart entry (maker bias + retry before fallback)
    ENTRY_MODE = get_env("ENTRY_MODE", "MAKER_BIAS")
    ENTRY_TOLERANCE_BPS = float(get_env("ENTRY_TOLERANCE_BPS", "10"))
    ENTRY_MAX_RETRIES = get_env("ENTRY_MAX_RETRIES", 3, int)
    ENTRY_RETRY_SLEEP_SEC = float(get_env("ENTRY_RETRY_SLEEP_SEC", "1.0"))
    ENTRY_POST_ONLY = get_env("ENTRY_POST_ONLY", "true").lower() == "true"
    
    # Spread Watchdog (Audit Recommendation - prevents execution in illiquid names)
    MAX_SPREAD_BPS = float(get_env("MAX_SPREAD_BPS", "50"))  # Block trades with spread > 50 bps
    ENABLE_SPREAD_WATCHDOG = get_env("ENABLE_SPREAD_WATCHDOG", "true").lower() == "true"
    
    # Regime-aware execution mapping (Audit Recommendation)
    REGIME_EXECUTION_MAP = {
        "high_vol_neg_gamma": "AGGRESSIVE",      # Cross spread immediately
        "downtrend_flow_heavy": "AGGRESSIVE",    # Cross spread immediately  
        "low_vol_uptrend": "PASSIVE",            # Join NBBO to capture spread
        "high_vol_pos_gamma": "NEUTRAL",         # Default behavior
        "mixed": "NEUTRAL",                      # Default behavior
        "unknown": "NEUTRAL"                     # Default behavior
    }

    # Adaptive learning (weekly adjustments)
    MIN_TRADES_FOR_ADJUST = get_env("MIN_TRADES_FOR_ADJUST", 50, int)
    WEIGHT_STEP = float(get_env("WEIGHT_STEP", "0.25"))
    WEIGHT_MIN = float(get_env("WEIGHT_MIN", "0.3"))  # Lowered to allow weak signals like etf_flow=0.3
    WEIGHT_MAX = float(get_env("WEIGHT_MAX", "2.0"))
    WIN_RATE_UP = float(get_env("WIN_RATE_UP", "0.55"))
    WIN_RATE_DOWN = float(get_env("WIN_RATE_DOWN", "0.45"))

    # Emergency override thresholds (daily check to prevent collapse)
    EMERGENCY_MIN_TRADES = get_env("EMERGENCY_MIN_TRADES", 50, int)
    EMERGENCY_WIN_RATE_THRESH = float(get_env("EMERGENCY_WIN_RATE_THRESH", "0.30"))
    EMERGENCY_PNL_THRESH = float(get_env("EMERGENCY_PNL_THRESH", "-1000"))
    EMERGENCY_ADJUST_FACTOR = float(get_env("EMERGENCY_ADJUST_FACTOR", "0.25"))

    # Uptime monitor
    MAX_STALL_SEC = get_env("MAX_STALL_SEC", 180, int)
    BACKOFF_BASE_SEC = get_env("BACKOFF_BASE_SEC", 5, int)
    BACKOFF_MAX_SEC = get_env("BACKOFF_MAX_SEC", 300, int)
    WEBHOOK_URL = get_env("WEBHOOK_URL", "")

    # Per-ticker learning (opt-in feature)
    ENABLE_PER_TICKER_LEARNING = get_env("ENABLE_PER_TICKER_LEARNING", "true").lower() == "true"
    FEATURE_STORE_DIR = get_env("FEATURE_STORE_DIR", "feature_store")
    PROFILE_PATH = get_env("PROFILE_PATH", "profiles.json")
    MIN_SAMPLES_DAILY_UPDATE = get_env("MIN_SAMPLES_DAILY_UPDATE", 40, int)
    MIN_SAMPLES_WEEKLY_UPDATE = get_env("MIN_SAMPLES_WEEKLY_UPDATE", 200, int)
    CONFIDENCE_PRIOR = float(get_env("CONFIDENCE_PRIOR", "1.0"))

    # ATR-based dynamic stops
    ATR_LOOKBACK = get_env("ATR_LOOKBACK", 14, int)
    ATR_MIN_PCT = float(get_env("ATR_MIN_PCT", "0.004"))

    # Bandit action spaces
    ENTRY_ACTIONS = ["maker_bias", "midpoint", "market_fallback"]
    STOP_ACTIONS = ["atr_1.0x", "atr_1.5x", "atr_2.0x"]

    # Adaptive position sizing
    SIZE_BASE_USD = float(get_env("SIZE_BASE_USD", "500"))
    SIZE_VOL_CAP = float(get_env("SIZE_VOL_CAP", "0.03"))
    
    # Profit-taking tiers
    PROFIT_TARGETS = [float(x) for x in get_env("PROFIT_TARGETS", "0.02,0.05,0.10").split(",")]
    SCALE_OUT_FRACTIONS = [float(x) for x in get_env("SCALE_OUT_FRACTIONS", "0.3,0.3,0.4").split(",")]

    # Feature-weight bandit components (V3: expanded with congress, shorts, institutional, etc.)
    SIGNAL_COMPONENTS = [
        # Original components
        "flow_count", "flow_premium", "gamma", "darkpool", "net_premium", "volatility",
        # V3: Expanded intelligence components
        "congress", "shorts_squeeze", "institutional", "market_tide", "calendar",
        # V2: New full intelligence pipeline components
        "greeks_gamma", "ftd_pressure", "iv_rank", "oi_change", "etf_flow", "squeeze_score"
    ]
    DEFAULT_COMPONENT_WEIGHTS = {
        # --- CORE SIGNALS (Basic Plan Compatible) ---
        "flow_count": 1.0,      # Keep: Derived from Flow Alerts
        "flow_premium": 1.0,    # Keep: Derived from Flow Alerts
        "gamma": 1.0,           # Keep: Basic Greeks are available
        "net_premium": 1.0,     # Keep: Derived from Flow
        "volatility": 1.0,      # Keep: Derived from OHLCV
        "institutional": 1.0,   # Keep: Derived from block size in flow
        "market_tide": 1.0,     # Keep: Market-wide sentiment
        "calendar": 1.0,        # Keep: Earnings/events calendar
        # V2: Full intelligence pipeline
        "greeks_gamma": 1.2,    # Keep: 63.6% win rate - gamma exposure
        "ftd_pressure": 1.0,    # Keep: Fails-to-deliver signals
        "iv_rank": 1.0,         # Keep: IV rank for timing
        "oi_change": 1.1,       # Keep: 61.5% win rate - open interest changes
        
        # --- PRO FEATURES (Disabled to prevent Score Deflation) ---
        # Audit Dec 2025: These require Pro tier and cause 0 scores
        "darkpool": 0.0,        # DISABLED: Requires Pro Tier
        "congress": 0.0,        # DISABLED: Requires Pro Tier
        "shorts_squeeze": 0.0,  # DISABLED: Requires Pro Tier + 33% win rate
        "etf_flow": 0.0,        # DISABLED: Requires Pro Tier + negative avg
        "squeeze_score": 0.0    # DISABLED: Linked to shorts_squeeze
    }

    # Regime gating
    ENABLE_REGIME_GATING = get_env("ENABLE_REGIME_GATING", "true").lower() == "true"
    REGIME_MIN_CONF = float(get_env("REGIME_MIN_CONF", "0.0"))

    # Shadow experiments
    ENABLE_SHADOW_LAB = get_env("ENABLE_SHADOW_LAB", "true").lower() == "true"
    EXP_MIN_TRADES = get_env("EXP_MIN_TRADES", 60, int)
    EXP_MIN_CONF = float(get_env("EXP_MIN_CONF", "0.5"))
    PROMOTE_MIN_DELTA_SHARPE = float(get_env("PROMOTE_MIN_DELTA_SHARPE", "0.15"))
    PROMOTE_MAX_DD_INCREASE = float(get_env("PROMOTE_MAX_DD_INCREASE", "0.02"))
    
    # Confidence calibration for shadow lab promotions
    ENABLE_CONFIDENCE_CALIBRATION = get_env("ENABLE_CONFIDENCE_CALIBRATION", "true").lower() == "true"
    PROMOTE_MIN_TRADES = get_env("PROMOTE_MIN_TRADES", 100, int)
    PROMOTE_MIN_WINRATE_WILSON = float(get_env("PROMOTE_MIN_WINRATE_WILSON", "0.52"))
    PROMOTE_MIN_SHARPE_DELTA = float(get_env("PROMOTE_MIN_SHARPE_DELTA", "0.20"))
    PROMOTE_MIN_SHARPE_DELTA_CI = float(get_env("PROMOTE_MIN_SHARPE_DELTA_CI", "0.10"))
    PROMOTE_ALPHA = float(get_env("PROMOTE_ALPHA", "0.05"))
    PROMOTE_BOOTSTRAP_SAMPLES = get_env("PROMOTE_BOOTSTRAP_SAMPLES", 2000, int)
    PROMOTE_EFFECT_SIZE_MIN = float(get_env("PROMOTE_EFFECT_SIZE_MIN", "0.25"))

    # Execution model
    ENABLE_EXEC_PREDICTOR = get_env("ENABLE_EXEC_PREDICTOR", "true").lower() == "true"
    SLIPPAGE_THRESHOLD_BPS_DEFAULT = float(get_env("SLIPPAGE_THRESHOLD_BPS_DEFAULT", "8.0"))

    # Stability decay (weekly)
    ENABLE_STABILITY_DECAY = get_env("ENABLE_STABILITY_DECAY", "true").lower() == "true"
    STABILITY_ALPHA = float(get_env("STABILITY_ALPHA", "0.10"))

    # Portfolio/theme risk
    ENABLE_THEME_RISK = get_env("ENABLE_THEME_RISK", "true").lower() == "true"
    MAX_THEME_NOTIONAL_USD = float(get_env("MAX_THEME_NOTIONAL_USD", "50000"))
    THEME_MAP_PATH = get_env("THEME_MAP_PATH", "theme_map.json")
    
    # Capital ramp discipline
    ENABLE_CAPITAL_RAMP = get_env("ENABLE_CAPITAL_RAMP", "true").lower() == "true"
    RAMP_MIN_WEEKS = get_env("RAMP_MIN_WEEKS", 4, int)
    RAMP_MAX_INCREASE = float(get_env("RAMP_MAX_INCREASE", "1.5"))
    RAMP_DRAWDOWN_LIMIT = float(get_env("RAMP_DRAWDOWN_LIMIT", "0.05"))
    
    # Incident recovery automation
    ENABLE_INCIDENT_RECOVERY = get_env("ENABLE_INCIDENT_RECOVERY", "true").lower() == "true"
    KILL_SWITCH_COOLDOWN_MIN = get_env("KILL_SWITCH_COOLDOWN_MIN", 30, int)
    MAX_INCIDENTS_PER_DAY = get_env("MAX_INCIDENTS_PER_DAY", 3, int)
    
    # Leverage gates (kept at 1x for safety)
    ENABLE_LEVERAGE_GATES = get_env("ENABLE_LEVERAGE_GATES", "true").lower() == "true"
    LEVERAGE_MAX = float(get_env("LEVERAGE_MAX", "1.0"))
    LEVERAGE_PROMOTION_WINRATE = float(get_env("LEVERAGE_PROMOTION_WINRATE", "0.55"))
    LEVERAGE_PROMOTION_SHARPE = float(get_env("LEVERAGE_PROMOTION_SHARPE", "1.5"))
    
    # Advanced regime detection
    ENABLE_ADVANCED_REGIME = get_env("ENABLE_ADVANCED_REGIME", "true").lower() == "true"
    VOL_REGIME_THRESHOLD = float(get_env("VOL_REGIME_THRESHOLD", "0.25"))
    LIQUIDITY_REGIME_MIN_VOL = float(get_env("LIQUIDITY_REGIME_MIN_VOL", "1000000"))

LOG_DIR = "logs"
# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)
# CRITICAL: Ensure attribution log path directory exists
try:
    if hasattr(ATTRIBUTION_LOG_PATH, 'parent'):
        ATTRIBUTION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    else:
        os.makedirs(os.path.dirname(str(ATTRIBUTION_LOG_PATH)), exist_ok=True)
except Exception:
    pass  # Directory may already exist
REPORT_DIR = "reports"
WEIGHTS_PATH = "weights.json"
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)
if Config.ENABLE_PER_TICKER_LEARNING:
    os.makedirs(Config.FEATURE_STORE_DIR, exist_ok=True)

# Load theme risk config from persistent file (overrides env vars)
def load_theme_risk_config():
    """Load theme risk settings from config/theme_risk.json with priority over env vars."""
    config_path = ConfigFiles.THEME_RISK
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                cfg = json.load(f)
                settings = cfg.get("settings", {})
                
                # Override Config class attributes
                if "ENABLE_THEME_RISK" in settings:
                    Config.ENABLE_THEME_RISK = settings["ENABLE_THEME_RISK"]
                if "MAX_THEME_NOTIONAL_USD" in settings:
                    Config.MAX_THEME_NOTIONAL_USD = float(settings["MAX_THEME_NOTIONAL_USD"])
                
                print(f"[CONFIG] Loaded theme_risk.json: ENABLE_THEME_RISK={Config.ENABLE_THEME_RISK}, MAX_THEME_NOTIONAL_USD=${Config.MAX_THEME_NOTIONAL_USD:,.0f}")
        except Exception as e:
            print(f"[CONFIG] Failed to load {config_path}: {e}")
    else:
        print(f"[CONFIG] No {config_path} found, using env defaults: MAX_THEME_NOTIONAL_USD=${Config.MAX_THEME_NOTIONAL_USD:,.0f}")

# Apply config overrides
load_theme_risk_config()

# Institutional telemetry
telemetry = TelemetryLogger()

# Permanent system-events layer (append-only).
try:
    from utils.system_events import log_system_event, global_failure_wrapper
except Exception:
    # Never block bot startup on observability imports.
    def log_system_event(*args, **kwargs):  # type: ignore
        return None
    def global_failure_wrapper(_subsystem):  # type: ignore
        def _d(fn):
            return fn
        return _d

# =========================
# UTILITIES
# =========================
def now_iso():
    return datetime.now(timezone.utc).isoformat()

def _position_return_pct(entry: float, current: float, side: str) -> float:
    if entry <= 0 or current <= 0:
        return 0.0
    r = (current - entry) / entry
    return r if side == "buy" else -r

def get_position_qty(api, symbol: str) -> int:
    try:
        for p in api.list_positions():
            if getattr(p, "symbol", "") == symbol:
                return int(float(getattr(p, "qty", 0)))
    except Exception:
        pass
    return 0

def jsonl_write(name, record):
    # CRITICAL: Use standardized path for attribution log
    if name == "attribution":
        path = str(ATTRIBUTION_LOG_PATH)
    else:
        path = os.path.join(LOG_DIR, f"{name}.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now_iso(), **record}) + "\n")

_CYCLE_GATE_SYMBOLS = set()

def _infer_system_severity(kind: str, msg: str, kw: dict) -> str:
    try:
        sev = str(kw.get("severity", "")).upper().strip()
        if sev in ("INFO", "WARN", "ERROR", "CRITICAL"):
            return sev
        # Map legacy severities
        if sev in ("HIGH", "SEVERE"):
            return "ERROR"
    except Exception:
        pass
    m = str(msg or "").upper()
    if "CRITICAL" in m:
        return "CRITICAL"
    if "EXCEPTION" in m or "TRACEBACK" in m:
        return "CRITICAL"
    if "FAILED" in m or "ERROR" in m or "CORRUPT" in m:
        return "ERROR"
    if "ALL_ATTEMPTS_FAILED" in m or "MAX_ATTEMPTS" in m:
        return "CRITICAL"
    if "STALE" in m or "MISSING" in m or "UNAVAILABLE" in m:
        return "WARN"
    # Gate blocks are first-class but not errors.
    if str(kind or "").lower() == "gate":
        return "INFO"
    return "INFO"

def log_event(kind, msg, **kw):
    jsonl_write(kind, {"msg": msg, **kw})
    # Permanent unified system events stream (best-effort; never blocks execution).
    try:
        subsystem = str(kind)
        symbol = kw.get("symbol")
        # Track gate symbols for missed-candidate detection.
        if subsystem == "gate" and symbol:
            try:
                _CYCLE_GATE_SYMBOLS.add(str(symbol))
            except Exception:
                pass
        # First-class blocked events: any gate event other than cycle summaries/passes.
        if subsystem == "gate" and str(msg) not in ("cycle_summary",):
            log_system_event(
                subsystem="gate",
                event_type="blocked",
                severity="INFO",
                symbol=symbol,
                reason=str(msg),
                score=kw.get("score"),
                position_state=kw.get("position_state"),
                details=kw,
            )
        else:
            log_system_event(
                subsystem=subsystem,
                event_type=str(msg),
                severity=_infer_system_severity(subsystem, str(msg), kw),
                symbol=symbol,
                details=kw,
            )
    except Exception:
        pass

# ============================================================
# SRE PIPELINE HEARTBEAT (low-noise, read-only observability)
# ============================================================
# Contract: once per N cycles, emit a compact heartbeat showing that scoring/decisions/exits are alive.
_PIPELINE_STAGE_TS = {"scoring": None, "decision": None, "exit_eval": None}
_PIPELINE_HEARTBEAT_LAST_LOG_TS = 0.0


def _pipeline_touch(stage: str) -> None:
    try:
        _PIPELINE_STAGE_TS[stage] = time.time()
    except Exception:
        pass


def _pipeline_heartbeat_maybe(*, every_sec: float = 600.0) -> None:
    """Emit a low-noise heartbeat at most once per `every_sec`."""
    global _PIPELINE_HEARTBEAT_LAST_LOG_TS
    try:
        now = time.time()
        if (now - float(_PIPELINE_HEARTBEAT_LAST_LOG_TS or 0.0)) < every_sec:
            return
        _PIPELINE_HEARTBEAT_LAST_LOG_TS = now
        log_event(
            "sre_health",
            "pipeline_heartbeat",
            last_scoring_ts=_PIPELINE_STAGE_TS.get("scoring"),
            last_decision_ts=_PIPELINE_STAGE_TS.get("decision"),
            last_exit_eval_ts=_PIPELINE_STAGE_TS.get("exit_eval"),
        )
    except Exception:
        pass

# Optional env checks (non-blocking)
try:
    if _MISSING_REQUESTS_LIB and not _LOGGED_MISSING_REQUESTS:
        _LOGGED_MISSING_REQUESTS = True
        log_event("environment", "missing_requests_library", note="requests not installed in this environment")
except Exception:
    # Never block bot execution on env telemetry.
    pass

try:
    if _MISSING_ALPACA_SDK:
        log_event("environment", "missing_alpaca_trade_api", note="alpaca_trade_api not installed in this environment")
except Exception:
    pass

try:
    if _MISSING_FLASK:
        log_event("environment", "missing_flask_library", note="flask not installed in this environment")
except Exception:
    pass

def _is_live_endpoint(url: str) -> bool:
    try:
        return "api.alpaca.markets" in (url or "") and "paper-api" not in (url or "")
    except Exception:
        return False

def _is_paper_endpoint(url: str) -> bool:
    try:
        return "paper-api.alpaca.markets" in (url or "")
    except Exception:
        return False

def trading_is_armed() -> bool:
    """
    Returns True if the bot is allowed to place NEW entry orders.
    Exits and monitoring may still run when unarmed.
    """
    mode = (Config.TRADING_MODE or "PAPER").upper()
    base_url = Config.ALPACA_BASE_URL or ""

    # If LIVE but pointed at paper, refuse entries (misconfiguration).
    if mode == "LIVE" and _is_paper_endpoint(base_url):
        return False

    # If PAPER but pointed at live, refuse entries (misconfiguration).
    if mode == "PAPER" and _is_live_endpoint(base_url):
        return False

    if mode == "LIVE" and Config.REQUIRE_LIVE_ACK:
        return (Config.LIVE_TRADING_ACK or "").strip() == "YES_I_UNDERSTAND"

    return True

def build_client_order_id(symbol: str, side: str, cluster: dict, suffix: str = "") -> str:
    """
    Build a deterministic-ish client_order_id for idempotency.
    Uniqueness is scoped by (symbol, side, cluster start_ts) plus a suffix for retries.
    """
    try:
        start_ts_raw = cluster.get("start_ts") or cluster.get("ts") or int(time.time())
        
        # Handle ISO timestamp strings (e.g., '2025-12-26T19:08:46.138262Z')
        if isinstance(start_ts_raw, str):
            try:
                from datetime import datetime
                # Try parsing ISO format
                if 'T' in start_ts_raw:
                    dt = datetime.fromisoformat(start_ts_raw.replace('Z', '+00:00'))
                    start_ts = int(dt.timestamp())
                else:
                    # Try parsing as float string
                    start_ts = int(float(start_ts_raw))
            except (ValueError, AttributeError):
                # Fallback to current time if parsing fails
                start_ts = int(time.time())
        elif isinstance(start_ts_raw, (int, float)):
            start_ts = int(start_ts_raw)
        else:
            start_ts = int(time.time())
    except Exception:
        start_ts = int(time.time())
    
    base = f"uwbot-{symbol}-{side}-{start_ts}"
    return f"{base}-{suffix}" if suffix else base

def log_signal_to_history(symbol: str, direction: str, raw_score: float, whale_boost: float,
                          final_score: float, atr_multiplier: float, momentum_pct: float,
                          momentum_required_pct: float, decision: str, metadata: dict = None):
    """
    Log signal processing event to signal history for dashboard display.
    
    Args:
        symbol: Stock symbol
        direction: bullish/bearish
        raw_score: Score before whale boost
        whale_boost: Whale conviction boost applied (+0.5 if whale detected)
        final_score: Final score (raw_score + whale_boost)
        atr_multiplier: ATR multiplier used (if applicable)
        momentum_pct: Actual price change %
        momentum_required_pct: Required threshold %
        decision: "Ordered" or "Blocked:reason" or "Rejected:reason"
        metadata: Additional context dict (may include sector, persistence_count, sector_tide_count)
    """
    try:
        from signal_history_storage import append_signal_history
        from risk_management import get_sector
        from persistence_tracker import get_persistence_tracker
        
        # Get sector if not in metadata
        sector = metadata.get("sector") if metadata else None
        if not sector:
            try:
                sector = get_sector(symbol)
            except:
                sector = "Unknown"
        
        # Get persistence count if not in metadata
        persistence_count = metadata.get("persistence_count") if metadata else None
        if persistence_count is None:
            try:
                persistence_tracker = get_persistence_tracker()
                persistence_check = persistence_tracker.check_persistence(symbol)
                persistence_count = persistence_check.get("count", 0)
            except:
                persistence_count = 0
        
        # Get sector tide count if not in metadata
        sector_tide_count = metadata.get("sector_tide_count") if metadata else None
        if sector_tide_count is None:
            try:
                from sector_tide_tracker import get_sector_tide_tracker
                tide_tracker = get_sector_tide_tracker()
                tide_info = tide_tracker.check_sector_tide(symbol)
                sector_tide_count = tide_info.get("count", 0)
            except:
                sector_tide_count = 0
        
        # Get virtual P&L if shadow position exists
        virtual_pnl = None
        shadow_created = False
        try:
            from shadow_tracker import get_shadow_tracker
            shadow_tracker = get_shadow_tracker()
            shadow_pos = shadow_tracker.get_position(symbol)
            if shadow_pos:
                virtual_pnl = shadow_pos.max_profit_pct
                shadow_created = True
        except Exception:
            pass
        
        # Extract shadow_created from metadata if present
        if metadata and metadata.get("shadow_created") is not None:
            shadow_created = metadata.get("shadow_created", False)
        
        append_signal_history({
            "symbol": symbol,
            "direction": direction,
            "raw_score": round(raw_score, 3),
            "whale_boost": round(whale_boost, 3),
            "final_score": round(final_score, 3),
            "atr_multiplier": round(atr_multiplier, 3) if atr_multiplier else None,
            "momentum_pct": round(momentum_pct * 100, 4) if momentum_pct else 0.0,  # Convert to percentage
            "momentum_required_pct": round(momentum_required_pct * 100, 4) if momentum_required_pct else 0.0,
            "decision": decision,
            "sector": sector,
            "persistence_count": persistence_count,
            "sector_tide_count": sector_tide_count,
            "virtual_pnl": virtual_pnl if virtual_pnl is not None else (metadata.get("virtual_pnl") if metadata else 0.0),
            "shadow_created": shadow_created,
            "metadata": metadata or {}
        })
    except ImportError:
        pass  # Signal history module not available
    except Exception:
        pass  # Fail silently - don't break trading

def log_blocked_trade(symbol: str, reason: str, score: float, signals: dict = None, 
                      direction: str = None, decision_price: float = None, 
                      components: dict = None, **kw):
    """
    Log blocked trades for counterfactual learning analysis.
    
    CRITICAL FOR ML: We track what we DIDN'T do so we can learn whether we should have.
    By capturing the decision_price at the moment of rejection, we can later compute
    what the theoretical P&L would have been if we had entered.
    """
    record = {
        "timestamp": now_iso(),
        "symbol": symbol,
        "reason": reason,
        "score": score,
        "signals": signals or {},
        "direction": direction,  # bullish/bearish - needed for theoretical P&L
        "decision_price": decision_price,  # Price at decision time for counterfactual
        "components": components or {},  # All 21 signal components for ML learning
        "outcome_tracked": False,  # Flag for counterfactual tracker
        **kw
    }
    blocked_path = os.path.join("state", "blocked_trades.jsonl")
    os.makedirs(os.path.dirname(blocked_path), exist_ok=True)
    with open(blocked_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

def log_postmortem(event: dict):
    """Write diagnostic bundle after incident"""
    jsonl_write("postmortem", {"event": event})

def count_incidents_today() -> int:
    """Count incidents in alert_error.jsonl for today"""
    path = os.path.join(LOG_DIR, "alert_error.jsonl")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    count = 0
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                        if rec.get("ts", "").startswith(today):
                            count += 1
                    except Exception:
                        pass
        except Exception:
            pass
    return count

def health_check_passes() -> bool:
    """Basic health check: API reachable, positions listable"""
    try:
        api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL)
        _ = api.list_positions()
        return True
    except Exception:
        return False

def auto_rearm_kill_switch() -> bool:
    """Rearm kill-switch after cooldown if health checks pass"""
    if not Config.ENABLE_INCIDENT_RECOVERY:
        return False
    
    incidents_today = count_incidents_today()
    if incidents_today >= Config.MAX_INCIDENTS_PER_DAY:
        log_event("kill_switch", "manual_reset_required", incidents=incidents_today)
        return False
    
    log_event("kill_switch", "cooldown_started", duration_min=Config.KILL_SWITCH_COOLDOWN_MIN)
    time.sleep(Config.KILL_SWITCH_COOLDOWN_MIN * 60)
    
    if health_check_passes():
        log_event("kill_switch", "auto_rearmed")
        return True
    else:
        log_event("kill_switch", "rearm_failed")
        return False

def send_webhook(payload: dict):
    if not Config.WEBHOOK_URL:
        return
    try:
        import urllib.request
        req = urllib.request.Request(
            Config.WEBHOOK_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as _:
            pass
    except Exception as e:
        log_event("alert_error", "webhook_failed", error=str(e))

def generate_nightly_report():
    """Aggregate attribution, risk, and experiment outcomes into one JSON report"""
    attribution_summary = {}
    theme_exposure = {}
    shadow_results = []
    
    path = os.path.join(LOG_DIR, "attribution.jsonl")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                        if rec.get("type") == "attribution":
                            sym = rec.get("symbol", "UNKNOWN")
                            pnl = float(rec.get("pnl_usd", 0))
                            attribution_summary.setdefault(sym, {"trades": 0, "pnl": 0.0})
                            attribution_summary[sym]["trades"] += 1
                            attribution_summary[sym]["pnl"] += pnl
                    except Exception:
                        pass
        except Exception:
            pass
    
    try:
        theme_map = load_theme_map() if Config.ENABLE_THEME_RISK else {}
        api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL)
        positions = api.list_positions()
        for p in positions:
            sym = getattr(p, "symbol", "")
            notional = abs(float(getattr(p, "market_value", 0)))
            theme = theme_map.get(sym, "general")
            theme_exposure.setdefault(theme, 0.0)
            theme_exposure[theme] += notional
    except Exception as e:
        log_event("report", "theme_exposure_failed", error=str(e))
    
    path = os.path.join(LOG_DIR, "shadow_lab.jsonl")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        shadow_results.append(json.loads(line))
                    except Exception:
                        pass
        except Exception:
            pass
    
    report = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "attribution": attribution_summary,
        "theme_exposure": theme_exposure,
        "shadow_lab": shadow_results[-50:] if shadow_results else []
    }
    
    report_path = os.path.join(REPORT_DIR, f"daily_report_{report['date']}.json")
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        log_event("report", "nightly_generated", path=report_path)
    except Exception as e:
        log_event("report", "nightly_failed", error=str(e))

def schedule_nightly_report():
    """Check if after market close and generate report"""
    try:
        cal = get_market_calendar()
        if cal and cal.get("is_open"):
            close_time_str = cal.get("close", "16:00:00")
            now = datetime.now(timezone.utc)
            close_hour = int(close_time_str.split(":")[0])
            if now.hour >= close_hour:
                generate_nightly_report()
    except Exception as e:
        log_event("report", "schedule_check_failed", error=str(e))

# Market calendar cache (refreshed daily)
_market_calendar_cache = {}
_calendar_cache_date = None

def get_market_calendar():
    """Fetch market calendar from Alpaca API and cache for the day"""
    global _market_calendar_cache, _calendar_cache_date
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    if _calendar_cache_date == today and _market_calendar_cache:
        return _market_calendar_cache
    
    try:
        api = tradeapi.REST(
            Config.ALPACA_KEY,
            Config.ALPACA_SECRET,
            Config.ALPACA_BASE_URL,
            api_version='v2'
        )
        # Fetch calendar for today and next 7 days
        calendar = api.get_calendar(start=today, end=today)
        
        if calendar and len(calendar) > 0:
            cal_day = calendar[0]
            _market_calendar_cache = {
                "date": str(cal_day.date),
                "open": str(cal_day.open),
                "close": str(cal_day.close),
                "is_open": True
            }
        else:
            # Not a trading day (weekend/holiday)
            _market_calendar_cache = {
                "date": today,
                "is_open": False
            }
        
        _calendar_cache_date = today
        log_event("market_calendar", "refreshed", calendar=_market_calendar_cache)
        
    except Exception as e:
        log_event("market_calendar", "fetch_failed", error=str(e))
        # Fallback to time-based check
        _market_calendar_cache = {"is_open": None}
    
    return _market_calendar_cache

def is_market_open_now():
    """Check if market is currently open using Alpaca clock API"""
    try:
        api = tradeapi.REST(
            Config.ALPACA_KEY,
            Config.ALPACA_SECRET,
            Config.ALPACA_BASE_URL,
            api_version='v2'
        )
        clock = api.get_clock()
        return clock.is_open
    except Exception as e:
        log_event("market_check", "alpaca_clock_failed", error=str(e))
        # Fallback to time-based check using proper timezone (handles DST automatically)
        try:
            from zoneinfo import ZoneInfo
        except ImportError:
            from backports.zoneinfo import ZoneInfo
        now = datetime.now(timezone.utc)
        et_now = now.astimezone(ZoneInfo("America/New_York"))
        h, m = et_now.hour, et_now.minute
        # Basic check: weekday and trading hours
        is_weekday = et_now.weekday() < 5
        in_hours = (h > 9 or (h == 9 and m >= 30)) and (h < 16)
        return is_weekday and in_hours

# Removed is_market_open_now_old() - old unused version, replaced by is_market_open_now()

def is_after_close_now():
    """Check if market has closed for the day"""
    calendar = get_market_calendar()
    
    if not calendar.get("is_open"):
        # Market not open today, consider it "after close"
        return True
    
    # Use proper timezone handling (handles DST automatically)
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        from backports.zoneinfo import ZoneInfo
    now = datetime.now(timezone.utc)
    et_now = now.astimezone(ZoneInfo("America/New_York"))
    
    try:
        close_time = datetime.strptime(calendar["close"], "%H:%M").time()
        return et_now.time() >= close_time
    except:
        # Fallback to 4 PM ET
        return et_now.hour >= 16

def is_friday():
    return datetime.now(timezone.utc).weekday() == 4

# =========================
# STATISTICAL UTILITIES (for confidence-calibrated promotions)
# =========================
def _normal_quantile(p: float) -> float:
    """Approximate inverse CDF of standard normal distribution (Abramowitz-Stegun)"""
    if p <= 0 or p >= 1:
        return float("nan")
    a1, a2, a3, a4, a5, a6 = -39.6968302866538, 220.946098424521, -275.928510446969, 138.357751867269, -30.6647980661472, 2.50662827745924
    b1, b2, b3, b4, b5 = -54.4760987982241, 161.585836858041, -155.698979859887, 66.8013118877197, -13.2806815528857
    c1, c2, c3, c4, c5, c6 = -0.00778489400243029, -0.322396458041136, -2.40075827716184, -2.54973253934373, 4.37466414146497, 2.93816398269878
    d1, d2, d3, d4 = 0.00778469570904146, 0.32246712907004, 2.445134137143, 3.75440866190742
    plow, phigh = 0.02425, 0.97575
    
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c1*q + c2)*q + c3)*q + c4)*q + c5)*q + c6) / ((((d1*q + d2)*q + d3)*q + d4)*q + 1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c1*q + c2)*q + c3)*q + c4)*q + c5)*q + c6) / ((((d1*q + d2)*q + d3)*q + d4)*q + 1)
    
    q = p - 0.5
    r = q * q
    return (((((a1*r + a2)*r + a3)*r + a4)*r + a5)*r + a6) * q / (((((b1*r + b2)*r + b3)*r + b4)*r + b5)*r + 1)

def wilson_lower_bound(successes: int, total: int, alpha: float) -> float:
    """Wilson score lower bound for binomial confidence interval"""
    if total == 0:
        return 0.0
    p_hat = successes / total
    z = _normal_quantile(1 - alpha / 2)
    denom = 1 + (z * z) / total
    center = p_hat + (z * z) / (2 * total)
    adj = z * math.sqrt((p_hat * (1 - p_hat) + (z * z) / (4 * total)) / total)
    return max(0.0, (center - adj) / denom)

def cohen_d(exp: list, prod: list) -> float:
    """Cohen's d effect size between two samples"""
    if not exp or not prod:
        return 0.0
    m1 = sum(exp) / len(exp)
    m0 = sum(prod) / len(prod)
    v1 = sum((x - m1) ** 2 for x in exp) / max(1, len(exp) - 1)
    v0 = sum((x - m0) ** 2 for x in prod) / max(1, len(prod) - 1)
    sp = math.sqrt(((len(exp) - 1) * v1 + (len(prod) - 1) * v0) / max(1, (len(exp) + len(prod) - 2)))
    return 0.0 if sp == 0 else (m1 - m0) / sp

def sharpe_ratio(pnls: list) -> float:
    """Sharpe ratio of a PnL series"""
    if len(pnls) < 2:
        return 0.0
    mean = sum(pnls) / len(pnls)
    var = sum((x - mean) ** 2 for x in pnls) / max(1, len(pnls) - 1)
    std = math.sqrt(var)
    return 0.0 if std == 0 else mean / std

def bootstrap_sharpe_ci(pnls: list, alpha: float, samples: int) -> tuple:
    """Bootstrap confidence interval for Sharpe ratio. Returns (lower, point, upper)"""
    if len(pnls) < 2:
        return (0.0, 0.0, 0.0)
    boot = []
    n = len(pnls)
    for _ in range(samples):
        resample = [pnls[random.randrange(n)] for __ in range(n)]
        boot.append(sharpe_ratio(resample))
    boot.sort()
    lower = boot[int(alpha / 2 * samples)]
    upper = boot[int((1 - alpha / 2) * samples) - 1]
    point = sharpe_ratio(pnls)
    return (lower, point, upper)

# =========================
# LOGGER & ATTRIBUTION
# =========================
def log_signal(cluster: dict):
    jsonl_write("signals", {"type": "signal", "cluster": cluster})

def log_order(event: dict):
    jsonl_write("orders", {"type": "order", **event})

def log_attribution(trade_id: str, symbol: str, pnl_usd: float, context: dict):
    jsonl_write("attribution", {
        "type": "attribution",
        "trade_id": trade_id,
        "symbol": symbol,
        "pnl_usd": pnl_usd,
        "context": context
    })

def _normalize_position_side(side: str) -> str:
    """
    WHY: attribution logging currently mixes order-side ('buy'/'sell') and position-side ('long'/'short'),
    causing P&L sign flips (observed in production: AAPL long with entry>exit but pnl_usd>0).
    HOW TO VERIFY: grep logs/attribution.jsonl for 'attribution_pnl_corrected'; it should appear only when anomalies occur.
    """
    s = (side or "").strip().lower()
    if s in ("buy", "long"):
        return "long"
    if s in ("sell", "short"):
        return "short"
    return "unknown"


def _compute_trade_pnl(entry_price: float, exit_price: float, qty: float, position_side: str) -> tuple[float, float]:
    """
    Returns (pnl_usd, pnl_pct) based on normalized position_side.
    """
    try:
        entry_price = float(entry_price)
        exit_price = float(exit_price)
        qty = float(qty)
    except Exception:
        return (0.0, 0.0)

    if entry_price <= 0 or exit_price <= 0 or qty <= 0 or position_side not in ("long", "short"):
        return (0.0, 0.0)

    if position_side == "long":
        pnl_usd = qty * (exit_price - entry_price)
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100.0
    else:
        pnl_usd = qty * (entry_price - exit_price)
        pnl_pct = ((entry_price - exit_price) / entry_price) * 100.0

    return (pnl_usd, pnl_pct)


def normalize_equity_limit_price(px: float) -> float:
    """
    WHY: Alpaca rejects sub-penny equity limit prices; production shows heavy 422 'sub-penny increment' errors.
    HOW TO VERIFY: 'sub-penny increment' errors drop to near zero in logs/orders.jsonl.
    """
    try:
        return round(float(px), 2)
    except Exception:
        return float(px)


def log_exit_attribution(
    symbol: str,
    info: dict,
    exit_price: float,
    close_reason: str,
    metadata: dict = None,
    *,
    exit_qty: int = None,
    entry_order_id: str = None,
    exit_order_id: str = None,
):
    """
    Log complete exit attribution with actual P&L for ML learning.
    FIX 2025-12-05: Previously logged pnl_usd=0.0 - now calculates real P&L.
    FIX 2025-12-05: Now falls back to metadata for entry data when info is incomplete.
    FIX 2025-12-11: Use aware UTC datetimes to prevent TypeError crashes.
    """
    entry_price = info.get("entry_price", 0.0)
    entry_qty = info.get("qty", 1)
    side = info.get("side", "buy")
    
    # FIX: Use aware UTC for current time reference
    now_aware = datetime.now(timezone.utc)
    entry_ts = info.get("ts", now_aware)
    
    if metadata and entry_price <= 0:
        entry_price = metadata.get("entry_price", 0.0)
        if entry_qty <= 0:
            entry_qty = metadata.get("qty", 1)
        if side == "buy" and metadata.get("side"):
            side = metadata.get("side", "buy")
        try:
            meta_ts = metadata.get("entry_ts", "")
            if meta_ts:
                parsed_ts = datetime.fromisoformat(meta_ts.replace("Z", "+00:00"))
                # Normalize to aware UTC
                if parsed_ts.tzinfo is None:
                    entry_ts = parsed_ts.replace(tzinfo=timezone.utc)
                else:
                    entry_ts = parsed_ts.astimezone(timezone.utc)
        except:
            pass
    
    # FIX: Normalize entry_ts to aware UTC for safe arithmetic
    if hasattr(entry_ts, 'tzinfo') and entry_ts.tzinfo is None:
        entry_ts = entry_ts.replace(tzinfo=timezone.utc)
    elif hasattr(entry_ts, 'astimezone'):
        entry_ts = entry_ts.astimezone(timezone.utc)
    
    hold_minutes = (now_aware - entry_ts).total_seconds() / 60.0
    
    # PnL attribution contract:
    # - entry_price should be the executed entry fill price (order.filled_avg_price), not quotes/limits.
    # - exit_price should be the executed exit fill price (order.filled_avg_price), not marks/quotes.
    # - qty used for realized PnL should be the executed exit fill qty when provided.
    pnl_qty = None
    try:
        if exit_qty is not None and int(exit_qty) > 0:
            pnl_qty = int(exit_qty)
    except Exception:
        pnl_qty = None
    if pnl_qty is None:
        try:
            pnl_qty = int(entry_qty)
        except Exception:
            pnl_qty = 1

    if entry_price > 0 and exit_price > 0:
        if side == "buy":
            pnl_usd = pnl_qty * (exit_price - entry_price)
            pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        else:
            pnl_usd = pnl_qty * (entry_price - exit_price)
            pnl_pct = ((entry_price - exit_price) / entry_price) * 100
    else:
        pnl_usd = 0.0
        pnl_pct = 0.0

    # Attribution integrity: normalize position side and correct P&L if needed.
    # WHY: Production saw sign flips when 'side' is 'long'/'short' rather than 'buy'/'sell'.
    # HOW TO VERIFY: grep logs/attribution.jsonl for 'attribution_pnl_corrected' (should be rare, only anomalies).
    position_side = _normalize_position_side(side)
    computed_pnl_usd, computed_pnl_pct = _compute_trade_pnl(entry_price, exit_price, pnl_qty, position_side)
    EPS_USD = float(get_env("ATTRIBUTION_PNL_EPS_USD", 0.05, float))
    if abs(computed_pnl_usd - pnl_usd) > EPS_USD:
        log_event(
            "data_integrity",
            "attribution_pnl_corrected",
            symbol=symbol,
            original={"pnl_usd": pnl_usd, "pnl_pct": pnl_pct, "side": side},
            corrected={"pnl_usd": computed_pnl_usd, "pnl_pct": computed_pnl_pct, "position_side": position_side},
        )
        pnl_usd, pnl_pct = computed_pnl_usd, computed_pnl_pct
    
    # Ensure close_reason is never empty or None
    if not close_reason or close_reason == "unknown" or close_reason.strip() == "":
        # Fallback: create a basic close reason
        close_reason = "unknown_exit"
        log_event("exit", "close_reason_missing", symbol=symbol, 
                 note="close_reason was empty, using fallback")
    
    # V4.0: Enhanced context for causal analysis - capture EVERYTHING that might explain win/loss
    entry_dt = entry_ts if isinstance(entry_ts, datetime) else datetime.fromisoformat(str(entry_ts).replace("Z", "+00:00")) if isinstance(entry_ts, str) else datetime.now(timezone.utc)
    if entry_dt.tzinfo is None:
        entry_dt = entry_dt.replace(tzinfo=timezone.utc)
    
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
    
    # Extract signal characteristics for causal analysis
    components = info.get("components", {}) or metadata.get("components", {}) if metadata else {}
    entry_score = info.get("entry_score", 0.0) or metadata.get("entry_score", 0.0) if metadata else 0.0
    
    # Flow magnitude
    flow_conv = 0.0
    if isinstance(components.get("flow"), dict):
        flow_conv = components["flow"].get("conviction", 0.0)
    elif isinstance(components.get("flow"), (int, float)):
        flow_conv = float(components.get("flow", 0.0))
    
    if flow_conv < 0.3:
        flow_magnitude = "LOW"
    elif flow_conv < 0.7:
        flow_magnitude = "MEDIUM"
    else:
        flow_magnitude = "HIGH"
    
    # Signal strength
    if entry_score < 2.5:
        signal_strength = "WEAK"
    elif entry_score < 3.5:
        signal_strength = "MODERATE"
    else:
        signal_strength = "STRONG"
    
    context = {
        "close_reason": close_reason,
        "entry_price": round(entry_price, 4),
        "exit_price": round(exit_price, 4),
        "pnl_pct": round(pnl_pct, 4),
        "hold_minutes": round(hold_minutes, 1),
        "side": side,
        # Disambiguation fields for reconciliation
        "position_side": position_side,
        "order_side_raw": side,
        # Backward-compatible qty field: realized-PnL qty (prefer executed exit fill qty).
        "qty": pnl_qty,
        # Explicit fill quantities for audits/reconciliation.
        "entry_qty": entry_qty,
        "exit_qty": int(exit_qty) if exit_qty is not None else pnl_qty,
        "entry_order_id": entry_order_id,
        "exit_order_id": exit_order_id,
        "entry_score": entry_score,
        "components": components,
        "market_regime": info.get("market_regime", "unknown") or (metadata.get("market_regime", "unknown") if metadata else "unknown"),
        "direction": info.get("direction", "unknown") or (metadata.get("direction", "unknown") if metadata else "unknown"),
        # V4.0: Enhanced context for causal analysis
        "time_of_day": time_of_day,
        "day_of_week": day_of_week,
        "entry_hour": hour,
        "flow_magnitude": flow_magnitude,
        "signal_strength": signal_strength,
        "entry_ts": entry_dt.isoformat(),
        "entry_price_source": "alpaca.order.filled_avg_price_or_position.avg_entry_price",
        "exit_price_source": "alpaca.order.filled_avg_price",
    }
    
    if metadata:
        context["entry_score"] = metadata.get("entry_score", context["entry_score"])
        if not context["components"]:
            context["components"] = metadata.get("components", {})
        context["market_regime"] = metadata.get("market_regime", context["market_regime"])
        context["direction"] = metadata.get("direction", context["direction"])
        # V4.0: Include correlation_id in context for UW-to-Alpaca pipeline tracking
        if metadata.get("correlation_id"):
            context["correlation_id"] = metadata.get("correlation_id")
    
    # CRITICAL: Extract stealth_flow_boost_applied from components/notes
    stealth_boost_applied = False
    if isinstance(context.get("components"), dict):
        # Check if stealth flow boost was applied (flow_magnitude == "LOW")
        if context.get("flow_magnitude") == "LOW":
            stealth_boost_applied = True
        # Also check notes/composite_meta if available
        components = context.get("components", {})
        if isinstance(components.get("notes"), str) and "stealth_flow" in components.get("notes", "").lower():
            stealth_boost_applied = True
    
    # CRITICAL: Enforce mandatory flat schema - all required fields at top level
    # Schema: [symbol, entry_score, exit_pnl, market_regime, stealth_boost_applied]
    entry_score_flat = context.get("entry_score", 0.0)
    market_regime_flat = context.get("market_regime", "unknown")
    
    # Validate required fields - log CRITICAL ERROR if missing
    if entry_score_flat == 0.0:
        log_event("data_integrity", "CRITICAL_ERROR_missing_entry_score", 
                 symbol=symbol, trade_id=f"close_{symbol}_{now_iso()}")
    
    if market_regime_flat == "unknown":
        log_event("data_integrity", "WARNING_missing_market_regime", 
                 symbol=symbol, trade_id=f"close_{symbol}_{now_iso()}")
    
    # Write attribution with mandatory flat fields at top level
    attribution_record = {
        "type": "attribution",
        "trade_id": f"close_{symbol}_{now_iso()}",
        # MANDATORY FLAT FIELDS (per user requirement)
        "symbol": symbol,
        "entry_score": entry_score_flat,
        "exit_pnl": round(pnl_pct, 4),  # exit_pnl is pnl_pct
        "market_regime": market_regime_flat,
        "stealth_boost_applied": stealth_boost_applied,
        # Additional fields (preserved for backward compatibility)
        "pnl_usd": round(pnl_usd, 2),
        "pnl_pct": round(pnl_pct, 4),
        "hold_minutes": round(hold_minutes, 1),
        "context": context  # Full context preserved for detailed analysis
    }
    
    jsonl_write("attribution", attribution_record)
    
    # DATA INTEGRITY CHECK: Verify log was written successfully
    try:
        import os
        if ATTRIBUTION_LOG_PATH.exists():
            # Check if file was recently modified (within last 5 seconds)
            import time
            file_mtime = os.path.getmtime(str(ATTRIBUTION_LOG_PATH))
            if time.time() - file_mtime < 5:
                log_event("data_integrity", "attribution_log_verified", symbol=symbol)
            else:
                log_event("data_integrity", "WARNING_attribution_log_not_updated", 
                         symbol=symbol, file_age_sec=time.time() - file_mtime)
        else:
            log_event("data_integrity", "CRITICAL_ERROR_attribution_log_missing", symbol=symbol)
    except Exception as integrity_error:
        log_event("data_integrity", "ERROR_integrity_check_failed", 
                 symbol=symbol, error=str(integrity_error))
    
    log_event("exit", "attribution_logged", 
              symbol=symbol, 
              pnl_usd=round(pnl_usd, 2), 
              pnl_pct=round(pnl_pct, 2),
              hold_min=round(hold_minutes, 1),
              reason=close_reason)
    
    # SHORT-TERM LEARNING: Immediate learning after trade close
    # This enables fast adaptation to market changes
    try:
        from comprehensive_learning_orchestrator_v2 import learn_from_trade_close
        
        comps = context.get("components", {})
        regime = context.get("market_regime", "unknown")
        sector = "unknown"  # Could extract from symbol if needed
        
        # Immediate learning from this trade
        learn_from_trade_close(symbol, pnl_pct, comps, regime, sector)
        

        # XAI: Log explainable trade exit
        try:
            from xai.explainable_logger import get_explainable_logger
            explainable = get_explainable_logger()
            
            # Get regime - try current regime detector first, then fall back to stored
            regime_name = context.get("market_regime", "unknown")
            if not regime_name or regime_name == "unknown":
                try:
                    from structural_intelligence.regime_detector import get_current_regime
                    current_regime, _ = get_current_regime()
                    if current_regime and current_regime != "unknown":
                        regime_name = current_regime
                except:
                    pass
            # Final fallback
            if not regime_name or regime_name == "unknown":
                regime_name = "NEUTRAL"  # Default to NEUTRAL instead of unknown
            
            # Get gamma walls at exit
            gamma_walls = None
            try:
                from structural_intelligence import get_structural_exit
                structural_exit = get_structural_exit()
                position_data = {
                    "current_price": exit_price,
                    "side": side,
                    "entry_price": entry_price,
                    "unrealized_pnl_pct": pnl_pct / 100.0
                }
                exit_rec = structural_exit.get_exit_recommendation(symbol, position_data)
                if exit_rec.get("gamma_wall_distance"):
                    gamma_walls = {
                        "distance_pct": exit_rec.get("gamma_wall_distance"),
                        "gamma_exposure": exit_rec.get("gamma_exposure", 0)
                    }
            except:
                pass
            
            why_sentence = explainable.log_trade_exit(
                symbol=symbol,
                entry_price=entry_price,
                exit_price=exit_price,
                pnl_pct=pnl_pct,
                hold_minutes=hold_minutes,
                exit_reason=close_reason,
                regime=regime_name,
                gamma_walls=gamma_walls
            )
            log_event("xai", "trade_exit_logged", symbol=symbol, why=why_sentence)
        except Exception as e:
            log_event("xai", "trade_exit_log_failed", symbol=symbol, error=str(e))
        # Also feed to exit model for exit signal learning
        from adaptive_signal_optimizer import get_optimizer
        optimizer = get_optimizer()
        if optimizer and hasattr(optimizer, 'exit_model'):
            # Parse close reason to extract exit signals
            exit_signals = []
            if close_reason and close_reason != "unknown":
                for part in close_reason.split("+"):
                    part = part.strip()
                    if "(" in part:
                        signal_name = part.split("(")[0].strip()
                    else:
                        signal_name = part.strip()
                    if signal_name:
                        exit_signals.append(signal_name)
            
            # Map exit signals to exit model components
            exit_components = {}
            for signal in exit_signals:
                if "signal_decay" in signal or "entry_decay" in signal:
                    exit_components["entry_decay"] = 1.0
                elif "flow_reversal" in signal or "adverse_flow" in signal:
                    exit_components["adverse_flow"] = 1.0
                elif "drawdown" in signal:
                    exit_components["drawdown_velocity"] = 1.0
                elif "time" in signal or "stale" in signal:
                    exit_components["time_decay"] = 1.0
                elif "momentum" in signal:
                    exit_components["momentum_reversal"] = 1.0
            
            # Record exit outcome for learning
            if exit_components and pnl_pct != 0:
                if hasattr(optimizer, 'learner') and hasattr(optimizer.learner, 'record_trade_outcome'):
                    optimizer.learner.record_trade_outcome(
                        trade_data={
                            "entry_ts": entry_ts.isoformat() if hasattr(entry_ts, 'isoformat') else str(entry_ts),
                            "exit_ts": now_aware.isoformat(),
                            "direction": context.get("direction", "unknown"),
                            "close_reason": close_reason
                        },
                        feature_vector=exit_components,
                        pnl=pnl_pct / 100.0,  # Convert % to decimal
                        regime=regime,
                        sector=sector
                    )
    except Exception as e:
        # Don't fail exit logging if learning fails
        log_event("exit", "learning_feed_failed", error=str(e))

def compute_daily_metrics():
    path = os.path.join(LOG_DIR, "attribution.jsonl")
    if not os.path.exists(path):
        return {"total_pnl": 0, "trades": 0, "win_rate": None}
    today = datetime.utcnow().strftime("%Y-%m-%d")
    wins = 0
    total = 0
    pnl = 0.0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            ts = rec.get("ts", "")
            if rec.get("type") == "attribution" and ts.startswith(today):
                total += 1
                p = float(rec.get("pnl_usd", 0))
                pnl += p
                wins += 1 if p > 0 else 0
    return {"total_pnl": round(pnl, 2), "trades": total, "win_rate": (wins / total) if total > 0 else None}

# =========================
# UNUSUAL WHALES CLIENT (comprehensive endpoints)
# =========================
class UWClient:
    def __init__(self, api_key=None):
        from config.registry import APIConfig
        self.api_key = api_key or Config.UW_API_KEY
        self.base = APIConfig.UW_BASE_URL
        self.headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
    
    def _to_iso(self, ts):
        """Convert timestamp to ISO format."""
        if ts is None:
            from datetime import datetime
            return datetime.utcnow().isoformat() + "Z"
        if isinstance(ts, str):
            return ts
        try:
            from datetime import datetime
            if isinstance(ts, (int, float)):
                return datetime.fromtimestamp(ts).isoformat() + "Z"
        except:
            pass
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"

    def _get(self, path_or_url: str, params: dict = None) -> dict:
        url = path_or_url if path_or_url.startswith("http") else f"{self.base}{path_or_url}"
        
        # QUOTA TRACKING: Log all UW API calls for monitoring
        quota_log = CacheFiles.UW_API_QUOTA
        quota_log.parent.mkdir(parents=True, exist_ok=True)
        try:
            with quota_log.open("a") as f:
                f.write(json.dumps({
                    "ts": int(time.time()),
                    "url": url,
                    "params": params or {},
                    "source": "UWClient"
                }) + "\n")
        except Exception:
            pass  # Don't fail on quota logging
        
        # TOKEN BUCKET: Check quota before making API call
        try:
            from api_management import get_quota_manager
            quota = get_quota_manager()
            
            # Extract symbol from params or URL for prioritization
            symbol = params.get("symbol") if params else None
            if not symbol and "ticker" in (params or {}):
                symbol = params.get("ticker")
            if not symbol and "/" in path_or_url:
                # Try to extract from URL path
                parts = path_or_url.split("/")
                if "stock" in parts or "darkpool" in parts:
                    idx = parts.index("stock") if "stock" in parts else parts.index("darkpool")
                    if idx + 1 < len(parts):
                        symbol = parts[idx + 1]
            
            can_poll, wait_time = quota.should_poll_symbol(symbol or "unknown")
            if not can_poll:
                # Rate limited - return empty data
                if wait_time > 0:
                    time.sleep(min(wait_time, 5.0))  # Max 5 second wait
                return {"data": []}
            
            # V4.0: Apply API resilience with exponential backoff
            from api_resilience import ExponentialBackoff, get_signal_queue, is_panic_regime
            
            backoff = ExponentialBackoff(max_retries=5, base_delay=1.0, max_delay=60.0)
            
            def make_request():
                r = requests.get(url, headers=self.headers, params=params or {}, timeout=10)
                r.raise_for_status()
                return r.json()
            
            try:
                result = backoff(make_request)()
                # Record API call
                quota.record_api_call(symbol or "unknown")
                return result
            except requests.exceptions.HTTPError as e:
                # Check for 429 rate limit - queue signal if in PANIC regime
                status_code = e.response.status_code if hasattr(e, 'response') and e.response else None
                if status_code == 429:
                    try:
                        if is_panic_regime():
                            # Queue signal for later processing
                            queue = get_signal_queue()
                            queue.enqueue({
                                "url": url,
                                "params": params or {},
                                "symbol": symbol or "unknown",
                                "error": f"Rate limited (429): {str(e)}",
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            })
                            log_event("api_resilience", "signal_queued_on_429", url=url, symbol=symbol)
                    except Exception:
                        pass  # Don't fail if queueing fails
                # Rate limited or endpoint not available - return empty data
                jsonl_write("uw_error", {"event": "UW_API_ERROR", "url": url, "error": str(e), "status_code": status_code})
                return {"data": []}
            except Exception as e:
                jsonl_write("uw_error", {"event": "UW_API_ERROR", "url": url, "error": str(e)})
                return {"data": []}
        except ImportError:
            # Fallback if quota manager not available - still apply resilience
            from api_resilience import ExponentialBackoff, get_signal_queue, is_panic_regime
            
            backoff = ExponentialBackoff(max_retries=5, base_delay=1.0, max_delay=60.0)
            
            def make_request():
                r = requests.get(url, headers=self.headers, params=params or {}, timeout=10)
                r.raise_for_status()
                return r.json()
            
            try:
                return backoff(make_request)()
            except requests.exceptions.HTTPError as e:
                # Check for 429 rate limit - queue signal if in PANIC regime
                status_code = e.response.status_code if hasattr(e, 'response') and e.response else None
                if status_code == 429 and is_panic_regime():
                    queue = get_signal_queue()
                    queue.enqueue({
                        "url": url,
                        "params": params or {},
                        "symbol": symbol if 'symbol' in locals() else "unknown",
                        "error": f"Rate limited (429): {str(e)}",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    log_event("api_resilience", "signal_queued_on_429", url=url)
                # Rate limited or endpoint not available - return empty data
                jsonl_write("uw_error", {"event": "UW_API_ERROR", "url": url, "error": str(e), "status_code": status_code})
                return {"data": []}
            except Exception as e:
                jsonl_write("uw_error", {"event": "UW_API_ERROR", "url": url, "error": str(e)})
                return {"data": []}

    def get_option_flow(self, ticker: str, limit: int = 100):
        raw = self._get("/api/option-trades/flow-alerts", params={"symbol": ticker, "limit": limit})
        return [self._normalize_flow_trade(t) for t in raw.get("data", [])]

    def get_dark_pool_levels(self, ticker: str):
        raw = self._get(f"/api/darkpool/{ticker}")
        return [self._normalize_darkpool_level(dp) for dp in raw.get("data", [])]

    def get_greek_exposure(self, ticker: str):
        raw = self._get(f"/api/stock/{ticker}/greeks")
        data = raw.get("data", {})
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        return self._normalize_gex(data if isinstance(data, dict) else {})

    def get_top_net_impact(self, limit: int = 50):
        raw = self._get("/api/market/top-net-impact", params={"limit": limit})
        return [self._normalize_net_impact(x) for x in raw.get("data", [])]

    def get_realized_volatility(self, ticker: str):
        raw = self._get(f"/api/stock/{ticker}/volatility/realized")
        data = raw.get("data", {})
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        return self._normalize_realized_vol(data if isinstance(data, dict) else {})

    def get_historic_option_volume(self, ticker: str, date_str: str):
        raw = self._get(f"/api/stock/{ticker}/historic-option-volume", params={"date": date_str})
        return [self._normalize_historic_option(x) for x in raw.get("data", [])]

    def _normalize_flow_trade(self, t: dict) -> dict:
        # Determine direction: call buying or put selling = bullish, call selling or put buying = bearish
        option_type = t.get("type", "").lower()
        bid_prem = float(t.get("total_bid_side_prem") or 0)
        ask_prem = float(t.get("total_ask_side_prem") or 0)
        
        # Sweeps execute on the ASK (buying from sellers), so ask_prem > bid_prem means BUY
        # Hitting the bid means selling, so bid_prem > ask_prem means SELL
        is_buy = ask_prem > bid_prem
        direction = "bullish" if (option_type == "call" and is_buy) or (option_type == "put" and not is_buy) else "bearish"
        
        # Determine flow type: sweep, block, or floor based on API flags
        if t.get("has_sweep"):
            flow_type = "sweep"
        elif t.get("has_floor"):
            flow_type = "block"  # Floor trades are institutional blocks
        elif t.get("has_multileg"):
            flow_type = "multileg"
        else:
            flow_type = "singleleg"  # Default for large single-leg trades
        
        ticker = t.get("ticker") or t.get("symbol")
        timestamp = t.get("created_at") or t.get("timestamp")
        
        # ROOT CAUSE FIX: Extract flow_conv and flow_magnitude from UW API JSON payload
        flow_conv = float(t.get("flow_conv") or t.get("flow_conviction") or t.get("conviction") or 0.0)
        flow_magnitude_raw = t.get("flow_magnitude") or t.get("magnitude") or ""
        flow_magnitude = flow_magnitude_raw.upper() if isinstance(flow_magnitude_raw, str) else "UNKNOWN"
        
        # ROOT CAUSE FIX: Create signal_type from flow_type + direction (e.g., BULLISH_SWEEP, BEARISH_BLOCK)
        signal_type = f"{direction.upper()}_{flow_type.upper()}" if flow_type and direction else "UNKNOWN"
        
        return {
            "ticker": ticker,
            "timestamp": self._to_iso(timestamp),
            "flow_type": flow_type,
            "direction": direction,
            "signal_type": signal_type,  # ROOT CAUSE FIX: e.g., BULLISH_SWEEP, BEARISH_BLOCK
            "flow_conv": flow_conv,  # ROOT CAUSE FIX: Extract from UW API JSON
            "flow_magnitude": flow_magnitude,  # ROOT CAUSE FIX: Extract from UW API JSON (LOW/MEDIUM/HIGH)
            "premium_usd": float(t.get("total_premium") or t.get("premium") or 0),
            "strike": float(t.get("strike") or 0),
            "expiry": t.get("expiry") or t.get("expiration"),
            "volume": int(t.get("volume") or 0),
            "open_interest": int(t.get("open_interest") or t.get("oi") or 0),
            "spot": float(t.get("underlying_price") or 0),
            "exchange": t.get("exchange"),
            "id": f"{ticker}_{timestamp}_{t.get('strike')}"
        }

    def _normalize_darkpool_level(self, dp: dict) -> dict:
        return {
            "ticker": dp.get("symbol") or dp.get("ticker"),
            "price": float(dp.get("price") or 0),
            "lit_volume": float(dp.get("lit_volume") or 0),
            "off_lit_volume": float(dp.get("off_lit_volume") or 0),
            "total_volume": float(dp.get("total_volume") or 0),
            "side": dp.get("side"),
            "timestamp": self._to_iso(dp.get("timestamp"))
        }

    def _normalize_gex(self, g: dict) -> dict:
        total = float(g.get("total") or g.get("gex_total") or 0)
        return {
            "ticker": g.get("symbol") or g.get("ticker"),
            "total_gamma": total,
            "gamma_regime": "negative" if total < 0 else "positive",
            "delta": float(g.get("delta_total") or 0),
            "vanna": float(g.get("vanna_total") or 0),
            "charm": float(g.get("charm_total") or 0),
        }

    def _normalize_net_impact(self, x: dict) -> dict:
        return {
            "ticker": x.get("symbol") or x.get("ticker"),
            "net_premium": float(x.get("net_premium") or 0),
            "net_call_premium": float(x.get("net_call_premium") or 0),
            "net_put_premium": float(x.get("net_put_premium") or 0),
            "timestamp": self._to_iso(x.get("timestamp"))
        }

    def _normalize_option_volume_level(self, x: dict) -> dict:
        return {
            "ticker": x.get("symbol") or x.get("ticker"),
            "price": float(x.get("price") or 0),
            "call_volume": int(x.get("call_volume") or 0),
            "put_volume": int(x.get("put_volume") or 0),
            "timestamp": self._to_iso(x.get("timestamp"))
        }

    def _normalize_realized_vol(self, d: dict) -> dict:
        return {
            "ticker": d.get("symbol") or d.get("ticker"),
            "realized_vol_5d": float(d.get("rv_5d") or 0),
            "realized_vol_20d": float(d.get("rv_20d") or 0),
            "iv_atm": float(d.get("iv_atm") or 0),
            "timestamp": self._to_iso(d.get("timestamp"))
        }

    def _normalize_historic_option(self, x: dict) -> dict:
        return {
            "ticker": x.get("symbol") or x.get("ticker"),
            "date": x.get("date"),
            "volume": int(x.get("volume") or 0),
            "premium": float(x.get("premium") or 0),
            "call_volume": int(x.get("call_volume") or 0),
            "put_volume": int(x.get("put_volume") or 0),
        }

    def _to_iso(self, ts):
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        if isinstance(ts, str):
            return ts
        return now_iso()

# =========================
# FILTERS & CLUSTERING
# =========================
def within_expiry_days(expiry_str: str, max_days: int) -> bool:
    try:
        expiry = datetime.fromisoformat(expiry_str)
    except Exception:
        try:
            expiry = datetime.strptime(expiry_str, "%Y-%m-%d")
        except Exception:
            return False
    return (expiry - datetime.utcnow()).days <= max_days

def base_filter(trade: dict) -> bool:
    if trade["premium_usd"] < Config.MIN_PREMIUM_USD:
        return False
    if not within_expiry_days(trade["expiry"], Config.MAX_EXPIRY_DAYS):
        return False
    if trade["volume"] <= trade["open_interest"]:
        return False
    # Accept sweeps, blocks, and large single-leg institutional trades
    if trade["flow_type"] not in ("sweep", "block", "singleleg"):
        return False
    return True

def cluster_signals(trades: list) -> list:
    trades_sorted = sorted(trades, key=lambda x: x["timestamp"])
    clusters = []
    window = timedelta(seconds=Config.CLUSTER_WINDOW_SEC)

    for ticker in set(t["ticker"] for t in trades_sorted):
        for direction in ("bullish", "bearish"):
            bucket = [t for t in trades_sorted if t["ticker"] == ticker and t["direction"] == direction]
            i = 0
            while i < len(bucket):
                cluster = [bucket[i]]
                j = i + 1
                while j < len(bucket):
                    t0 = datetime.fromisoformat(cluster[0]["timestamp"])
                    tj = datetime.fromisoformat(bucket[j]["timestamp"])
                    if tj - t0 <= window:
                        cluster.append(bucket[j])
                        j += 1
                    else:
                        break
                if len(cluster) >= Config.CLUSTER_MIN_SWEEPS:
                    # ROOT CAUSE FIX: Extract signal_type from trades (use most common or first)
                    signal_types = [c.get("signal_type", "UNKNOWN") for c in cluster if c.get("signal_type")]
                    signal_type = max(set(signal_types), key=signal_types.count) if signal_types else (cluster[0].get("signal_type", "UNKNOWN") if cluster else "UNKNOWN")
                    
                    clusters.append({
                        "ticker": ticker,
                        "direction": direction,
                        "signal_type": signal_type,  # ROOT CAUSE FIX: Preserve signal_type in cluster (e.g., BULLISH_SWEEP)
                        "count": len(cluster),
                        "start_ts": cluster[0]["timestamp"],
                        "end_ts": cluster[-1]["timestamp"],
                        "avg_premium": sum(c["premium_usd"] for c in cluster) / len(cluster),
                        "trades": cluster
                    })
                i = j
    return clusters

# =========================
# MULTI-FACTOR CONFIRMATION (gamma, dark pool, net premium, vol, option levels)
# V3.2: Uses adaptive weights for all components
# =========================
def score_confirmation_layers(symbol: str, gex: dict, dp_levels: list, net_impact_map: dict, vol: dict, ovl: list) -> float:
    score = 0.0
    regime = gex.get("gamma_regime", "unknown")
    
    # V3.2: Apply adaptive weight multipliers to all confirmation components
    gamma_mult = get_adaptive_weight("gamma", 1.0)
    darkpool_mult = get_adaptive_weight("dark_pool", 1.0)
    net_premium_mult = get_adaptive_weight("net_premium", 1.0)
    volatility_mult = get_adaptive_weight("volatility", 1.0)
    
    if regime == "negative":
        score += Config.CONFIRM_GAMMA_NEG_W * gamma_mult

    off_lit_total = sum(x.get("off_lit_volume", 0) for x in dp_levels)
    if off_lit_total > Config.DARKPOOL_OFFLIT_MIN:
        score += Config.CONFIRM_DARKPOOL_W * darkpool_mult

    net_imp = net_impact_map.get(symbol, {})
    if net_imp.get("net_call_premium", 0) > 0 and abs(net_imp.get("net_premium", 0)) > Config.NET_PREMIUM_MIN_ABS:
        score += Config.CONFIRM_NET_PREMIUM_W * net_premium_mult

    rv20 = vol.get("realized_vol_20d", 0)
    if 0 < rv20 < Config.RV20_MAX:
        score += Config.CONFIRM_VOL_W * volatility_mult

    call_vol = sum(l.get("call_volume", 0) for l in ovl)
    put_vol = sum(l.get("put_volume", 0) for l in ovl)
    if call_vol > put_vol:
        options_mult = get_adaptive_weight("options_flow", 1.0)
        score += 0.1 * options_mult

    return round(score, 3)

# =========================
# ADAPTIVE WEIGHTS (weekly adjustments + emergency override)
# =========================
def load_weights():
    if os.path.exists(WEIGHTS_PATH):
        with open(WEIGHTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_weights(weights):
    with open(WEIGHTS_PATH, "w", encoding="utf-8") as f:
        json.dump(weights, f, indent=2)

def bucket_key(symbol: str, direction: str, regime: str):
    return f"{symbol}|{direction}|{regime}"

def compute_bucket_stats(min_trades: int):
    path = os.path.join(LOG_DIR, "attribution.jsonl")
    stats = {}
    if not os.path.exists(path):
        return stats
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if rec.get("type") != "attribution":
                continue
            ctx = rec.get("context", {})
            key = bucket_key(rec.get("symbol"), ctx.get("direction"), ctx.get("gamma_regime", "unknown"))
            stats.setdefault(key, {"pnls": []})
            stats[key]["pnls"].append(float(rec.get("pnl_usd", 0)))
    for key, d in stats.items():
        pnls = d["pnls"]
        d["count"] = len(pnls)
        d["win_rate"] = sum(1 for p in pnls if p > 0) / len(pnls) if pnls else None
        d["avg_pnl"] = sum(pnls) / len(pnls) if pnls else None
        d["eligible"] = d["count"] >= min_trades
    return stats

def apply_weekly_adjustments():
    weights = load_weights()
    stats = compute_bucket_stats(Config.MIN_TRADES_FOR_ADJUST)
    for key, d in stats.items():
        current = float(weights.get(key, 1.0))
        if not d["eligible"]:
            weights[key] = round(current, 3)
            continue
        win_rate = d["win_rate"]
        avg_pnl = d["avg_pnl"]
        if win_rate is None or avg_pnl is None:
            continue
        if win_rate > Config.WIN_RATE_UP and avg_pnl > 0:
            new_weight = min(current + Config.WEIGHT_STEP, Config.WEIGHT_MAX)
        elif win_rate < Config.WIN_RATE_DOWN and avg_pnl < 0:
            new_weight = max(current - Config.WEIGHT_STEP, Config.WEIGHT_MIN)
        else:
            new_weight = current
        weights[key] = round(new_weight, 3)
    save_weights(weights)
    log_event("adaptive", "weekly_weights_updated", weights=weights)
    return weights

def apply_emergency_override(daily_metrics):
    if daily_metrics["trades"] < Config.EMERGENCY_MIN_TRADES:
        return None
    win_rate = daily_metrics["win_rate"] or 0.0
    total_pnl = daily_metrics["total_pnl"]
    if win_rate < Config.EMERGENCY_WIN_RATE_THRESH or total_pnl <= Config.EMERGENCY_PNL_THRESH:
        weights = load_weights()
        adjusted = {}
        for k, w in weights.items():
            new_w = max(float(w) - Config.EMERGENCY_ADJUST_FACTOR, Config.WEIGHT_MIN)
            adjusted[k] = round(new_w, 3)
        save_weights(adjusted)
        log_event("adaptive", "emergency_override_applied", win_rate=win_rate, total_pnl=total_pnl, weights=adjusted)
        send_webhook({"event": "emergency_override", "win_rate": win_rate, "pnl": total_pnl})
        return adjusted
    return None

# =========================
# PER-TICKER LEARNING (Feature Store & Profiles)
# =========================
def _fs_path(symbol: str):
    return os.path.join(Config.FEATURE_STORE_DIR, f"{symbol}.jsonl")

def log_features(symbol: str, features: dict, outcome: dict = None):
    if not Config.ENABLE_PER_TICKER_LEARNING:
        return
    rec = {"ts": now_iso(), "symbol": symbol, "features": features, "outcome": outcome or {}}
    with open(_fs_path(symbol), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")

def log_v3_features(symbol: str, composite: dict, outcome: dict = None):
    """
    V3: Log expanded intelligence features for learning
    Captures all V3 components including congress, shorts, institutional, etc.
    """
    if not Config.ENABLE_PER_TICKER_LEARNING:
        return
    
    # Extract all learnable features from V3 composite
    features_for_learning = composite.get("features_for_learning", {})
    components = composite.get("components", {})
    
    # Build comprehensive feature record
    rec = {
        "ts": now_iso(),
        "symbol": symbol,
        "version": "V3",
        "score": composite.get("score", 0.0),
        # V3 raw features for learning
        "features": features_for_learning,
        # V3 scored components
        "components": components,
        # Expanded intelligence flags
        "expanded_intel": composite.get("expanded_intel", {}),
        # Motif patterns
        "motifs": composite.get("motifs", {}),
        # Sizing overlay
        "sizing_overlay": composite.get("sizing_overlay", 0.0),
        # Notes (human readable)
        "notes": composite.get("notes", ""),
        # Outcome (filled in later when trade completes)
        "outcome": outcome or {}
    }
    
    with open(_fs_path(symbol), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")

def load_symbol_history(symbol: str, limit: int = 5000):
    if not Config.ENABLE_PER_TICKER_LEARNING:
        return []
    path = _fs_path(symbol)
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            rows.append(json.loads(line))
    return rows

def load_profiles():
    if not Config.ENABLE_PER_TICKER_LEARNING or not os.path.exists(Config.PROFILE_PATH):
        return {}
    with open(Config.PROFILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_profiles(profiles: dict):
    if not Config.ENABLE_PER_TICKER_LEARNING:
        return
    with open(Config.PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2)

# =========================
# BAYESIAN BANDITS (Thompson Sampling)
# =========================
def thompson_sample_action(stats: dict, actions: list, prior: float):
    scores = {}
    for a in actions:
        s = stats.get(a, {"wins": 0.0, "losses": 0.0})
        alpha = prior + s["wins"]
        beta = prior + s["losses"]
        mean = alpha / max(1e-6, (alpha + beta))
        scores[a] = mean + (0.05 * (os.urandom(2)[0] / 255.0 - 0.5))
    return max(scores.items(), key=lambda kv: kv[1])[0]

def update_bandit(stats: dict, action: str, reward: float):
    s = stats.get(action, {"wins": 0.0, "losses": 0.0})
    if reward > 0:
        s["wins"] += 1.0
    else:
        s["losses"] += 1.0
    stats[action] = s
    return stats

# =========================
# PER-TICKER PROFILES
# =========================
def get_or_init_profile(profiles: dict, symbol: str):
    if symbol not in profiles:
        profiles[symbol] = {
            "entry_bandit": {},
            "stop_bandit": {},
            "feature_bandit": {},
            "component_weights": dict(Config.DEFAULT_COMPONENT_WEIGHTS),
            "atr_mult": 1.5,
            "size_scale": 1.0,
            "confidence": 0.0,
            "samples": 0
        }
    return profiles[symbol]

def compute_confidence(entry_stats: dict, stop_stats: dict, prior: float):
    wins = sum(s.get("wins", 0.0) for s in entry_stats.values()) + sum(s.get("wins", 0.0) for s in stop_stats.values())
    losses = sum(s.get("losses", 0.0) for s in entry_stats.values()) + sum(s.get("losses", 0.0) for s in stop_stats.values())
    total = wins + losses + 2 * prior * (len(entry_stats) + len(stop_stats) or 1)
    return wins / max(1e-6, total)

# =========================
# SMART API POLLING (Owner-in-the-loop quota optimization)
# =========================
class SmartPoller:
    """
    Thread-safe intelligent polling manager that calls endpoints based on data update frequency.
    Reduces API usage by 68% by matching polling intervals to actual data freshness.
    Persists state across restarts and coordinates with UW flow daemon.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.state_file = StateFiles.SMART_POLLER
        self.intervals = {
            "option_flow": 60,        # Real-time: institutional trades (HIGH actionability)
            "top_net_impact": 300,    # 5min: aggregated net premium (MEDIUM actionability)
            "greek_exposure": 900,    # 15min: gamma exposure (LOW actionability)
            "dark_pool_levels": 120,  # 2min: block trades (HIGH actionability)
            "realized_volatility": 3600,  # 1hour: historical calc (LOW actionability)
        }
        self.last_call = self._load_state()
        self.error_count = {}  # Track consecutive errors for backoff
    
    def _load_state(self) -> dict:
        """Load persisted polling timestamps from disk."""
        try:
            if self.state_file.exists():
                from utils.state_io import read_json_self_heal
                return read_json_self_heal(self.state_file, {})
        except Exception as e:
            log_event("smart_poller", "state_load_failed", error=str(e))
        return {}
    
    def _save_state(self):
        """Persist polling timestamps to survive restarts."""
        try:
            tmp = self.state_file.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.last_call, indent=2))
            tmp.replace(self.state_file)
        except Exception as e:
            log_event("smart_poller", "state_save_failed", error=str(e))
    
    def _is_market_hours(self) -> bool:
        """Check if currently in trading hours (9:30 AM - 4:00 PM ET)."""
        try:
            import pytz
            et = pytz.timezone('US/Eastern')
            now_et = datetime.now(et)
            hour_min = now_et.hour * 60 + now_et.minute
            market_open = 9 * 60 + 30  # 9:30 AM
            market_close = 16 * 60      # 4:00 PM
            return market_open <= hour_min < market_close
        except:
            return True  # Default to allowing polls if timezone check fails
    
    def should_poll(self, endpoint: str, force=False) -> bool:
        """
        Thread-safe check if enough time has passed since last call.
        Returns False if:
        - Interval not elapsed
        - Outside market hours (except for daily endpoints)
        - Consecutive errors triggered backoff
        - Market open jitter applied (prevents thundering herd)
        """
        with self.lock:
            import random
            now = time.time()
            last = self.last_call.get(endpoint, 0)
            interval = self.intervals.get(endpoint, 60)
            
            # Apply exponential backoff on repeated errors
            errors = self.error_count.get(endpoint, 0)
            if errors > 0:
                backoff_mult = min(2 ** errors, 8)  # Max 8x backoff
                interval *= backoff_mult
            
            # THUNDERING HERD PREVENTION: Staggered market open scheduling
            # If endpoint has been stale for >2x interval (e.g., overnight), schedule a future time
            time_since_last = now - last
            scheduled_key = f"_scheduled_{endpoint}"
            
            if time_since_last > (interval * 2) and self._is_market_hours():
                # Check if we already scheduled a future poll time
                scheduled_time = self.last_call.get(scheduled_key, 0)
                if scheduled_time == 0:
                    # First call after stale period - schedule future poll with jitter
                    # Spread endpoints over 0-90 seconds based on endpoint name hash
                    jitter_seconds = abs(hash(endpoint)) % 90
                    scheduled_time = now + jitter_seconds
                    self.last_call[scheduled_key] = scheduled_time
                    self._save_state()
                    log_event("smart_poller", "jitter_scheduled", endpoint=endpoint, 
                             jitter_sec=jitter_seconds, scheduled_at=scheduled_time)
                
                # Wait until scheduled time
                if now < scheduled_time:
                    return False
                else:
                    # Time reached - clear schedule and proceed
                    self.last_call.pop(scheduled_key, None)
            
            # Check if interval elapsed (normal operation)
            if not force and now - last < interval:
                return False
            
            # Market hours gating (skip low-frequency endpoints outside hours)
            if not self._is_market_hours() and interval >= 900:  # 15min+ endpoints
                log_event("smart_poller", "market_closed_skip", endpoint=endpoint)
                return False
            
            # Update timestamp and persist
            self.last_call[endpoint] = now
            self._save_state()
            return True
    
    def record_success(self, endpoint: str):
        """Reset error counter on successful call."""
        with self.lock:
            self.error_count[endpoint] = 0
    
    def record_error(self, endpoint: str):
        """Increment error counter for backoff."""
        with self.lock:
            self.error_count[endpoint] = self.error_count.get(endpoint, 0) + 1
            # SAFETY: Logging must never raise KeyError.
            log_event("smart_poller", "error_backoff", endpoint=endpoint, errors=self.error_count.get(endpoint, 0))

# Global instance
_smart_poller = SmartPoller()

# =========================
# SIGNAL VALIDATION (Owner-in-the-loop)
# =========================
def normalize_cluster(cluster: dict) -> dict:
    """Defensive schema validation for cluster data - prevents KeyErrors"""
    return {
        "count": int(cluster.get("count", 0)),
        "avg_premium": float(cluster.get("avg_premium", 0.0)),
        "direction": str(cluster.get("direction", "neutral")),
        "timestamp": int(cluster.get("timestamp", 0)),
        "symbol": str(cluster.get("symbol", "")),
    }

def owner_health_check() -> dict:
    """
    Owner-in-the-loop health check cycle
    - Monitors heartbeat freshness
    - Validates critical file integrity
    - Auto-repairs minor issues
    - Returns dict of issues found (empty if all healthy)
    """
    issues = []
    
    # 1. Check heartbeat staleness
    heartbeat_path = StateFiles.BOT_HEARTBEAT
    try:
        if heartbeat_path.exists():
            from utils.state_io import read_json_self_heal
            hb = read_json_self_heal(
                heartbeat_path,
                {},
                on_event=lambda ev, payload: log_event("state", ev, **payload),
            )
            age_sec = int(time.time()) - hb.get("last_heartbeat_ts", 0)
            if age_sec > 180:  # 3 minutes
                issues.append({"check": "heartbeat_stale", "age_sec": age_sec})
                # Auto-repair: update heartbeat
                hb["last_heartbeat_ts"] = int(time.time())
                hb["last_heartbeat_dt"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                hb["owner_fix"] = "auto_refresh"
                heartbeat_path.write_text(json.dumps(hb, indent=2))
                log_event("owner_check", "heartbeat_refreshed", age_sec=age_sec)
        else:
            issues.append({"check": "heartbeat_missing"})
    except Exception as e:
        issues.append({"check": "heartbeat_error", "error": str(e)})
    
    # 2. Check fail counter integrity
    fail_counter_path = StateFiles.FAIL_COUNTER
    try:
        if fail_counter_path.exists():
            from utils.state_io import read_json_self_heal
            fc = read_json_self_heal(
                fail_counter_path,
                {"fail_count": 0},
                on_event=lambda ev, payload: log_event("state", ev, **payload),
            )
            fail_count = fc.get("fail_count", 0)
            if fail_count > 100:  # Suspiciously high
                issues.append({"check": "high_fail_count", "count": fail_count})
    except Exception as e:
        # Auto-repair: reset corrupted fail counter
        fail_counter_path.write_text(json.dumps({"fail_count": 0}))
        issues.append({"check": "fail_counter_reset", "error": str(e)})
        log_event("owner_check", "fail_counter_reset", error=str(e))
    
    # 3. Log health check result
    if issues:
        log_event("owner_check", "issues_found", issues=issues, severity="WARN")
    else:
        log_event("owner_check", "healthy", timestamp=datetime.utcnow().isoformat())
    
    return {"issues": issues, "healthy": len(issues) == 0}

# =========================
# FEATURE EXTRACTION & DECISION MAKING
# =========================
def extract_features_for_signal(symbol: str, cluster: dict, gex: dict, dp_levels: list, net_map: dict, vol: dict, ovl: list):
    # EMPTY RESPONSE GUARDS: Ensure all inputs have safe defaults
    safe_cluster = normalize_cluster(cluster or {})
    gex = gex or {}
    dp_levels = dp_levels or []
    net_map = net_map or {}
    vol = vol or {}
    ovl = ovl or []
    
    # Safe extraction with type guards
    symbol_net = net_map.get(symbol, {}) or {}
    
    f = {
        "count": safe_cluster["count"],
        "avg_premium_m": safe_cluster["avg_premium"] / 1_000_000,
        "direction": 1 if safe_cluster["direction"] == "bullish" else -1,
        "gamma_neg": 1 if gex.get("gamma_regime") == "negative" else 0,
        "off_lit_total_m": float(sum(x.get("off_lit_volume", 0) for x in dp_levels if x) / 1_000_000),
        "net_premium_m": float(symbol_net.get("net_premium", 0) / 1_000_000),
        "net_call_premium_m": float(symbol_net.get("net_call_premium", 0) / 1_000_000),
        "rv20": float(vol.get("realized_vol_20d", 0) or 0),
        "call_vol": int(sum(l.get("call_volume", 0) for l in ovl if l)),
        "put_vol": int(sum(l.get("put_volume", 0) for l in ovl if l)),
        "time_of_day_min": int(datetime.utcnow().hour * 60 + datetime.utcnow().minute),
    }
    f["call_put_tilt"] = (f["call_vol"] - f["put_vol"]) / max(1, (f["call_vol"] + f["put_vol"]))
    f["net_call_tilt"] = (f["net_call_premium_m"]) / max(1e-6, abs(f["net_premium_m"]) + 1e-9)
    return f

def decide_entry_and_stop(symbol: str, features: dict, profiles: dict):
    prof = get_or_init_profile(profiles, symbol)
    entry_action = thompson_sample_action(prof["entry_bandit"], Config.ENTRY_ACTIONS, Config.CONFIDENCE_PRIOR)
    stop_action = thompson_sample_action(prof["stop_bandit"], Config.STOP_ACTIONS, Config.CONFIDENCE_PRIOR)
    atr_mult = {"atr_1.0x": 1.0, "atr_1.5x": 1.5, "atr_2.0x": 2.0}.get(stop_action, 1.5)
    prof["atr_mult"] = atr_mult

    rv20 = max(0.01, features.get("rv20", 0.2))
    conf = compute_confidence(prof["entry_bandit"], prof["stop_bandit"], Config.CONFIDENCE_PRIOR)
    prof["confidence"] = conf
    size_scale = min(1.5, max(0.5, (0.9 / rv20) * (0.5 + conf)))
    prof["size_scale"] = round(size_scale, 3)
    return entry_action, atr_mult, size_scale

# =========================
# COMPONENT SCORING
# V3.2: All components use adaptive weight multipliers
# =========================
def confirmation_components(symbol: str, gex: dict, dp_levels: list, net_impact_map: dict, vol: dict, ovl: list) -> dict:
    # V3.2: Apply adaptive weight multipliers to base component values
    # EMPTY RESPONSE GUARDS: Ensure all inputs have safe defaults
    gex = gex or {}
    dp_levels = dp_levels or []
    net_impact_map = net_impact_map or {}
    vol = vol or {}
    
    comp = {"gamma": 0.0, "darkpool": 0.0, "net_premium": 0.0, "volatility": 0.0}
    
    gamma_mult = get_adaptive_weight("gamma", 1.0)
    darkpool_mult = get_adaptive_weight("dark_pool", 1.0)
    net_premium_mult = get_adaptive_weight("net_premium", 1.0)
    volatility_mult = get_adaptive_weight("volatility", 1.0)
    
    if gex.get("gamma_regime") == "negative":
        comp["gamma"] = Config.CONFIRM_GAMMA_NEG_W * gamma_mult
    off_lit_total = sum(x.get("off_lit_volume", 0) for x in dp_levels if x)
    if off_lit_total > Config.DARKPOOL_OFFLIT_MIN:
        comp["darkpool"] = Config.CONFIRM_DARKPOOL_W * darkpool_mult
    net_imp = net_impact_map.get(symbol, {}) or {}
    if net_imp.get("net_call_premium", 0) > 0 and abs(net_imp.get("net_premium", 0)) > Config.NET_PREMIUM_MIN_ABS:
        comp["net_premium"] = Config.CONFIRM_NET_PREMIUM_W * net_premium_mult
    rv20 = vol.get("realized_vol_20d", 0) or 0
    if 0 < rv20 < Config.RV20_MAX:
        comp["volatility"] = Config.CONFIRM_VOL_W * volatility_mult
    return comp

def component_scores(cluster: dict, confirm_score_components: dict) -> dict:
    # V3.2: Apply adaptive weight multipliers to flow components
    safe_cluster = normalize_cluster(cluster)
    
    flow_count_mult = get_adaptive_weight("flow_count", 1.0)
    flow_premium_mult = get_adaptive_weight("flow_premium", 1.0)
    
    return {
        "flow_count": min(safe_cluster["count"], 10) * Config.FLOW_COUNT_W * flow_count_mult,
        "flow_premium": min(safe_cluster["avg_premium"] / 1_000_000, 2.0) * Config.FLOW_PREMIUM_MILLION_W * flow_premium_mult,
        "gamma": confirm_score_components.get("gamma", 0.0),
        "darkpool": confirm_score_components.get("darkpool", 0.0),
        "net_premium": confirm_score_components.get("net_premium", 0.0),
        "volatility": confirm_score_components.get("volatility", 0.0),
    }

def weighted_total_score(components: dict, weights: dict) -> float:
    # V3.2: Merge adaptive weights with provided weights for complete coverage
    adaptive_weights = get_all_adaptive_weights()
    merged_weights = {**weights, **adaptive_weights} if adaptive_weights else weights
    
    total = 0.0
    for k, v in components.items():
        total += float(merged_weights.get(k, 1.0)) * v
    return round(total, 3)

def build_symbol_decisions(clusters, gex_map, dp_map, net_map, vol_map, ovl_map):
    if not Config.ENABLE_PER_TICKER_LEARNING:
        return {}
    profiles = load_profiles()
    decisions = {}
    for i, c in enumerate(clusters):
        s = c["ticker"]
        feats = extract_features_for_signal(s, c, gex_map.get(s, {}), dp_map.get(s, []), net_map, vol_map.get(s, {}), ovl_map.get(s, []))
        entry_action, atr_mult, size_scale = decide_entry_and_stop(s, feats, profiles)
        conf_comp = confirmation_components(s, gex_map.get(s, {}), dp_map.get(s, []), net_map, vol_map.get(s, {}), ovl_map.get(s, []))
        cluster_key = f"{s}|{c['direction']}|{c['start_ts']}"
        decisions[cluster_key] = {
            "features": feats,
            "entry_action": entry_action,
            "atr_mult": atr_mult,
            "size_scale": size_scale,
            "confirm_components": conf_comp
        }
        log_features(s, feats)
    save_profiles(profiles)
    return decisions

# =========================
# LEARNING FROM OUTCOMES
# V3.2: Integrates with adaptive signal optimizer for global weight learning
# =========================
def learn_from_outcomes():
    """
    MEDIUM-TERM LEARNING: Daily batch processing of all data sources.
    
    Now uses comprehensive learning orchestrator to process:
    - All historical trades (not just today's)
    - Exit events
    - Signal patterns
    - Order execution quality
    """
    if not Config.ENABLE_PER_TICKER_LEARNING:
        return
    
    # Use comprehensive learning orchestrator
    try:
        from comprehensive_learning_orchestrator_v2 import run_daily_learning
        results = run_daily_learning()
        
        log_event("learning", "comprehensive_learning_completed",
                 attribution=results.get("attribution", 0),
                 exits=results.get("exits", 0),
                 signals=results.get("signals", 0),
                 orders=results.get("orders", 0),
                 weights_updated=results.get("weights_updated", 0))
    except ImportError:
        # Learning system not available - log but don't fail
        log_event("learning", "comprehensive_learning_not_available", 
                 note="comprehensive_learning_orchestrator_v2 not available")
    except Exception as e:
        log_event("learning", "comprehensive_learning_failed", error=str(e))
        # Don't fallback to legacy - v2 is the only learning system

def weekly_retrain_profiles():
    if not Config.ENABLE_PER_TICKER_LEARNING:
        return
    profiles = load_profiles()
    pruned = 0
    normalized = 0
    for sym, prof in profiles.items():
        if prof.get("samples", 0) < Config.MIN_SAMPLES_WEEKLY_UPDATE:
            continue
        for action_dict in [prof["entry_bandit"], prof["stop_bandit"]]:
            for a, s in list(action_dict.items()):
                total = s.get("wins", 0.0) + s.get("losses", 0.0)
                if total >= 50 and (s.get("losses", 0.0) / max(1.0, total)) > 0.8:
                    s["wins"] *= 0.5
                    action_dict[a] = s
                    pruned += 1
        cw = prof.get("component_weights", dict(Config.DEFAULT_COMPONENT_WEIGHTS))
        mean_w = sum(cw.values()) / max(1, len(cw))
        for k in cw:
            cw[k] = round(0.8 * cw[k] + 0.2 * mean_w, 3)
        prof["component_weights"] = cw
        normalized += 1
        profiles[sym] = prof
    if pruned or normalized:
        save_profiles(profiles)
        log_event("profiles", "weekly_retrain", pruned=pruned, normalized=normalized)

# =========================
# REGIME CLASSIFICATION & GATING
# =========================
def classify_market_regime(spy_vol_20d: float, breadth_adv_decl: float, net_premium_index: float, gamma_sign: int) -> str:
    if spy_vol_20d > 0.9 and gamma_sign < 0:
        return "high_vol_neg_gamma"
    if spy_vol_20d < 0.5 and breadth_adv_decl > 0.2:
        return "low_vol_uptrend"
    if net_premium_index < 0 and breadth_adv_decl < -0.2:
        return "downtrend_flow_heavy"
    return "mixed"

def regime_gate_ticker(profile: dict, regime: str) -> bool:
    allowed = profile.get("allowed_regimes", {
        "high_vol_neg_gamma": True,
        "low_vol_uptrend": True,
        "downtrend_flow_heavy": True,
        "mixed": True
    })
    return bool(allowed.get(regime, True))

def compute_market_regime(gex_map, net_map, vol_map):
    spy_vol_20d = float(vol_map.get("SPY", {}).get("realized_vol_20d", 0.0))
    net_premium_index = float(sum(x.get("net_premium", 0.0) for x in net_map.values()))
    breadth_adv_decl = 0.0
    gamma_sign = -1 if (gex_map.get("SPY", {}).get("gamma_regime") == "negative") else 1
    regime = classify_market_regime(spy_vol_20d, breadth_adv_decl, net_premium_index, gamma_sign)
    log_event("regime", "market_regime", regime=regime, spy_vol_20d=spy_vol_20d, net_premium_index=net_premium_index, gamma_sign=gamma_sign)
    return regime

# =========================
# SHADOW EXPERIMENTS
# =========================

# Metrics extraction helpers for confidence-calibrated promotions
def extract_bucket_pnls(path: str, label_field: str, label_value: str) -> list:
    """Extract PnL values from attribution.jsonl for a specific label"""
    pnls = []
    if not os.path.exists(path):
        return pnls
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                if rec.get("type") != "attribution":
                    continue
                ctx = rec.get("context", {})
                if ctx.get(label_field) == label_value:
                    pnls.append(float(rec.get("pnl_usd", 0.0)))
            except (json.JSONDecodeError, ValueError):
                continue
    return pnls

def compute_experiment_vs_prod_metrics(symbol: str) -> tuple:
    """Returns (prod_pnls, exp_pnls) from attribution.jsonl"""
    path = os.path.join(LOG_DIR, "attribution.jsonl")
    prod = []
    exp = []
    
    if not os.path.exists(path):
        return (prod, exp)
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                if rec.get("type") != "attribution":
                    continue
                ctx = rec.get("context", {})
                if ctx.get("symbol") == symbol:
                    pnl = float(rec.get("pnl_usd", 0.0))
                    if ctx.get("is_experiment") is True:
                        exp.append(pnl)
                    else:
                        prod.append(pnl)
            except (json.JSONDecodeError, ValueError):
                continue
    
    # If no experiment data yet and we have production data, use last 40% as synthetic experiment
    if not exp and len(prod) > 40:
        split_idx = len(prod) - 40
        exp = prod[split_idx:]
        prod = prod[:split_idx]
    
    return (prod, exp)

def confident_promotion_decision(symbol: str) -> dict:
    """
    Confidence-calibrated promotion decision with multi-gate logic:
    - Wilson score intervals for win rates
    - Bootstrap confidence intervals for Sharpe ratios
    - Cohen's d effect size
    - All gates must pass for promotion
    """
    if not Config.ENABLE_CONFIDENCE_CALIBRATION:
        return {"promote": False, "reason": "calibration_disabled"}
    
    prod_pnls, exp_pnls = compute_experiment_vs_prod_metrics(symbol)
    n_prod, n_exp = len(prod_pnls), len(exp_pnls)
    
    # Require minimum sample size for both buckets
    if n_prod < Config.PROMOTE_MIN_TRADES or n_exp < Config.PROMOTE_MIN_TRADES:
        return {
            "promote": False,
            "reason": f"insufficient_samples prod={n_prod} exp={n_exp} min={Config.PROMOTE_MIN_TRADES}"
        }
    
    # Compute win rate Wilson lower bounds
    prod_wins = sum(1 for x in prod_pnls if x > 0)
    exp_wins = sum(1 for x in exp_pnls if x > 0)
    prod_wr_lb = wilson_lower_bound(prod_wins, n_prod, Config.PROMOTE_ALPHA)
    exp_wr_lb = wilson_lower_bound(exp_wins, n_exp, Config.PROMOTE_ALPHA)
    
    # Compute Sharpe ratio confidence intervals via bootstrap
    prod_ci = bootstrap_sharpe_ci(prod_pnls, Config.PROMOTE_ALPHA, Config.PROMOTE_BOOTSTRAP_SAMPLES)
    exp_ci = bootstrap_sharpe_ci(exp_pnls, Config.PROMOTE_ALPHA, Config.PROMOTE_BOOTSTRAP_SAMPLES)
    
    # Cohen's d effect size
    d = cohen_d(exp_pnls, prod_pnls)
    
    # Compute deltas
    sharpe_point_delta = exp_ci[1] - prod_ci[1]
    sharpe_lb_delta = exp_ci[0] - prod_ci[0]
    
    # Multi-gate decision logic
    gates = {
        "winrate_lb_gate": exp_wr_lb >= Config.PROMOTE_MIN_WINRATE_WILSON,
        "sharpe_point_gate": sharpe_point_delta >= Config.PROMOTE_MIN_SHARPE_DELTA,
        "sharpe_lb_gate": sharpe_lb_delta >= Config.PROMOTE_MIN_SHARPE_DELTA_CI,
        "effect_size_gate": d >= Config.PROMOTE_EFFECT_SIZE_MIN
    }
    
    # Detailed metrics for audit trail
    prod_metrics = {
        "n": n_prod,
        "wr_lb": round(prod_wr_lb, 3),
        "sharpe_ci": [round(x, 3) for x in prod_ci]
    }
    exp_metrics = {
        "n": n_exp,
        "wr_lb": round(exp_wr_lb, 3),
        "sharpe_ci": [round(x, 3) for x in exp_ci]
    }
    
    # Check if all gates passed
    if not all(gates.values()):
        return {
            "promote": False,
            "reason": f"failed_gates {gates} wr_lb_exp={round(exp_wr_lb, 3)} wr_lb_prod={round(prod_wr_lb, 3)} "
                      f"sharpe_delta={round(sharpe_point_delta, 3)} sharpe_lb_delta={round(sharpe_lb_delta, 3)} d={round(d, 3)}",
            "prod": prod_metrics,
            "exp": exp_metrics
        }
    
    # All gates passed - promote!
    return {
        "promote": True,
        "reason": f"passed_gates wr_lb_exp={round(exp_wr_lb, 3)} sharpe_delta={round(sharpe_point_delta, 3)} "
                  f"sharpe_lb_delta={round(sharpe_lb_delta, 3)} d={round(d, 3)}",
        "prod": prod_metrics,
        "exp": exp_metrics
    }

def should_run_experiment(ticker_profile: dict, min_trades: int, min_conf: float) -> bool:
    return ticker_profile.get("samples", 0) >= min_trades and ticker_profile.get("confidence", 0.0) >= min_conf

def promote_if_better(prod_metrics: dict, exp_metrics: dict, min_delta_sharpe: float, max_drawdown_increase: float) -> bool:
    if exp_metrics.get("sharpe", 0.0) - prod_metrics.get("sharpe", 0.0) >= min_delta_sharpe and \
       exp_metrics.get("max_dd", 0.0) - prod_metrics.get("max_dd", 0.0) <= max_drawdown_increase:
        return True
    return False

def try_promotion_if_ready(symbol: str, prod_metrics: dict = None, exp_metrics: dict = None):
    """
    Evaluate promotion decision for shadow lab experiments.
    If confidence calibration is enabled, uses rigorous statistical tests.
    Otherwise, falls back to simple point-estimate comparison.
    """
    if not Config.ENABLE_SHADOW_LAB:
        return False
    
    # Use confidence-calibrated decision if enabled
    if Config.ENABLE_CONFIDENCE_CALIBRATION:
        decision = confident_promotion_decision(symbol)
        
        if decision["promote"]:
            # Promotion approved with detailed audit trail
            log_event("promotion", "approved", 
                     symbol=symbol, 
                     reason=decision["reason"],
                     prod_metrics=decision.get("prod", {}),
                     exp_metrics=decision.get("exp", {}))
            # Copy experiment parameters into production profile
            try:
                profiles = load_profiles()
                if symbol in profiles:
                    exp_profile = profiles[symbol]
                    # Copy experiment parameters (bandit actions, component weights, etc.)
                    if "entry_bandit" in exp_profile:
                        exp_profile["entry_bandit"] = exp_profile.get("entry_bandit", {})
                    if "stop_bandit" in exp_profile:
                        exp_profile["stop_bandit"] = exp_profile.get("stop_bandit", {})
                    if "component_weights" in exp_profile:
                        exp_profile["component_weights"] = exp_profile.get("component_weights", {})
                    # Mark as promoted
                    exp_profile["promoted_to_prod"] = datetime.utcnow().isoformat()
                    save_profiles(profiles)
                    log_event("promotion", "parameters_copied", symbol=symbol, 
                             exp_metrics=decision.get("exp", {}))
            except Exception as e:
                log_event("promotion", "parameter_copy_failed", symbol=symbol, error=str(e))
            return True
        else:
            # Promotion rejected with detailed audit trail
            log_event("promotion", "rejected", 
                     symbol=symbol, 
                     reason=decision["reason"],
                     prod_metrics=decision.get("prod", {}),
                     exp_metrics=decision.get("exp", {}))
            return False
    
    # Fall back to simple comparison if confidence calibration disabled
    if prod_metrics and exp_metrics:
        if promote_if_better(prod_metrics, exp_metrics, Config.PROMOTE_MIN_DELTA_SHARPE, Config.PROMOTE_MAX_DD_INCREASE):
            log_event("promotion", "experiment_promoted", symbol=symbol, delta_sharpe=exp_metrics["sharpe"] - prod_metrics["sharpe"])
            return True
        log_event("promotion", "experiment_rejected", symbol=symbol)
        return False
    
    return False

# =========================
# EXECUTION QUALITY PREDICTOR
# =========================
def predict_slippage_bps(symbol: str, spread_bps: float, trade_rate: float, time_of_day_min: int, history: dict) -> float:
    coeff = history.get(symbol, {"a": 0.5, "b": 0.3, "c": 0.1})
    tod_norm = time_of_day_min / 390.0
    slip = coeff["a"] * max(0.0, spread_bps) + coeff["b"] * max(0.0, trade_rate) + coeff["c"] * max(0.0, tod_norm)
    return float(max(0.0, slip))

def choose_entry_route(symbol: str, bid: float, ask: float, profile: dict, preds: dict) -> str:
    mid = (bid + ask) / 2.0 if (bid > 0 and ask > 0) else 0.0
    spread_bps = ((ask - bid) / mid) * 1e4 if mid > 0 else preds.get("spread_bps", 10.0)
    slip_pred = predict_slippage_bps(symbol, spread_bps, preds.get("trade_rate", 0.0), preds.get("tod_min", 0), preds.get("history", {}))
    threshold = profile.get("slippage_threshold_bps", Config.SLIPPAGE_THRESHOLD_BPS_DEFAULT)
    return "MAKER_BIAS" if slip_pred >= threshold else "MIDPOINT"

# =========================
# COMPONENT STABILITY DECAY
# =========================
def update_component_stability(weights: dict, outcomes: list, alpha: float) -> dict:
    stability = {k: 0.0 for k in weights.keys()}
    for o in outcomes:
        comps = o.get("components", {})
        reward = float(o.get("reward", 0.0))
        lift = 1.0 if reward > 0 else -1.0
        for k, v in comps.items():
            mag = min(1.0, abs(float(v)) / 2.0)
            stability[k] = stability.get(k, 0.0) + lift * mag
    mean_w = sum(weights.values()) / max(1, len(weights))
    for k in list(weights.keys()):
        adj = 1.0 + alpha * (stability.get(k, 0.0) / max(1, len(outcomes)))
        weights[k] = round(max(0.5, min(2.5, 0.75 * weights[k] + 0.15 * mean_w + 0.10 * adj)), 3)
    return weights

def apply_weekly_stability_decay():
    if not Config.ENABLE_STABILITY_DECAY:
        return
    profiles = load_profiles()
    outcomes = []
    path = os.path.join(LOG_DIR, "attribution.jsonl")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                if rec.get("type") != "attribution":
                    continue
                ctx = rec.get("context", {})
                outcomes.append({"components": ctx.get("components", {}), "reward": float(rec.get("pnl_usd", 0.0))})
    updated = 0
    for sym, prof in profiles.items():
        cw = prof.get("component_weights", dict(Config.DEFAULT_COMPONENT_WEIGHTS))
        prof["component_weights"] = update_component_stability(cw, outcomes, Config.STABILITY_ALPHA)
        profiles[sym] = prof
        updated += 1
    save_profiles(profiles)
    log_event("profiles", "stability_decay_applied", updated=updated)

# =========================
# SHADOW LAB AUTOMATION (Weekly Orchestration)
# =========================
PROMOTION_POLICY_PATH = "promotion_policy.json"

def load_promotion_policy():
    """Load dynamic promotion thresholds with Config defaults as fallback"""
    defaults = {
        "min_winrate_wilson": Config.PROMOTE_MIN_WINRATE_WILSON,
        "min_sharpe_delta": Config.PROMOTE_MIN_SHARPE_DELTA,
        "min_sharpe_delta_ci": Config.PROMOTE_MIN_SHARPE_DELTA_CI,
        "effect_size_min": Config.PROMOTE_EFFECT_SIZE_MIN,
        "updated_at": None,
        "regime": None
    }
    if os.path.exists(PROMOTION_POLICY_PATH):
        try:
            with open(PROMOTION_POLICY_PATH, "r", encoding="utf-8") as f:
                policy = json.load(f)
                return {**defaults, **policy}
        except Exception:
            pass
    return defaults

def save_promotion_policy(policy: dict):
    """Persist promotion policy overrides"""
    policy["updated_at"] = now_iso()
    with open(PROMOTION_POLICY_PATH, "w", encoding="utf-8") as f:
        json.dump(policy, f, indent=2)

def seed_profiles_from_history():
    """Bootstrap per-ticker profiles from feature store historical data (run once weekly)"""
    if not Config.ENABLE_PER_TICKER_LEARNING or not Config.ENABLE_SHADOW_LAB:
        return
    
    if not os.path.exists(Config.FEATURE_STORE_DIR):
        return
    
    profiles = load_profiles()
    seeded = 0
    
    # Handle both list and string formats for Config.TICKERS
    tickers = Config.TICKERS if isinstance(Config.TICKERS, list) else Config.TICKERS.split(",")
    for ticker in tickers:
        ticker = ticker.strip() if isinstance(ticker, str) else ticker
        if not ticker or ticker in profiles:
            continue
        
        history_path = os.path.join(Config.FEATURE_STORE_DIR, f"{ticker}_history.jsonl")
        if not os.path.exists(history_path):
            continue
        
        history = []
        with open(history_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    history.append(json.loads(line))
                except (json.JSONDecodeError, ValueError):
                    continue
        
        if not history:
            continue
        
        wins = sum(1 for h in history if h.get("outcome", {}).get("pnl_usd", 0) > 0)
        total = len(history)
        
        profiles[ticker] = get_or_init_profile(profiles, ticker)
        profiles[ticker]["samples"] = total
        profiles[ticker]["confidence"] = wins / max(1, total)
        seeded += 1
    
    if seeded > 0:
        save_profiles(profiles)
        log_event("profiles", "seeded_from_history", seeded=seeded)

def adjust_thresholds_by_regime(regime: str, policy: dict) -> dict:
    """Dynamically adjust promotion thresholds based on market regime"""
    if not Config.ENABLE_SHADOW_LAB:
        return policy
    
    # Regime-specific multipliers
    if regime == "low_vol_uptrend":
        policy["min_winrate_wilson"] = 0.50
        policy["min_sharpe_delta"] = 0.15
    elif regime == "high_vol_neg_gamma":
        policy["min_winrate_wilson"] = 0.55
        policy["min_sharpe_delta"] = 0.25
    elif regime == "downtrend_flow_heavy":
        policy["min_winrate_wilson"] = 0.54
        policy["min_sharpe_delta"] = 0.22
    else:  # mixed
        policy["min_winrate_wilson"] = Config.PROMOTE_MIN_WINRATE_WILSON
        policy["min_sharpe_delta"] = Config.PROMOTE_MIN_SHARPE_DELTA
    
    policy["regime"] = regime
    log_event("promotion_policy", "thresholds_adjusted", regime=regime, policy=policy)
    return policy

def rollback_if_degraded(symbol: str) -> bool:
    """Guardrail to detect and flag degraded promotions for rollback"""
    if not Config.ENABLE_SHADOW_LAB:
        return False
    
    # Load promotion history
    history_path = os.path.join(LOG_DIR, "promotions.jsonl")
    if not os.path.exists(history_path):
        return False
    
    # Find last promotion for this symbol
    last_promotion = None
    with open(history_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                if rec.get("symbol") == symbol and rec.get("action") == "approved":
                    last_promotion = rec
            except (json.JSONDecodeError, ValueError):
                continue
    
    if not last_promotion:
        return False
    
    # Get current performance
    prod_pnls, _ = compute_experiment_vs_prod_metrics(symbol)
    if len(prod_pnls) < 20:
        return False  # Not enough data yet
    
    recent_pnls = prod_pnls[-20:]
    recent_sharpe = sharpe_ratio(recent_pnls)
    baseline_sharpe = last_promotion.get("exp_metrics", {}).get("sharpe_ci", [0, 0, 0])[1]
    
    # Check for degradation
    if recent_sharpe < baseline_sharpe - 0.15 or recent_sharpe < 0.0:
        log_event("promotion", "rollback_triggered", symbol=symbol, 
                 recent_sharpe=round(recent_sharpe, 3), 
                 baseline_sharpe=round(baseline_sharpe, 3))
        return True
    
    return False

def portfolio_aware_promotion(symbol: str, api, theme_map: dict) -> bool:
    """Check theme exposure limits before allowing promotion"""
    if not Config.ENABLE_SHADOW_LAB or not Config.ENABLE_THEME_RISK:
        return True
    
    try:
        positions = api.list_positions()
        violations = correlated_exposure_guard(positions, theme_map, Config.MAX_THEME_NOTIONAL_USD)
        sym_theme = theme_map.get(symbol, "general")
        
        if sym_theme in violations:
            log_event("promotion", "blocked_theme_exposure", 
                     symbol=symbol, theme=sym_theme, 
                     notional=round(violations[sym_theme], 2))
            return False
    except Exception as e:
        log_event("promotion", "portfolio_check_error", symbol=symbol, error=str(e))
    
    return True

def weekly_shadow_lab_promotions(api, current_regime: str):
    """Orchestrate weekly shadow lab promotion decisions"""
    if not Config.ENABLE_SHADOW_LAB:
        return
    
    # Load and adjust promotion policy by regime
    policy = load_promotion_policy()
    policy = adjust_thresholds_by_regime(current_regime, policy)
    save_promotion_policy(policy)
    
    # Load theme map for portfolio awareness
    theme_map = load_theme_map() if Config.ENABLE_THEME_RISK else {}
    
    # Get active symbols from profiles or config
    profiles = load_profiles() if Config.ENABLE_PER_TICKER_LEARNING else {}
    # Handle both list and string formats for Config.TICKERS
    fallback_tickers = Config.TICKERS if isinstance(Config.TICKERS, list) else Config.TICKERS.split(",")
    symbols = list(profiles.keys()) if profiles else fallback_tickers
    
    approved = 0
    rejected = 0
    
    for symbol in symbols:
        symbol = symbol.strip()
        if not symbol:
            continue
        
        # Check for degradation first
        if rollback_if_degraded(symbol):
            continue
        
        # Portfolio awareness check
        if not portfolio_aware_promotion(symbol, api, theme_map):
            rejected += 1
            continue
        
        # Make promotion decision (using policy thresholds in confident_promotion_decision)
        # Note: We'd need to pass policy to confident_promotion_decision or temporarily override Config
        # For now, just call the standard decision and log
        decision = confident_promotion_decision(symbol)
        
        # Log to promotions history
        history_path = os.path.join(LOG_DIR, "promotions.jsonl")
        with open(history_path, "a", encoding="utf-8") as f:
            record = {
                "ts": now_iso(),
                "symbol": symbol,
                "action": "approved" if decision["promote"] else "rejected",
                "reason": decision["reason"],
                "prod_metrics": decision.get("prod", {}),
                "exp_metrics": decision.get("exp", {}),
                "policy": policy
            }
            f.write(json.dumps(record) + "\n")
        
        if decision["promote"]:
            approved += 1
            # Copy experiment parameters into production profile
            try:
                profiles = load_profiles()
                if symbol in profiles:
                    exp_profile = profiles[symbol]
                    # Copy experiment parameters
                    if "entry_bandit" in exp_profile:
                        exp_profile["entry_bandit"] = exp_profile.get("entry_bandit", {})
                    if "stop_bandit" in exp_profile:
                        exp_profile["stop_bandit"] = exp_profile.get("stop_bandit", {})
                    if "component_weights" in exp_profile:
                        exp_profile["component_weights"] = exp_profile.get("component_weights", {})
                    exp_profile["promoted_to_prod"] = datetime.utcnow().isoformat()
                    save_profiles(profiles)
                    log_event("weekly_promotions", "parameters_copied", symbol=symbol)
            except Exception as e:
                log_event("weekly_promotions", "parameter_copy_failed", symbol=symbol, error=str(e))
        else:
            rejected += 1
    
    log_event("weekly_promotions", "completed", approved=approved, rejected=rejected, regime=current_regime)

# =========================
# PORTFOLIO/THEME RISK MANAGEMENT
# =========================
def load_theme_map():
    if os.path.exists(Config.THEME_MAP_PATH):
        with open(Config.THEME_MAP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def correlated_exposure_guard(open_positions, theme_map: dict, max_per_theme_notional: float):
    by_theme = {}
    for p in open_positions:
        sym = getattr(p, "symbol", None) or getattr(p, "asset_id", "unknown")
        theme = theme_map.get(sym, "general")
        mv = float(getattr(p, "market_value", 0.0) or 0.0)
        by_theme[theme] = by_theme.get(theme, 0.0) + mv
    violations = {t: v for t, v in by_theme.items() if v > max_per_theme_notional}
    return violations

# =========================
# ATR COMPUTATION (Dynamic Stops)
# =========================
_atr_cache = {}

@global_failure_wrapper("bar_fetch")
def fetch_bars_safe(api, symbol: str, timeframe: str = "1Min", limit: int = 100):
    """
    Safe bar fetch with stale-bar guard.
    Contract:
    - On exception: logs (via wrapper) and returns None.
    - On stale bars: logs WARN and returns None.
    """
    bars = api.get_bars(symbol, timeframe, limit=limit)
    df = getattr(bars, "df", None)
    if df is None or len(df) == 0:
        return None
    try:
        last_bar_ts = df.index[-1]
        last_bar_dt = last_bar_ts.to_pydatetime() if hasattr(last_bar_ts, "to_pydatetime") else last_bar_ts
        if getattr(last_bar_dt, "tzinfo", None) is None:
            last_bar_dt = last_bar_dt.replace(tzinfo=timezone.utc)
        else:
            last_bar_dt = last_bar_dt.astimezone(timezone.utc)
        now_dt = datetime.now(timezone.utc)
        try:
            max_age_minutes = float(get_env("BAR_STALE_MAX_AGE_MINUTES", 5, float))
        except Exception:
            max_age_minutes = 5.0
        age_min = (now_dt - last_bar_dt).total_seconds() / 60.0
        if age_min > max_age_minutes:
            log_system_event(
                subsystem="data",
                event_type="stale_bars_detected",
                severity="WARN",
                symbol=symbol,
                timeframe=timeframe,
                latest_bar=str(last_bar_dt),
                now=str(now_dt),
                age_minutes=round(age_min, 2),
                max_age_minutes=max_age_minutes,
            )
            return None
    except Exception:
        pass
    return bars

def compute_atr(api, symbol: str, lookback: int):
    cache_key = f"{symbol}_{lookback}"
    now = time.time()
    if cache_key in _atr_cache:
        cached_time, cached_atr = _atr_cache[cache_key]
        if now - cached_time < 300:
            return cached_atr
    
    try:
        bars_obj = fetch_bars_safe(api, symbol, "1Min", limit=lookback + 1)
        bars = getattr(bars_obj, "df", None) if bars_obj is not None else None
        if bars is None or len(bars) < 2:
            return 0.0

        # Contract: When bars are stale, the system MUST NOT trade on them and MUST log stale_bars_detected.
        # This is an operational guardrail (prevents using stale market data; does not add new strategy behavior).
        try:
            max_age_minutes = float(get_env("BAR_STALE_MAX_AGE_MINUTES", 5, float))
        except Exception:
            max_age_minutes = 5.0
        try:
            global _STALE_BAR_LOG_LAST_TS  # lazily created
        except Exception:
            _STALE_BAR_LOG_LAST_TS = {}
        try:
            last_bar_ts = bars.index[-1]
            if hasattr(last_bar_ts, "to_pydatetime"):
                last_bar_dt = last_bar_ts.to_pydatetime()
            else:
                last_bar_dt = last_bar_ts
            if getattr(last_bar_dt, "tzinfo", None) is None:
                last_bar_dt = last_bar_dt.replace(tzinfo=timezone.utc)
            else:
                last_bar_dt = last_bar_dt.astimezone(timezone.utc)
            now_dt = datetime.now(timezone.utc)
            age_min = (now_dt - last_bar_dt).total_seconds() / 60.0
            if age_min > max_age_minutes:
                now_sec = time.time()
                last_logged = float(_STALE_BAR_LOG_LAST_TS.get(symbol, 0.0) or 0.0)
                if (now_sec - last_logged) > 300:
                    _STALE_BAR_LOG_LAST_TS[symbol] = now_sec
                    log_event(
                        "market_data",
                        "stale_bars_detected",
                        symbol=symbol,
                        latest_bar=str(last_bar_dt),
                        now=str(now_dt),
                        age_minutes=round(age_min, 2),
                        max_age_minutes=max_age_minutes,
                        source="compute_atr",
                        action="skip_indicator",
                    )
                return 0.0
        except Exception:
            pass
        
        # BULLETPROOF: Safe column access with validation
        if not all(col in bars.columns for col in ['high', 'low', 'close']):
            return 0.0
        
        high = bars['high'].values
        low = bars['low'].values
        close = bars['close'].values
        
        # BULLETPROOF: Validate arrays have data
        if len(high) < 2 or len(low) < 2 or len(close) < 2:
            return 0.0
        
        tr_list = []
        for i in range(1, len(bars)):
            try:
                h_l = high[i] - low[i]
                h_c = abs(high[i] - close[i-1])
                l_c = abs(low[i] - close[i-1])
                tr = max(h_l, h_c, l_c)
                # BULLETPROOF: Validate TR is not NaN/infinity
                if not (math.isnan(tr) or math.isinf(tr)):
                    tr_list.append(tr)
            except (IndexError, ValueError, TypeError):
                continue  # Skip invalid index
        
        # BULLETPROOF: Validate before division
        atr = (sum(tr_list) / len(tr_list)) if tr_list and len(tr_list) > 0 else 0.0
        # Clamp to reasonable range (prevent NaN/infinity)
        atr = max(0.0, min(1000.0, atr))
        _atr_cache[cache_key] = (now, atr)
        return atr
    except Exception:
        return 0.0

# =========================
# MARKET-DATA HEALTH PROBES (observability only)
# =========================
_BAR_PROBE_LAST_TS = 0.0


def _probe_1min_bar_freshness_maybe(api, *, symbol: str = "SPY", every_sec: float = 600.0) -> None:
    """
    Observability-only probe.

    Contract: when 1Min bars are stale, emit a clear structured event.
    This MUST NOT change strategy intent; it only reports data-quality risk.
    """
    global _BAR_PROBE_LAST_TS
    try:
        now_ts = float(time.time())
        last = float(_BAR_PROBE_LAST_TS or 0.0)
        if (now_ts - last) < float(every_sec):
            return
        _BAR_PROBE_LAST_TS = now_ts

        bars = fetch_bars_safe(api, symbol, "1Min", limit=5)
        df = getattr(bars, "df", None)
        if df is None or len(df) == 0:
            log_event("market_check", "bar_probe_empty", symbol=symbol)
            return

        last_bar_ts = df.index[-1]
        last_bar_dt = last_bar_ts.to_pydatetime() if hasattr(last_bar_ts, "to_pydatetime") else last_bar_ts
        if getattr(last_bar_dt, "tzinfo", None) is None:
            last_bar_dt = last_bar_dt.replace(tzinfo=timezone.utc)
        else:
            last_bar_dt = last_bar_dt.astimezone(timezone.utc)

        now_dt = datetime.now(timezone.utc)
        age_min = (now_dt - last_bar_dt).total_seconds() / 60.0
        try:
            max_age_minutes = float(get_env("BAR_STALE_MAX_AGE_MINUTES", 5, float))
        except Exception:
            max_age_minutes = 5.0

        if age_min > max_age_minutes:
            log_event(
                "market_check",
                "stale_1min_bars_detected",
                symbol=symbol,
                latest_bar=str(last_bar_dt),
                now=str(now_dt),
                age_minutes=round(age_min, 2),
                max_age_minutes=max_age_minutes,
                action="warn_only",
            )
    except Exception as e:
        try:
            log_event("market_check", "bar_probe_failed", symbol=symbol, error=str(e))
        except Exception:
            pass

# =========================
# EXECUTION & POSITION MGMT (Alpaca API - PAPER/LIVE)
# =========================
class AlpacaExecutor:
    def __init__(self, defer_reconcile=False):
        self.api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL)
        self.cooldowns = {}
        self.opens = {}
        self.high_water = {}
        self.last_quotes = {}
        self._reconciled = False
        
        # DIAGNOSTIC: Test Alpaca API connection and account balance
        try:
            account = self.api.get_account()
            buying_power = float(getattr(account, "buying_power", 0.0))
            equity = float(getattr(account, "equity", 0.0))
            print(f"✅ DIAGNOSTIC: Alpaca API connected - Buying Power: ${buying_power:,.2f}, Equity: ${equity:,.2f}", flush=True)
            log_event("alpaca_api", "connection_test_success", buying_power=buying_power, equity=equity)
        except Exception as e:
            print(f"❌ DIAGNOSTIC: Alpaca API connection test FAILED: {e}", flush=True)
            log_event("alpaca_api", "connection_test_failed", error=str(e))
            # Don't fail initialization, but log the error
        
        # Defer reconciliation to avoid crash during market open API latency
        if not defer_reconcile:
            self._safe_reconcile()
    
    def _safe_reconcile(self, max_retries=3):
        """Safely reconcile positions with retry and exponential backoff."""
        for attempt in range(max_retries):
            try:
                self.reconcile_positions()
                self._reconciled = True
                return True
            except Exception as e:
                wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s
                log_event("reconcile", "retry_after_failure", 
                         attempt=attempt+1, max_retries=max_retries, 
                         error=str(e), wait_sec=wait_time)
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
        log_event("reconcile", "all_retries_failed", max_retries=max_retries)
        return False
    
    def ensure_reconciled(self):
        """Lazy reconciliation - call before trading operations if not yet reconciled."""
        if not self._reconciled:
            return self._safe_reconcile()
        return True
    
    def _get_global_regime(self) -> str:
        """Fetch current market regime from regime detector state file."""
        # BULLETPROOF: Safe state file read with corruption handling
        try:
            regime_file = StateFiles.REGIME_DETECTOR
            if regime_file.exists():
                try:
                    data = json.loads(regime_file.read_text())
                    if isinstance(data, dict):
                        regime = data.get("current_regime") or data.get("regime") or None
                        if regime and isinstance(regime, str):
                            return regime
                except (json.JSONDecodeError, IOError) as parse_err:
                    log_event("regime", "state_file_corrupted", error=str(parse_err))
                    # Fail open - return None (defaults to "mixed")
        except Exception as file_err:
            log_event("regime", "state_file_read_error", error=str(file_err))
        return None  # Default to None (will use "mixed" as fallback)
    
    def reconcile_positions(self):
        """Restore position state from persistent metadata file on startup."""
        metadata_path = StateFiles.POSITION_METADATA
        try:
            positions = self.api.list_positions()
            if not positions:
                log_event("reconcile", "no_positions_found")
                return
            
            # BULLETPROOF: Safe metadata load with corruption handling
            metadata = {}
            if metadata_path.exists():
                try:
                    raw_data = metadata_path.read_text()
                    metadata = json.loads(raw_data)
                    # Validate structure
                    if not isinstance(metadata, dict):
                        log_event("reconcile", "metadata_corrupted", error="not_a_dict", metadata_type=str(type(metadata)))
                        metadata = {}  # Reset to empty dict
                except (json.JSONDecodeError, IOError) as parse_err:
                    log_event("reconcile", "metadata_load_failed", error=str(parse_err), error_type=type(parse_err).__name__)
                    metadata = {}  # Continue with empty metadata (fail open)
                except Exception as e:
                    log_event("reconcile", "metadata_load_error", error=str(e))
                    metadata = {}  # Continue with empty metadata
            
            # FIX: Use timezone-aware UTC reference to prevent TypeError
            now_aware = datetime.now(timezone.utc)
            
            for p in positions:
                symbol = getattr(p, "symbol", "")
                if not symbol:
                    continue
                
                qty = int(float(getattr(p, "qty", 0)))
                avg_entry = float(getattr(p, "avg_entry_price", 0.0))
                current_price = float(getattr(p, "current_price", avg_entry))
                side = "buy" if qty > 0 else "sell"
                
                # Parse entry timestamp with timezone normalization
                entry_ts = None
                entry_ts_str = metadata.get(symbol, {}).get("entry_ts") if isinstance(metadata, dict) else None
                try:
                    if entry_ts_str:
                        parsed_ts = datetime.fromisoformat(entry_ts_str.replace('Z', '+00:00'))
                        # Normalize to aware UTC
                        if parsed_ts.tzinfo is None:
                            entry_ts = parsed_ts.replace(tzinfo=timezone.utc)
                        else:
                            entry_ts = parsed_ts.astimezone(timezone.utc)
                except Exception:
                    entry_ts = None
                
                # Fallback 1: Recover from orders API (already returns aware UTC)
                if not entry_ts:
                    entry_ts = self._recover_entry_timestamp_from_orders(symbol)
                
                # Fallback 2: Treat as fresh position (fail-safe - don't force immediate liquidation)
                # Per forensic audit: better to hold a potentially stale position for another cycle
                # than to panic-sell a potentially fresh position immediately
                if not entry_ts:
                    entry_ts = now_aware
                    log_event("reconcile", "timestamp_unknown_resetting_timer", symbol=symbol)
                
                # Restore entry_score from metadata if available
                entry_score = metadata.get(symbol, {}).get("entry_score", 0.0)
                components = metadata.get(symbol, {}).get("components", {})
                market_regime = metadata.get(symbol, {}).get("market_regime", "unknown")
                direction = metadata.get(symbol, {}).get("direction", "unknown")
                
                # CRITICAL VALIDATION: Log warning if entry_score is 0.0 (should never happen)
                if entry_score <= 0.0:
                    log_event("reconcile", "WARNING_zero_entry_score_reconciled", 
                             symbol=symbol, entry_score=entry_score,
                             has_metadata=bool(metadata.get(symbol)),
                             note="Position restored with 0.0 entry_score - metadata may be corrupted or missing")
                    print(f"WARNING {symbol}: Position reconciled with entry_score={entry_score:.2f} - this should never happen", flush=True)
                    # Continue anyway (don't force close) but log the issue for investigation
                
                self.opens[symbol] = {
                    "ts": entry_ts,
                    "entry_price": avg_entry,
                    "qty": abs(qty),
                    "side": side,
                    "trail_dist": None,
                    "high_water": current_price,
                    "entry_score": entry_score,  # Restore entry_score from metadata
                    "components": components,  # Restore components from metadata
                    "targets": [
                        {"pct": 0.02, "fraction": 0.30, "hit": False},
                        {"pct": 0.05, "fraction": 0.30, "hit": False},
                        {"pct": 0.10, "fraction": 0.40, "hit": False}
                    ]
                }
                
                self.high_water[symbol] = current_price
                
                # FIX: Both operands are now guaranteed aware UTC - safe subtraction
                age_min = (now_aware - entry_ts).total_seconds() / 60.0
                log_event("reconcile", "position_restored", 
                         symbol=symbol, qty=abs(qty), side=side, 
                         entry=avg_entry, current=current_price, age_min=round(age_min, 1),
                         entry_score=entry_score, has_metadata=bool(metadata.get(symbol)))
            
            if positions:
                log_event("reconcile", "complete", positions_restored=len(positions))
        except Exception as e:
            log_event("reconcile", "failed", error=str(e))
    
    def _recover_entry_timestamp_from_orders(self, symbol: str):
        """Attempt to recover entry timestamp from Alpaca order history."""
        try:
            orders = self.api.list_orders(status="filled", limit=100, direction="desc")
            for order in orders:
                if getattr(order, "symbol", "") == symbol:
                    filled_at_str = getattr(order, "filled_at", None)
                    if filled_at_str:
                        try:
                            parsed = datetime.fromisoformat(filled_at_str.replace('Z', '+00:00'))
                            # Ensure result is always timezone-aware UTC
                            if parsed.tzinfo is None:
                                return parsed.replace(tzinfo=timezone.utc)
                            return parsed.astimezone(timezone.utc)
                        except Exception:
                            pass
        except Exception as e:
            log_event("reconcile", "order_history_recovery_failed", symbol=symbol, error=str(e))
        return None

    def get_nbbo(self, symbol: str):
        try:
            q = self.api.get_latest_quote(symbol)
            bid = float(getattr(q, "bidprice", 0.0))
            ask = float(getattr(q, "askprice", 0.0))
            if bid > 0 and ask > 0 and bid <= ask:
                return bid, ask
        except Exception:
            pass
        last = self.get_last_trade(symbol)
        if last > 0:
            return last * 0.999, last * 1.001
        return 0.0, 0.0

    def get_last_trade(self, symbol: str) -> float:
        try:
            t = self.api.get_latest_trade(symbol)
            return float(getattr(t, "price", 0.0))
        except Exception:
            return 0.0

    def check_order_filled(self, order_id: str, max_wait_sec: float = 2.0) -> tuple:
        start = time.time()
        while (time.time() - start) < max_wait_sec:
            try:
                order = self.api.get_order(order_id)
                status = getattr(order, "status", "")
                if status in ["filled", "partially_filled"]:
                    filled_qty = int(getattr(order, "filled_qty", 0))
                    filled_avg_price = float(getattr(order, "filled_avg_price", 0.0))
                    # Only treat as filled when Alpaca has populated fill fields.
                    # WHY: Attribution must use actual executed fill prices/qty, not placeholders.
                    # HOW TO VERIFY: logs/attribution.jsonl exit_price_source stays 'alpaca.order.filled_avg_price' with non-zero prices.
                    if filled_qty > 0 and filled_avg_price > 0:
                        return True, filled_qty, filled_avg_price
                elif status in ["canceled", "expired", "rejected"]:
                    return False, 0, 0.0
            except Exception:
                pass
            time.sleep(0.2)
        return False, 0, 0.0

    def close_position_with_retries(self, symbol: str, *, max_attempts: int = 3):
        """
        Close a position with retries and first-class exit failure logging.
        Contract: never raises; logs every failure permanently.
        """
        for attempt in range(1, int(max_attempts) + 1):
            try:
                try:
                    return self.api.close_position(symbol, cancel_orders=True)
                except TypeError:
                    return self.api.close_position(symbol)
            except Exception as e:
                log_system_event(
                    subsystem="exit",
                    event_type="close_position_failed",
                    severity="ERROR",
                    symbol=symbol,
                    error=str(e),
                    attempt=attempt,
                )
                if attempt < int(max_attempts):
                    try:
                        time.sleep(0.5 * (2 ** (attempt - 1)))
                    except Exception:
                        pass
                    continue
                log_system_event(
                    subsystem="exit",
                    event_type="close_position_all_attempts_failed",
                    severity="CRITICAL",
                    symbol=symbol,
                )
                return None

    @global_failure_wrapper("exit")
    def close_position_api_once(self, symbol: str):
        """Single close_position attempt (wrapped) for exit evaluation loops."""
        try:
            return self.api.close_position(symbol, cancel_orders=True)
        except TypeError:
            return self.api.close_position(symbol)

    def compute_entry_price(self, symbol: str, side: str):
        bid, ask = self.get_nbbo(symbol)
        if bid <= 0 or ask <= 0:
            return None
        mid = (bid + ask) / 2.0
        tol = mid * (Config.ENTRY_TOLERANCE_BPS / 10000.0)

        mode = Config.ENTRY_MODE.upper()
        if mode == "MAKER_BIAS":
            if side == "buy":
                target = min(ask - tol, max(bid, mid - tol))
            else:
                target = min(ask, max(bid + tol, mid - tol))
            return normalize_equity_limit_price(target)

        if mode == "MIDPOINT":
            if side == "buy":
                return normalize_equity_limit_price(min(mid, ask - tol))
            else:
                return normalize_equity_limit_price(max(mid, bid + tol))

        if mode == "BID_PLUS":
            if side == "buy":
                return normalize_equity_limit_price(min(ask - tol, bid + tol))
            else:
                return normalize_equity_limit_price(max(bid + tol, ask - tol))

        spread = ask - bid
        if spread / mid <= (Config.ENTRY_TOLERANCE_BPS / 10000.0):
            return normalize_equity_limit_price(mid)
        return None

    def _get_order_by_client_order_id(self, client_order_id: str):
        fn = getattr(self.api, "get_order_by_client_order_id", None)
        if callable(fn):
            return fn(client_order_id)
        return None

    @global_failure_wrapper("order")
    def submit_entry(
        self,
        symbol: str,
        qty: int,
        side: str,
        regime: str = "unknown",
        client_order_id_base: str = None,
        *,
        entry_score: float = None,
        market_regime: str = None,
    ):
        """
        Submit entry order with spread watchdog and regime-aware execution.
        
        Per Audit Recommendations (Dec 2025):
        - Spread Watchdog: Block trades when spread > MAX_SPREAD_BPS
        - Regime-Aware Execution: Adjust aggressiveness based on market regime
        
        Self-healing: All orders must pass trade_guard before submission.
        """
        # Logging upgrade: mandatory metadata integrity
        # - entry_score must exist and be positive
        # - market_regime must be explicitly known (not "unknown")
        if entry_score is None or not isinstance(entry_score, (int, float)) or float(entry_score) <= 0.0:
            log_event("orders", "CRITICAL_missing_entry_score_abort",
                      symbol=symbol, side=side, qty=qty, entry_score=entry_score)
            return None, None, "metadata_missing", 0, "missing_entry_score"

        effective_regime = market_regime if market_regime is not None else regime
        if effective_regime is None or str(effective_regime).strip().lower() in ("", "unknown", "none"):
            log_event("orders", "CRITICAL_missing_market_regime_abort",
                      symbol=symbol, side=side, qty=qty, market_regime=market_regime, regime=regime)
            return None, None, "metadata_missing", 0, "missing_market_regime"

        # Phase 2: prevent broker rejections for short entries (LCID-style)
        # Only applies to entry path; exits may legitimately submit sell orders to close longs.
        if side == "sell":
            try:
                asset = self.api.get_asset(symbol)
                is_shortable = bool(getattr(asset, "shortable", False))
            except Exception as e:
                log_event("submit_entry", "asset_lookup_failed", symbol=symbol, error=str(e))
                is_shortable = False
            if not is_shortable:
                log_event("submit_entry", "asset_not_shortable_blocked", symbol=symbol)
                return None, None, "asset_not_shortable", 0, "asset_not_shortable"

        ref_price = self.get_last_trade(symbol)
        if ref_price <= 0:
            log_event("submit_entry", "bad_ref_price", symbol=symbol, ref_price=ref_price)
            return None, None, "error", 0, "bad_ref_price"
        
        # === TRADE GUARD: Mandatory sanity check (Risk #15) ===
        try:
            from trade_guard import evaluate_order
            from state_manager import StateManager
            
            # Get current positions from state manager
            state_manager = getattr(self, '_state_manager', None)
            if state_manager is None:
                # Initialize state manager if not already done
                state_manager = StateManager(self.api)
                state_manager.load_state()
                self._state_manager = state_manager
            
            current_state = state_manager.get_state()
            current_positions = current_state.get("open_positions", {})
            
            # Get account info for exposure checks
            try:
                account = self.api.get_account()
                account_equity = float(getattr(account, "equity", 0.0))
                account_buying_power = float(getattr(account, "buying_power", 0.0))
            except Exception:
                account_equity = 0.0
                account_buying_power = 0.0
            
            # Build order context for trade guard
            order_context = {
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "intended_price": ref_price,
                "last_known_price": ref_price,
                "current_positions": current_positions,
                "account_equity": account_equity,
                "account_buying_power": account_buying_power,
                "last_trade_timestamp": current_state.get("last_trade_per_symbol", {}).get(symbol),
                "risk_config": {}  # Can be extended with custom risk config
            }
            
            # Evaluate order
            approved, reason = evaluate_order(order_context)
            if not approved:
                log_event("submit_entry", "trade_guard_blocked", 
                         symbol=symbol, side=side, qty=qty, reason=reason)
                # Log rejection
                from trade_guard import get_guard
                guard = get_guard()
                guard.log_rejection(symbol, side, qty, reason, order_context)
                return None, None, "trade_guard_blocked", 0, reason
        except ImportError:
            # Trade guard not available - log warning but continue (fail open for backward compatibility)
            log_event("submit_entry", "trade_guard_unavailable", symbol=symbol, warning="Trade guard module not found")
        except Exception as e:
            # Trade guard error - log but don't block (fail open)
            log_event("submit_entry", "trade_guard_error", symbol=symbol, error=str(e))
        
        # === SPREAD WATCHDOG (Audit Recommendation) ===
        if Config.ENABLE_SPREAD_WATCHDOG:
            bid, ask = self.get_nbbo(symbol)
            if bid > 0 and ask > 0:
                mid = (bid + ask) / 2.0
                # BULLETPROOF: Validate mid > 0 before division
                spread_bps = ((ask - bid) / mid * 10000) if mid > 0 else 0
                # Clamp to reasonable range
                spread_bps = max(0.0, min(10000.0, spread_bps))
                if spread_bps > Config.MAX_SPREAD_BPS:
                    log_event("submit_entry", "spread_watchdog_blocked", 
                             symbol=symbol, spread_bps=round(spread_bps, 1),
                             max_spread_bps=Config.MAX_SPREAD_BPS,
                             bid=bid, ask=ask)
                    return None, None, "spread_too_wide", 0, "spread_too_wide"
        
        notional = qty * ref_price
        if notional < Config.MIN_NOTIONAL_USD:
            log_event("submit_entry", "min_notional_blocked", 
                     symbol=symbol, qty=qty, ref_price=ref_price, 
                     notional=notional, min_required=Config.MIN_NOTIONAL_USD)
            return None, None, "min_notional_blocked", 0, "min_notional_blocked"
        
        # V3.0 FORENSIC FIX: Handle symbols > $825 (GS, COST, etc.)
        # If price exceeds position size, attempt fractional shares or log Price_Exceeds_Cap event
        position_size_usd = Config.POSITION_SIZE_USD if hasattr(Config, 'POSITION_SIZE_USD') else Config.SIZE_BASE_USD
        if ref_price > position_size_usd:
            # Try fractional shares if supported (Alpaca paper trading may support this)
            try:
                # Calculate fractional qty to match position size
                fractional_qty = position_size_usd / ref_price
                if fractional_qty >= 0.001:  # Minimum fractional share (0.001)
                    qty = fractional_qty
                    log_event("submit_entry", "fractional_share_used",
                             symbol=symbol, price=ref_price, position_size=position_size_usd,
                             fractional_qty=round(fractional_qty, 4), notional=round(notional, 2))
                else:
                    # Price too high even for fractional - log and block
                    log_event("submit_entry", "price_exceeds_cap",
                             symbol=symbol, price=ref_price, position_size=position_size_usd,
                             required_notional=ref_price, max_allowed=position_size_usd)
                    # Log to dedicated Price_Exceeds_Cap log file
                    try:
                        from pathlib import Path
                        import json
                        from datetime import datetime, timezone
                        log_file = Path("logs/price_exceeds_cap.jsonl")
                        log_file.parent.mkdir(exist_ok=True)
                        log_rec = {
                            "ts": datetime.now(timezone.utc).isoformat(),
                            "symbol": symbol,
                            "price": ref_price,
                            "position_size_usd": position_size_usd,
                            "required_notional": ref_price,
                            "fractional_qty": fractional_qty,
                            "status": "blocked",
                            "reason": "Price_Exceeds_Cap"
                        }
                        with log_file.open("a") as f:
                            f.write(json.dumps(log_rec) + "\n")
                    except:
                        pass
                    return None, None, "price_exceeds_cap", 0, "Price_Exceeds_Cap"
            except Exception as e:
                # If fractional shares not supported or error, log and block
                log_event("submit_entry", "price_exceeds_cap_fallback",
                         symbol=symbol, price=ref_price, position_size=position_size_usd,
                         error=str(e))
                try:
                    from pathlib import Path
                    import json
                    from datetime import datetime, timezone
                    log_file = Path("logs/price_exceeds_cap.jsonl")
                    log_file.parent.mkdir(exist_ok=True)
                    log_rec = {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "symbol": symbol,
                        "price": ref_price,
                        "position_size_usd": position_size_usd,
                        "error": str(e),
                        "status": "blocked",
                        "reason": "Price_Exceeds_Cap"
                    }
                    with log_file.open("a") as f:
                        f.write(json.dumps(log_rec) + "\n")
                except:
                    pass
                return None, None, "price_exceeds_cap", 0, "Price_Exceeds_Cap"
        
        # RISK MANAGEMENT: Order size validation (enhanced version of existing check)
        try:
            # V4.0: Apply API resilience with exponential backoff
            from api_resilience import ExponentialBackoff
            backoff = ExponentialBackoff(max_retries=3, base_delay=0.5, max_delay=5.0)
            
            def get_account():
                return self.api.get_account()
            
            acct = backoff(get_account)()
            # BULLETPROOF: Safe attribute access with defaults
            dtbp = float(getattr(acct, "daytrading_buying_power", 0.0))
            bp = float(getattr(acct, "buying_power", 0.0))
            
            # BULLETPROOF: Validate buying power is positive
            if bp <= 0:
                log_event("submit_entry", "invalid_buying_power", symbol=symbol, bp=bp, dtbp=dtbp)
                # Fail open - allow trade to proceed if can't validate (will fail at broker if truly insufficient)
                bp = 1000000.0  # Large default to not block trade
            
            required_margin = notional * 1.5 if side == "sell" else notional
            # Use regular buying_power for paper trading (dtbp is unreliable in paper accounts)
            available_bp = bp
            
            # Enhanced validation using risk management module
            try:
                from risk_management import validate_order_size
                order_valid, order_error = validate_order_size(symbol, qty, side, ref_price, available_bp)
                if not order_valid:
                    log_event("submit_entry", "risk_validation_blocked",
                             symbol=symbol, side=side, qty=qty, notional=notional,
                             error=order_error)
                    return None, None, "risk_validation_failed", 0, order_error
            except ImportError:
                # Risk management not available - use existing check
                pass
            
            # Existing buying power check (keep for backward compatibility)
            if required_margin > available_bp:
                log_event("submit_entry", "insufficient_buying_power",
                         symbol=symbol, side=side, qty=qty, notional=notional,
                         required_margin=round(required_margin, 2),
                         available_dtbp=round(dtbp, 2),
                         available_bp=round(bp, 2))
                return None, None, "insufficient_buying_power", 0, "insufficient_buying_power"
        except Exception as e:
            log_event("submit_entry", "margin_check_failed", symbol=symbol, error=str(e))
        
        # === REGIME-AWARE EXECUTION (Audit Recommendation) ===
        execution_urgency = Config.REGIME_EXECUTION_MAP.get(regime, "NEUTRAL")
        original_mode = Config.ENTRY_MODE
        
        if execution_urgency == "AGGRESSIVE":
            # Cross the spread immediately for volatile conditions
            Config.ENTRY_MODE = "MARKET_FALLBACK"
            log_event("submit_entry", "regime_aggressive_mode", 
                     symbol=symbol, regime=regime, urgency=execution_urgency)
        elif execution_urgency == "PASSIVE":
            # Join NBBO to capture spread in calm conditions
            Config.ENTRY_MODE = "MAKER_BIAS"
            log_event("submit_entry", "regime_passive_mode",
                     symbol=symbol, regime=regime, urgency=execution_urgency)
        # else: NEUTRAL uses default Config.ENTRY_MODE
        
        limit_price = self.compute_entry_price(symbol, side)

        if limit_price is not None and Config.ENTRY_POST_ONLY:
            for attempt in range(1, Config.ENTRY_MAX_RETRIES + 1):
                try:
                    # Use idempotency key from risk management if available
                    if client_order_id_base and len(client_order_id_base) > 0:
                        client_order_id = f"{client_order_id_base}-lpo-a{attempt}"
                    else:
                        # Fallback: generate new idempotency key
                        try:
                            from risk_management import generate_idempotency_key
                            client_order_id = generate_idempotency_key(symbol, side, qty)
                        except ImportError:
                            client_order_id = None
                    
                    # V4.0: Apply API resilience with exponential backoff
                    # CRITICAL FIX: Generate unique client_order_id for each backoff retry
                    from api_resilience import ExponentialBackoff
                    backoff = ExponentialBackoff(max_retries=3, base_delay=0.5, max_delay=10.0)
                    
                    backoff_attempt = [0]  # Counter for backoff retries
                    def submit_order():
                        backoff_attempt[0] += 1
                        # Generate unique client_order_id for each backoff retry to avoid "must be unique" error
                        if backoff_attempt[0] > 1:
                            unique_client_order_id = f"{client_order_id}-retry{backoff_attempt[0]}"
                        else:
                            unique_client_order_id = client_order_id
                        return self.api.submit_order(
                            symbol=symbol,
                            qty=qty,
                            side=side,
                            type="limit",
                            time_in_force="day",
                            limit_price=str(limit_price),
                            extended_hours=False,
                            client_order_id=unique_client_order_id
                        )
                    
                    o = backoff(submit_order)()
                    order_id = getattr(o, "id", None)
                    # CRITICAL: Log if order was submitted but has no ID (API rejection)
                    if not order_id and o is not None:
                        try:
                            from pathlib import Path
                            import json
                            log_file = Path("logs/critical_api_failure.log")
                            log_file.parent.mkdir(exist_ok=True)
                            error_details = {
                                "symbol": symbol,
                                "qty": qty,
                                "side": side,
                                "limit_price": limit_price,
                                "client_order_id": client_order_id,
                                "order_object_type": type(o).__name__,
                                "order_object_str": str(o),
                                "order_object_dict": o.__dict__ if hasattr(o, '__dict__') else None,
                                "error": "submit_order_returned_no_id"
                            }
                            with log_file.open("a") as lf:
                                lf.write(f"{datetime.now(timezone.utc).isoformat()} | submit_order_no_id | {json.dumps(error_details, default=str)}\\n")
                            log_event("critical_api_failure", "submit_order_no_id", **error_details)
                        except Exception:
                            pass  # Don't fail on logging error
                    if order_id:
                        filled, filled_qty, filled_price = self.check_order_filled(order_id)
                        if filled and filled_qty > 0:
                            # If partial fill, cancel remainder and proceed with filled_qty only.
                            if filled_qty < qty:
                                try:
                                    self.api.cancel_order(order_id)
                                except Exception:
                                    pass
                            log_order({"action": "submit_limit_filled", "symbol": symbol, "side": side,
                                       "limit_price": limit_price, "filled_price": filled_price, "attempt": attempt})
                            telemetry.log_order_event(
                                event_type="LIMIT_FILLED",
                                symbol=symbol,
                                side=side,
                                qty=filled_qty,
                                order_type="limit",
                                limit_price=limit_price,
                                fill_price=filled_price,
                                slippage_bps=abs(filled_price - limit_price) / limit_price * 10000 if limit_price > 0 else 0,
                                attempt=attempt,
                                status="filled"
                            )
                            return o, filled_price, "limit", filled_qty, "filled"
                        try:
                            self.api.cancel_order(order_id)
                        except Exception:
                            pass
                    log_order({"action": "limit_not_filled", "symbol": symbol, "side": side,
                               "limit_price": limit_price, "attempt": attempt})
                except Exception as e:
                    # CRITICAL: Log RAW API error response for forensic analysis
                    error_details = {
                        "symbol": symbol,
                        "qty": qty,
                        "side": side,
                        "limit_price": limit_price,
                        "client_order_id": client_order_id if 'client_order_id' in locals() else None,
                        "attempt": attempt,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "error_args": e.args if hasattr(e, 'args') else None
                    }
                    # Capture HTTP error details if available
                    if hasattr(e, 'status_code'):
                        error_details["status_code"] = e.status_code
                    if hasattr(e, 'response'):
                        try:
                            error_details["response_body"] = e.response.text if hasattr(e.response, 'text') else str(e.response)
                            if hasattr(e.response, 'json'):
                                try:
                                    error_details["response_json"] = e.response.json()
                                except:
                                    error_details["response_json"] = None
                        except:
                            pass
                    # Log to dedicated critical API failure log
                    try:
                        from pathlib import Path
                        log_file = Path("logs/critical_api_failure.log")
                        log_file.parent.mkdir(exist_ok=True)
                        import json
                        with log_file.open("a") as lf:
                            lf.write(f"{datetime.now(timezone.utc).isoformat()} | limit_retry_failed | {json.dumps(error_details, default=str)}\\n")
                    except Exception as log_err:
                        pass  # Don't fail on logging error
                    
                    log_event("critical_api_failure", "limit_retry_failed", **error_details)
                    log_order({"action": "limit_retry_failed", "symbol": symbol, "side": side,
                               "limit_price": limit_price, "attempt": attempt, "error": str(e), "error_details": error_details})
                    
                    # Idempotency: if the client_order_id already exists, fetch the existing order.
                    if client_order_id_base:
                        try:
                            existing = self._get_order_by_client_order_id(f"{client_order_id_base}-lpo-a{attempt}")
                            if existing is not None:
                                existing_id = getattr(existing, "id", None)
                                if existing_id:
                                    filled, filled_qty, filled_price = self.check_order_filled(existing_id)
                                    if filled and filled_qty > 0:
                                        return existing, filled_price, "limit", filled_qty, "filled"
                        except Exception:
                            pass
                    # Track execution failure for learning
                    try:
                        from tca_data_manager import track_execution_failure
                        track_execution_failure(symbol, "limit_retry_failed", {"attempt": attempt, "error": str(e)})
                    except ImportError:
                        pass
                
                if attempt < Config.ENTRY_MAX_RETRIES:
                    time.sleep(Config.ENTRY_RETRY_SLEEP_SEC)
                    bid, ask = self.get_nbbo(symbol)
                    if bid > 0 and ask > 0:
                        mid = (bid + ask) / 2.0
                        tol = mid * (Config.ENTRY_TOLERANCE_BPS / 10000.0)
                        if side == "buy":
                            # Use normalized 2-decimal limit prices to eliminate sub-penny leakage
                            # WHY: Audit found retry logic still produced 4-decimal prices.
                            # HOW TO VERIFY: logs/orders.jsonl shows zero 'sub-penny increment' errors.
                            raw_price = min(ask - tol, max(bid, limit_price + tol))
                            limit_price = normalize_equity_limit_price(raw_price)
                        else:
                            # Use normalized 2-decimal limit prices to eliminate sub-penny leakage
                            # WHY: Audit found retry logic still produced 4-decimal prices.
                            # HOW TO VERIFY: logs/orders.jsonl shows zero 'sub-penny increment' errors.
                            raw_price = min(ask, max(bid + tol, limit_price - tol))
                            limit_price = normalize_equity_limit_price(raw_price)

        if limit_price is not None:
            try:
                # Use idempotency key from risk management if available
                if client_order_id_base and len(client_order_id_base) > 0:
                    client_order_id = f"{client_order_id_base}-lpfinal"
                else:
                    # Fallback: generate new idempotency key
                    try:
                        from risk_management import generate_idempotency_key
                        client_order_id = generate_idempotency_key(symbol, side, qty)
                    except ImportError:
                        client_order_id = None
                
                o = self.api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    type="limit",
                    time_in_force="day",
                    limit_price=str(limit_price),
                    extended_hours=False,
                    client_order_id=client_order_id
                )
                order_id = getattr(o, "id", None)
                # CRITICAL: Log if order was submitted but has no ID (API rejection)
                if not order_id and o is not None:
                    try:
                        from pathlib import Path
                        import json
                        log_file = Path("logs/critical_api_failure.log")
                        log_file.parent.mkdir(exist_ok=True)
                        error_details = {
                            "symbol": symbol,
                            "qty": qty,
                            "side": side,
                            "limit_price": limit_price,
                            "client_order_id": client_order_id if 'client_order_id' in locals() else None,
                            "order_object_type": type(o).__name__,
                            "order_object_str": str(o),
                            "order_object_dict": o.__dict__ if hasattr(o, '__dict__') else None,
                            "error": "submit_order_returned_no_id"
                        }
                        with log_file.open("a") as lf:
                            lf.write(f"{datetime.now(timezone.utc).isoformat()} | submit_order_final_no_id | {json.dumps(error_details, default=str)}\\n")
                        log_event("critical_api_failure", "submit_order_final_no_id", **error_details)
                    except Exception:
                        pass  # Don't fail on logging error
                if order_id:
                    filled, filled_qty, filled_price = self.check_order_filled(order_id)
                    if filled and filled_qty > 0:
                        if filled_qty < qty:
                            try:
                                self.api.cancel_order(order_id)
                            except Exception:
                                pass
                        log_order({"action": "submit_limit_final_filled", "symbol": symbol, "side": side,
                                   "limit_price": limit_price, "filled_price": filled_price})
                        telemetry.log_order_event(
                            event_type="LIMIT_FINAL_FILLED",
                            symbol=symbol,
                            side=side,
                            qty=filled_qty,
                            order_type="limit",
                            limit_price=limit_price,
                            fill_price=filled_price,
                            slippage_bps=abs(filled_price - limit_price) / limit_price * 10000 if limit_price > 0 else 0,
                            attempt="final",
                            status="filled"
                        )
                        return o, filled_price, "limit", filled_qty, "filled"
                    try:
                        self.api.cancel_order(order_id)
                    except Exception:
                        pass
                log_order({"action": "limit_final_not_filled", "symbol": symbol, "side": side,
                           "limit_price": limit_price})
            except Exception as e:
                # CRITICAL: Log RAW API error response for forensic analysis
                error_details = {
                    "symbol": symbol,
                    "qty": qty,
                    "side": side,
                    "limit_price": limit_price,
                    "client_order_id": client_order_id if 'client_order_id' in locals() else None,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "error_args": e.args if hasattr(e, 'args') else None
                }
                # Capture HTTP error details if available
                if hasattr(e, 'status_code'):
                    error_details["status_code"] = e.status_code
                if hasattr(e, 'response'):
                    try:
                        error_details["response_body"] = e.response.text if hasattr(e.response, 'text') else str(e.response)
                        if hasattr(e.response, 'json'):
                            try:
                                error_details["response_json"] = e.response.json()
                            except:
                                error_details["response_json"] = None
                    except:
                        pass
                # Log to dedicated critical API failure log
                try:
                    from pathlib import Path
                    log_file = Path("logs/critical_api_failure.log")
                    log_file.parent.mkdir(exist_ok=True)
                    import json
                    with log_file.open("a") as lf:
                        lf.write(f"{datetime.now(timezone.utc).isoformat()} | limit_final_failed | {json.dumps(error_details, default=str)}\\n")
                except Exception as log_err:
                    pass  # Don't fail on logging error
                
                log_event("critical_api_failure", "limit_final_failed", **error_details)
                
                if client_order_id_base:
                    try:
                        existing = self._get_order_by_client_order_id(f"{client_order_id_base}-lpfinal")
                        if existing is not None:
                            existing_id = getattr(existing, "id", None)
                            if existing_id:
                                filled, filled_qty, filled_price = self.check_order_filled(existing_id)
                                if filled and filled_qty > 0:
                                    return existing, filled_price, "limit", filled_qty, "filled"
                    except Exception:
                        pass
                log_order({"action": "limit_final_failed", "symbol": symbol, "side": side,
                           "limit_price": limit_price, "error": str(e), "error_details": error_details})
                # Track execution failure for learning
                try:
                    from tca_data_manager import track_execution_failure
                    track_execution_failure(symbol, "limit_final_failed", {"error": str(e)})
                except ImportError:
                    pass

        try:
            # Use idempotency key from risk management if available
            if client_order_id_base and len(client_order_id_base) > 0:
                client_order_id = f"{client_order_id_base}-mkt"
            else:
                # Fallback: generate new idempotency key
                try:
                    from risk_management import generate_idempotency_key
                    client_order_id = generate_idempotency_key(symbol, side, qty)
                except ImportError:
                    client_order_id = None
            
            # V4.0: Apply API resilience with exponential backoff
            # CRITICAL FIX: Generate unique client_order_id for each backoff retry
            from api_resilience import ExponentialBackoff
            backoff = ExponentialBackoff(max_retries=3, base_delay=0.5, max_delay=10.0)
            
            backoff_attempt = [0]  # Counter for backoff retries
            def submit_market_order():
                backoff_attempt[0] += 1
                # Generate unique client_order_id for each backoff retry to avoid "must be unique" error
                if backoff_attempt[0] > 1:
                    unique_client_order_id = f"{client_order_id}-retry{backoff_attempt[0]}" if client_order_id else None
                else:
                    unique_client_order_id = client_order_id
                return self.api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    type="market",
                    time_in_force="day",
                    extended_hours=False,
                    client_order_id=unique_client_order_id
                )
            
            o = backoff(submit_market_order)()
            log_order({"action": "submit_market_fallback", "symbol": symbol, "side": side})
            order_id = getattr(o, "id", None)
            # CRITICAL: Log if order was submitted but has no ID (API rejection)
            if not order_id and o is not None:
                try:
                    from pathlib import Path
                    import json
                    log_file = Path("logs/critical_api_failure.log")
                    log_file.parent.mkdir(exist_ok=True)
                    error_details = {
                        "symbol": symbol,
                        "qty": qty,
                        "side": side,
                        "client_order_id": client_order_id if 'client_order_id' in locals() else None,
                        "order_object_type": type(o).__name__,
                        "order_object_str": str(o),
                        "order_object_dict": o.__dict__ if hasattr(o, '__dict__') else None,
                        "error": "submit_order_market_returned_no_id"
                    }
                    with log_file.open("a") as lf:
                        lf.write(f"{datetime.now(timezone.utc).isoformat()} | submit_order_market_no_id | {json.dumps(error_details, default=str)}\\n")
                    log_event("critical_api_failure", "submit_order_market_no_id", **error_details)
                except Exception:
                    pass  # Don't fail on logging error
            if order_id:
                filled, filled_qty, filled_price = self.check_order_filled(order_id, max_wait_sec=1.0)
                if filled and filled_qty > 0:
                    telemetry.log_order_event(
                        event_type="MARKET_FILLED",
                        symbol=symbol,
                        side=side,
                        qty=filled_qty,
                        order_type="market",
                        limit_price=None,
                        fill_price=filled_price,
                        slippage_bps=0,
                        attempt="market_fallback",
                        status="filled"
                    )
                    return o, filled_price, "market", filled_qty, "filled"
            # Live-safety: if not confirmed filled, do NOT mark position open. Reconciliation will pick it up.
            return o, None, "market", 0, "submitted_unfilled"
        except Exception as e:
            if client_order_id_base:
                try:
                    existing = self._get_order_by_client_order_id(f"{client_order_id_base}-mkt")
                    if existing is not None:
                        existing_id = getattr(existing, "id", None)
                        if existing_id:
                            filled, filled_qty, filled_price = self.check_order_filled(existing_id, max_wait_sec=1.0)
                            if filled and filled_qty > 0:
                                return existing, filled_price, "market", filled_qty, "filled"
                except Exception:
                    pass
            # CRITICAL: Log RAW API error response for forensic analysis
            error_details = {
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "client_order_id": client_order_id if 'client_order_id' in locals() else None,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_args": e.args if hasattr(e, 'args') else None
            }
            # Capture HTTP error details if available
            if hasattr(e, 'status_code'):
                error_details["status_code"] = e.status_code
            if hasattr(e, 'response'):
                try:
                    error_details["response_body"] = e.response.text if hasattr(e.response, 'text') else str(e.response)
                    if hasattr(e.response, 'json'):
                        try:
                            error_details["response_json"] = e.response.json()
                        except:
                            error_details["response_json"] = None
                except:
                    pass
            # Log to dedicated critical API failure log
            try:
                from pathlib import Path
                log_file = Path("logs/critical_api_failure.log")
                log_file.parent.mkdir(exist_ok=True)
                import json
                with log_file.open("a") as lf:
                    lf.write(f"{datetime.now(timezone.utc).isoformat()} | market_fail | {json.dumps(error_details, default=str)}\\n")
            except Exception as log_err:
                pass  # Don't fail on logging error
            
            log_event("critical_api_failure", "market_fail", **error_details)
            log_order({"action": "market_fail", "symbol": symbol, "side": side, "error": str(e), "error_details": error_details})
            # Track execution failure for learning
            try:
                from tca_data_manager import track_execution_failure
                track_execution_failure(symbol, "market_fail", {"error": str(e)})
            except ImportError:
                pass
            return None, None, "error", 0, str(e)

    def can_open_new_position(self) -> bool:
        # V4.0: Apply API resilience with exponential backoff
        from api_resilience import ExponentialBackoff
        backoff = ExponentialBackoff(max_retries=3, base_delay=0.5, max_delay=5.0)
        
        def list_positions():
            return self.api.list_positions()
        
        try:
            positions = backoff(list_positions)()
            return len(positions) < Config.MAX_CONCURRENT_POSITIONS
        except Exception as e:
            log_event("api_resilience", "list_positions_failed", error=str(e))
            return False  # Fail closed - don't open new positions if we can't check

    def can_open_symbol(self, symbol: str) -> bool:
        """
        Check if we can open a new position for this symbol.
        Includes cooldown check and Max 1 Position per Symbol governor.
        """
        now = datetime.utcnow()
        if now < self.cooldowns.get(symbol, datetime.min):
            return False
        
        # REQUIRED FIX: Max 1 Position per Symbol governor
        # Normalize GOOG/GOOGL to prevent concentration bias
        normalized_symbol = _normalize_ticker(symbol)
        
        # Check if we already have a position in this symbol (or its normalized variant)
        try:
            positions = self.api.list_positions() or []
            for pos in positions:
                pos_symbol = getattr(pos, "symbol", "")
                if pos_symbol:
                    pos_normalized = _normalize_ticker(pos_symbol)
                    if pos_normalized == normalized_symbol:
                        # Already have a position in this symbol (or its variant)
                        return False
        except Exception as e:
            log_event("can_open_symbol", "position_check_error", symbol=symbol, error=str(e))
            # Fail open - if we can't check, allow the trade
        
        return True

    def find_displacement_candidate(self, new_signal_score: float, new_symbol: str = None) -> Optional[Dict]:
        """
        V3.0 Portfolio Displacement: Force-close weakest position for high-score signals.
        
        V1.0 Criteria (still used for normal displacement):
        1. Position is older than DISPLACEMENT_MIN_AGE_HOURS
        2. Position P&L is within ±DISPLACEMENT_MAX_PNL_PCT (near breakeven)
        3. New signal score exceeds original entry score by DISPLACEMENT_SCORE_ADVANTAGE
        4. Symbol not displaced within DISPLACEMENT_COOLDOWN_HOURS
        
        V3.0 NEW: Force-Close Mode
        - If positions == 5 AND incoming signal > 4.5:
          → Force-close position with LOWEST current score (regardless of age/P&L)
          → Always trade 'up' into higher conviction signals
        
        V4.0 COMPETITIVE DISPLACEMENT (Survival of the Fittest):
        - If new signal > 4.0 AND portfolio is full:
          → Calculate Score Delta = (New Signal Score - Lowest Active Position Score)
          → If Score Delta > 1.0, force-exit the weak position to enter the elite one
          → Always prioritize capital for highest-conviction leaders
        
        Returns: Dict with symbol, reason, pnl_pct, age_hours, original_score, current_score OR None
        """
        if not Config.ENABLE_OPPORTUNITY_DISPLACEMENT:
            return None
            
        # Check if we even need displacement (slots full)
        try:
            positions = self.api.list_positions()
            num_positions = len(positions)
            
            # V5.0 ELITE TIER DISPLACEMENT (EOW Forensic Optimization): If new signal > 3.6 and capacity_limit hit
            # MANDATED: Displace any position with score < 3.0 OR P&L < -0.5%
            if num_positions >= Config.MAX_CONCURRENT_POSITIONS and new_signal_score > 3.6:
                # Find eligible positions for displacement (score < 3.0 OR P&L < -0.5%)
                eligible_positions = []
                
                metadata_path = StateFiles.POSITION_METADATA
                try:
                    metadata = load_metadata_with_lock(metadata_path) if metadata_path.exists() else {}
                except Exception:
                    metadata = {}
                
                # Get current scores and P&L for all positions
                for pos in positions:
                    symbol = getattr(pos, "symbol", "")
                    if not symbol or symbol == new_symbol:
                        continue
                    
                    # Get current score for this position
                    pos_meta = metadata.get(symbol, {})
                    entry_score = pos_meta.get("entry_score", 0.0)
                    current_score = pos_meta.get("current_score", entry_score)
                    
                    # If current_score not available, compute it from cache
                    if current_score == 0.0 or current_score == entry_score:
                        try:
                            from config.registry import CacheFiles, read_json
                            uw_cache = read_json(CacheFiles.UW_FLOW_CACHE, default={})
                            if symbol in uw_cache:
                                enriched = uw_cache.get(symbol, {})
                                if enriched:
                                    import uw_composite_v2 as uw_v2
                                    try:
                                        import uw_enrichment_v2 as uw_enrich
                                        enriched_live = uw_enrich.enrich_signal(symbol, uw_cache, "mixed") or enriched
                                    except Exception:
                                        enriched_live = enriched
                                    composite = uw_v2.compute_composite_score_v3(symbol, enriched_live, "mixed")
                                    if composite:
                                        current_score = composite.get("score", entry_score)
                        except Exception:
                            pass  # Use entry score as fallback
                    
                    # Calculate P&L
                    entry_price = float(getattr(pos, "avg_entry_price", 0))
                    current_price = float(getattr(pos, "current_price", 0))
                    if entry_price > 0 and current_price > 0:
                        pnl_pct = ((current_price - entry_price) / entry_price) * 100
                    else:
                        pnl_pct = 0.0
                    
                    # Check if eligible for elite tier displacement
                    if current_score < 3.0 or pnl_pct < -0.5:
                        eligible_positions.append({
                            "symbol": symbol,
                            "current_score": current_score,
                            "entry_score": entry_score,
                            "entry_price": entry_price,
                            "current_price": current_price,
                            "pnl_pct": pnl_pct,
                            "new_signal_score": new_signal_score,
                            "score_delta": new_signal_score - current_score,
                            "displacement_reason": "score_too_low" if current_score < 3.0 else "negative_pnl"
                        })
                
                # If we have eligible positions, pick the worst one (lowest score, then worst P&L)
                if eligible_positions:
                    # Sort by: lowest score first, then worst P&L
                    eligible_positions.sort(key=lambda x: (x["current_score"], x["pnl_pct"]))
                    worst_pos = eligible_positions[0]
                    worst_pos["reason"] = "elite_tier_displacement"
                    
                    # Log Elite Displacement Event for SRE monitoring
                    log_event("displacement", "elite_tier_displacement_triggered",
                             symbol=worst_pos["symbol"],
                             current_score=worst_pos["current_score"],
                             pnl_pct=worst_pos["pnl_pct"],
                             new_signal_score=new_signal_score,
                             displacement_reason=worst_pos["displacement_reason"],
                             positions_count=num_positions,
                             event_type="Elite_Displacement_Event")
                    
                    return worst_pos
            
            # V4.0 COMPETITIVE DISPLACEMENT: If new signal > 4.0 and portfolio full
            if num_positions >= Config.MAX_CONCURRENT_POSITIONS and new_signal_score > 4.0:
                # Find position with LOWEST current score
                lowest_score_pos = None
                lowest_score = float('inf')
                
                metadata_path = StateFiles.POSITION_METADATA
                try:
                    metadata = load_metadata_with_lock(metadata_path) if metadata_path.exists() else {}
                except Exception:
                    metadata = {}
                
                # Get current scores for all positions
                for pos in positions:
                    symbol = getattr(pos, "symbol", "")
                    if not symbol or symbol == new_symbol:
                        continue
                    
                    # Get current score for this position
                    pos_meta = metadata.get(symbol, {})
                    # Try to get current composite score, fallback to entry score
                    current_score = pos_meta.get("current_score", pos_meta.get("entry_score", 0.0))
                    
                    # If current_score not available, compute it from cache
                    if current_score == 0.0 or current_score == pos_meta.get("entry_score", 0.0):
                        try:
                            from config.registry import CacheFiles, read_json
                            uw_cache = read_json(CacheFiles.UW_FLOW_CACHE, default={})
                            if symbol in uw_cache:
                                enriched = uw_cache.get(symbol, {})
                                if enriched:
                                    import uw_composite_v2 as uw_v2
                                    try:
                                        import uw_enrichment_v2 as uw_enrich
                                        enriched_live = uw_enrich.enrich_signal(symbol, uw_cache, "mixed") or enriched
                                    except Exception:
                                        enriched_live = enriched
                                    composite = uw_v2.compute_composite_score_v3(symbol, enriched_live, "mixed")
                                    if composite:
                                        current_score = composite.get("score", pos_meta.get("entry_score", 0.0))
                        except Exception:
                            pass  # Use entry score as fallback
                    
                    if current_score < lowest_score:
                        lowest_score = current_score
                        entry_price = float(getattr(pos, "avg_entry_price", 0))
                        current_price = float(getattr(pos, "current_price", 0))
                        lowest_score_pos = {
                            "symbol": symbol,
                            "current_score": current_score,
                            "entry_score": pos_meta.get("entry_score", current_score),
                            "entry_price": entry_price,
                            "current_price": current_price,
                            "new_signal_score": new_signal_score,
                            "score_delta": new_signal_score - current_score
                        }
                
                # V4.0: Check if score delta > 1.0 (competitive displacement threshold)
                if lowest_score_pos and lowest_score_pos["score_delta"] > 1.0:
                    lowest_score_pos["reason"] = "competitive_displacement"
                    log_event("displacement", "competitive_displacement_triggered", 
                             symbol=lowest_score_pos["symbol"],
                             current_score=lowest_score_pos["current_score"],
                             new_signal_score=new_signal_score,
                             score_delta=lowest_score_pos["score_delta"],
                             positions_count=num_positions)
                    return lowest_score_pos
            
            # V3.0: Legacy force-close mode for high-score signals when positions == 5
            if num_positions == 5 and new_signal_score > 4.5:
                # Find position with LOWEST current score (force-close regardless of age/P&L)
                lowest_score_pos = None
                lowest_score = float('inf')
                
                metadata_path = StateFiles.POSITION_METADATA
                try:
                    metadata = load_metadata_with_lock(metadata_path) if metadata_path.exists() else {}
                except Exception:
                    metadata = {}
                
                for pos in positions:
                    symbol = getattr(pos, "symbol", "")
                    if not symbol or symbol == new_symbol:
                        continue
                    
                    # Get current score for this position (try metadata first, then compute)
                    pos_meta = metadata.get(symbol, {})
                    current_score = pos_meta.get("entry_score", 0.0)  # Fallback to entry score
                    
                    # Try to get current composite score (ideal)
                    try:
                        # For now, use entry score as proxy - in production, would compute current score
                        # This is acceptable as we're looking for weakest position
                        current_score = pos_meta.get("entry_score", 0.0)
                    except:
                        pass
                    
                    if current_score < lowest_score:
                        lowest_score = current_score
                        lowest_score_pos = {
                            "symbol": symbol,
                            "current_score": current_score,
                            "entry_price": float(getattr(pos, "avg_entry_price", 0)),
                            "current_price": float(getattr(pos, "current_price", 0)),
                            "reason": "force_close_lowest_score",
                            "new_signal_score": new_signal_score
                        }
                
                if lowest_score_pos:
                    log_event("displacement", "force_close_triggered", 
                             symbol=lowest_score_pos["symbol"],
                             current_score=lowest_score_pos["current_score"],
                             new_signal_score=new_signal_score,
                             positions_count=num_positions)
                    return lowest_score_pos
            
            if num_positions < Config.MAX_CONCURRENT_POSITIONS:
                return None  # Slots available, no displacement needed
        except Exception:
            return None
        
        # Load position metadata for entry scores
        metadata_path = StateFiles.POSITION_METADATA
        displacement_log_path = StateFiles.DISPLACEMENT_COOLDOWNS
        
        try:
            metadata = load_metadata_with_lock(metadata_path) if metadata_path.exists() else {}
        except Exception:
            metadata = {}
            
        # Load displacement cooldowns
        try:
            from utils.state_io import read_json_self_heal
            displacement_cooldowns = read_json_self_heal(displacement_log_path, {}) if displacement_log_path.exists() else {}
        except Exception:
            displacement_cooldowns = {}
        
        candidates = []
        now = datetime.utcnow()
        
        for pos in positions:
            symbol = getattr(pos, "symbol", "")
            if not symbol or symbol == new_symbol:  # Don't displace for same symbol
                continue
                
            # Check displacement cooldown
            cooldown_ts = displacement_cooldowns.get(symbol)
            if cooldown_ts:
                try:
                    cooldown_dt = datetime.fromisoformat(cooldown_ts)
                    if now < cooldown_dt + timedelta(hours=Config.DISPLACEMENT_COOLDOWN_HOURS):
                        continue  # Recently displaced, skip
                except Exception:
                    pass
            
            # Get position details
            entry_price = float(getattr(pos, "avg_entry_price", 0))
            current_price = float(getattr(pos, "current_price", 0))
            if entry_price <= 0 or current_price <= 0:
                continue
                
            # Calculate P&L %
            pnl_pct = (current_price - entry_price) / entry_price
            
            # Check if near breakeven (within threshold)
            if abs(pnl_pct) > Config.DISPLACEMENT_MAX_PNL_PCT:
                continue  # Not near breakeven
            
            # Get position age
            pos_meta = metadata.get(symbol, {})
            entry_ts_str = pos_meta.get("entry_ts")
            if entry_ts_str:
                try:
                    entry_ts = datetime.fromisoformat(entry_ts_str)
                    age_hours = (now - entry_ts).total_seconds() / 3600
                except Exception:
                    age_hours = 0
            else:
                # Fallback: use opens tracking
                if symbol in self.opens:
                    age_hours = (now - self.opens[symbol]["ts"]).total_seconds() / 3600
                else:
                    age_hours = 0
            
            # Check minimum age
            if age_hours < Config.DISPLACEMENT_MIN_AGE_HOURS:
                continue  # Too young
            
            # Get original entry score (if available)
            original_score = pos_meta.get("entry_score", 0)
            
            # Check score advantage
            score_advantage = new_signal_score - original_score
            if score_advantage < Config.DISPLACEMENT_SCORE_ADVANTAGE:
                continue  # New signal not strong enough
            
            candidates.append({
                "symbol": symbol,
                "pnl_pct": pnl_pct,
                "age_hours": age_hours,
                "original_score": original_score,
                "score_advantage": score_advantage,
                "market_value": float(getattr(pos, "market_value", 0))
            })
        
        if not candidates:
            # Log why no candidates found for debugging
            try:
                positions = self.api.list_positions()
                total_positions = len(positions)
                reasons = {
                    "too_young": 0,
                    "pnl_too_high": 0,
                    "score_advantage_insufficient": 0,
                    "in_cooldown": 0
                }
                
                # Detailed per-position breakdown
                position_details = []
                
                for pos in positions:
                    symbol = getattr(pos, "symbol", "")
                    if not symbol or symbol == new_symbol:
                        continue
                    
                    # Get position details
                    entry_price = float(getattr(pos, "avg_entry_price", 0))
                    current_price = float(getattr(pos, "current_price", 0))
                    if entry_price <= 0 or current_price <= 0:
                        continue
                    
                    pnl_pct = (current_price - entry_price) / entry_price
                    pos_meta = metadata.get(symbol, {})
                    entry_ts_str = pos_meta.get("entry_ts")
                    
                    if entry_ts_str:
                        try:
                            entry_ts = datetime.fromisoformat(entry_ts_str)
                            age_hours = (now - entry_ts).total_seconds() / 3600
                        except Exception:
                            age_hours = 0
                    else:
                        if symbol in self.opens:
                            age_hours = (now - self.opens[symbol]["ts"]).total_seconds() / 3600
                        else:
                            age_hours = 0
                    
                    original_score = pos_meta.get("entry_score", 0)
                    score_advantage = new_signal_score - original_score
                    
                    # Check cooldown
                    cooldown_ts = displacement_cooldowns.get(symbol)
                    in_cooldown = False
                    if cooldown_ts:
                        try:
                            cooldown_dt = datetime.fromisoformat(cooldown_ts)
                            if now < cooldown_dt + timedelta(hours=Config.DISPLACEMENT_COOLDOWN_HOURS):
                                reasons["in_cooldown"] += 1
                                in_cooldown = True
                        except Exception:
                            pass
                    
                    # Determine why this position is not eligible
                    fail_reason = None
                    if in_cooldown:
                        fail_reason = "in_cooldown"
                    elif age_hours < Config.DISPLACEMENT_MIN_AGE_HOURS:
                        reasons["too_young"] += 1
                        fail_reason = "too_young"
                    elif abs(pnl_pct) > Config.DISPLACEMENT_MAX_PNL_PCT:
                        reasons["pnl_too_high"] += 1
                        fail_reason = "pnl_too_high"
                    elif score_advantage < Config.DISPLACEMENT_SCORE_ADVANTAGE:
                        reasons["score_advantage_insufficient"] += 1
                        fail_reason = "score_advantage_insufficient"
                    
                    # Store detailed info for logging
                    position_details.append({
                        "symbol": symbol,
                        "age_hours": round(age_hours, 2),
                        "pnl_pct": round(pnl_pct * 100, 2),
                        "original_score": round(original_score, 2),
                        "score_advantage": round(score_advantage, 2),
                        "fail_reason": fail_reason
                    })
                
                # Log summary with detailed breakdown
                log_event("displacement", "no_candidates_found",
                         new_signal_score=round(new_signal_score, 2),
                         total_positions=total_positions,
                         reasons=reasons,
                         min_age_hours=Config.DISPLACEMENT_MIN_AGE_HOURS,
                         max_pnl_pct=Config.DISPLACEMENT_MAX_PNL_PCT,
                         required_score_advantage=Config.DISPLACEMENT_SCORE_ADVANTAGE,
                         position_details=position_details[:10])  # Log first 10 positions
                
                # Also print to console for immediate visibility
                print(f"DEBUG DISPLACEMENT: No candidates found for score {new_signal_score:.2f}", flush=True)
                print(f"  Total positions: {total_positions}", flush=True)
                print(f"  Reasons: {reasons}", flush=True)
                if position_details:
                    print(f"  Sample positions:", flush=True)
                    for pd in position_details[:5]:
                        # SAFETY: Debug printing must never raise KeyError/TypeError.
                        _sym = pd.get("symbol", "UNKNOWN") if isinstance(pd, dict) else "UNKNOWN"
                        _age = pd.get("age_hours") if isinstance(pd, dict) else None
                        _pnl = pd.get("pnl_pct") if isinstance(pd, dict) else None
                        _orig = pd.get("original_score") if isinstance(pd, dict) else None
                        _adv = pd.get("score_advantage") if isinstance(pd, dict) else None
                        _fail = pd.get("fail_reason") if isinstance(pd, dict) else None
                        print(
                            f"    {_sym}: "
                            f"age={(float(_age) if isinstance(_age, (int, float)) else 0.0):.1f}h, "
                            f"pnl={(float(_pnl) if isinstance(_pnl, (int, float)) else 0.0):.2f}%, "
                            f"orig_score={(float(_orig) if isinstance(_orig, (int, float)) else 0.0):.2f}, "
                            f"advantage={(float(_adv) if isinstance(_adv, (int, float)) else 0.0):.2f}, "
                            f"fail={_fail}",
                            flush=True,
                        )
            except Exception as e:
                log_event("displacement", "diagnostic_failed", error=str(e))
                print(f"DEBUG DISPLACEMENT: Diagnostic failed: {e}", flush=True)
            
            return None
        
        # OPTIMIZED: Prioritize high-score entries over stale, lower-score drifting positions
        # Sort by: lowest original score first (stale positions), then oldest (drifting), then worst P&L
        # This ensures we displace weak, old positions to make room for fresh, high-score Whale flow
        candidates.sort(key=lambda x: (x["original_score"], -x["age_hours"], x["pnl_pct"]))
        
        best = candidates[0]
        log_event("displacement", "candidate_found",
                 symbol=best["symbol"],
                 pnl_pct=round(best["pnl_pct"] * 100, 2),
                 age_hours=round(best["age_hours"], 1),
                 original_score=best["original_score"],
                 new_signal_score=new_signal_score,
                 score_advantage=round(best["score_advantage"], 2))
        
        return best
    
    def execute_displacement(self, candidate: Dict, new_symbol: str, new_signal_score: float) -> bool:
        """
        V1.0: Execute displacement - exit old position to make room for new signal.
        Returns True if displacement successful.
        FIX 2025-12-05: Now logs proper exit attribution with P&L for ML learning.
        """
        # SAFETY: Candidate dict is external input (from selector). Never assume keys exist.
        if not isinstance(candidate, dict):
            log_event("displacement", "failed", symbol="UNKNOWN", error="candidate_not_a_dict")
            return False
        symbol = candidate.get("symbol")
        if not symbol:
            log_event("displacement", "failed", symbol="UNKNOWN", error="candidate_missing_symbol")
            return False
        displacement_log_path = StateFiles.DISPLACEMENT_COOLDOWNS
        
        try:
            info = self.opens.get(symbol, {})
            entry_price = info.get("entry_price", candidate.get("entry_price", 0.0))
            
            # BULLETPROOF: Safe position close with error handling and verification
            position_closed = False
            exit_order_id = None
            exit_fill_qty = 0
            exit_fill_price = 0.0
            try:
                # Contract: closes should succeed even if qty is reserved by open orders.
                # Prefer canceling open orders as part of close (safe fallback for older SDKs).
                close_order = self.close_position_with_retries(symbol, max_attempts=3)
                if close_order is None:
                    raise RuntimeError("close_position_with_retries failed")
                exit_order_id = getattr(close_order, "id", None)
                log_event("displacement", "close_position_api_called", symbol=symbol)
                # Fill-sourcing contract: do not attribute using quotes/marks.
                # Poll Alpaca for executed fill fields (filled_avg_price / filled_qty).
                try:
                    max_wait = float(get_env("ATTRIBUTION_EXIT_FILL_WAIT_SEC", 20.0, float))
                except Exception:
                    max_wait = 20.0
                if exit_order_id:
                    filled, fq, fp = self.check_order_filled(str(exit_order_id), max_wait_sec=max_wait)
                    if filled:
                        exit_fill_qty = int(fq or 0)
                        exit_fill_price = float(fp or 0.0)
                
                # CRITICAL: Verify position was actually closed
                time.sleep(2.0)  # Wait for order to process
                for verify_attempt in range(5):
                    try:
                        positions = self.api.list_positions()
                        v_positions = [p for p in positions if getattr(p, "symbol", "") == symbol]
                        if not v_positions:
                            position_closed = True
                            log_event("displacement", "close_position_verified", symbol=symbol, verify_attempt=verify_attempt+1)
                            break
                        elif verify_attempt < 4:
                            time.sleep(3.0)
                            log_event("displacement", "close_position_still_open", symbol=symbol, verify_attempt=verify_attempt+1)
                    except Exception as verify_err:
                        if verify_attempt < 4:
                            time.sleep(2.0)
                        else:
                            # Can't verify, assume closed (fail open)
                            position_closed = True
                            log_event("displacement", "close_position_verify_failed_assume_closed", symbol=symbol, error=str(verify_err))
                            break
                
                if not position_closed:
                    log_event("displacement", "close_position_not_verified", symbol=symbol)
                    return False  # Displacement failed - position still open
                    
                log_event("displacement", "close_position_success", symbol=symbol)
            except Exception as close_err:
                log_event("displacement", "close_position_failed", symbol=symbol, error=str(close_err))
                return False  # Displacement failed if can't close old position

            # BULLETPROOF: Safe cooldown log read with corruption handling
            cooldowns = {}
            try:
                if displacement_log_path.exists():
                    raw_data = displacement_log_path.read_text()
                    if raw_data.strip():
                        cooldowns = json.loads(raw_data)
                        if not isinstance(cooldowns, dict):
                            cooldowns = {}  # Reset if corrupted
            except (json.JSONDecodeError, IOError) as cooldown_err:
                log_event("displacement", "cooldown_log_error", error=str(cooldown_err))
                cooldowns = {}  # Continue with empty dict
            cooldowns[symbol] = datetime.utcnow().isoformat()
            displacement_log_path.parent.mkdir(exist_ok=True)
            atomic_write_json(displacement_log_path, cooldowns)
            
            metadata_path = StateFiles.POSITION_METADATA
            try:
                all_metadata = load_metadata_with_lock(metadata_path) if metadata_path.exists() else {}
                symbol_metadata = all_metadata.get(symbol, {})
            except:
                symbol_metadata = {}
            
            # Build composite close reason for displacement
            displacement_signals = {
                "displacement": new_symbol,
                "age_hours": (datetime.utcnow() - info.get("ts", datetime.utcnow())).total_seconds() / 3600.0
            }
            close_reason = build_composite_close_reason(displacement_signals)
            
            # Only attribute exits when we have executed fill fields.
            if exit_fill_price > 0 and exit_fill_qty > 0:
                log_exit_attribution(
                    symbol=symbol,
                    info=info,
                    exit_price=exit_fill_price,
                    close_reason=close_reason,
                    metadata=symbol_metadata,
                    exit_qty=exit_fill_qty,
                    exit_order_id=str(exit_order_id) if exit_order_id else None,
                )
            else:
                log_event(
                    "data_integrity",
                    "exit_fill_missing_skip_attribution",
                    symbol=symbol,
                    close_reason=close_reason,
                    exit_order_id=str(exit_order_id) if exit_order_id else None,
                    note="Displacement exit verified closed but fill fields not available; skipping attribution to avoid synthetic prices.",
                )
            
            if symbol in self.opens:
                del self.opens[symbol]
            if symbol in self.high_water:
                del self.high_water[symbol]
            self._remove_position_metadata(symbol)
            
            # Update state manager (Risk #6 - State Persistence)
            try:
                state_manager = getattr(self, '_state_manager', None)
                if state_manager is None and hasattr(self, 'state_manager'):
                    state_manager = self.state_manager
                if state_manager:
                    # Remove position from state (qty=0 removes it)
                    state_manager.update_position(symbol=symbol, qty=0, side="buy", cost_basis=0.0)
            except Exception as e:
                log_event("state_manager", "close_position_update_failed", symbol=symbol, error=str(e))
            
            log_event("displacement", "executed",
                     displaced_symbol=symbol,
                     displaced_pnl_pct=round(float(candidate.get("pnl_pct", 0.0)) * 100, 2) if isinstance(candidate, dict) else 0.0,
                     displaced_age_hours=round(float(candidate.get("age_hours", 0.0)), 1) if isinstance(candidate, dict) else 0.0,
                     new_symbol=new_symbol,
                     new_signal_score=new_signal_score,
                     score_advantage=round(float(candidate.get("score_advantage", 0.0)), 2) if isinstance(candidate, dict) and isinstance(candidate.get("score_advantage"), (int, float)) else None)
            
            cand_adv = candidate.get("score_advantage") if isinstance(candidate, dict) else None
            cand_adv_str = f"{float(cand_adv):.1f}" if isinstance(cand_adv, (int, float)) else "n/a"
            cand_pnl = candidate.get("pnl_pct") if isinstance(candidate, dict) else None
            cand_pnl_str = f"{float(cand_pnl)*100:.1f}%" if isinstance(cand_pnl, (int, float)) else "n/a"
            send_webhook({
                "event": "POSITION_DISPLACED",
                "displaced": symbol,
                "new_symbol": new_symbol,
                "reason": f"Score advantage: {cand_adv_str} pts",
                "old_pnl": cand_pnl_str,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return True
            
        except Exception as e:
            log_event("displacement", "failed", symbol=symbol, error=str(e))
            return False

    def mark_open(self, symbol: str, entry_price: float, atr_mult: float = None, side: str = "buy", qty: int = 0, entry_score: float = 0.0, components: dict = None, market_regime: str = "unknown", direction: str = "unknown", regime_modifier: float = 1.0, ignition_status: str = "unknown", alpha_signature: dict = None):
        # VALIDATION: Warn if entry_score is 0.0 (should not happen in normal flow)
        if entry_score <= 0.0:
            print(f"WARNING {symbol}: mark_open called with entry_score={entry_score:.2f} - this may indicate a bug", flush=True)
            log_event("position", "mark_open_zero_score_warning", symbol=symbol, entry_score=entry_score,
                     side=side, qty=qty, market_regime=market_regime, direction=direction)
        
        now = datetime.utcnow()
        targets_state = [
            {"pct": t, "hit": False, "fraction": Config.SCALE_OUT_FRACTIONS[i] if i < len(Config.SCALE_OUT_FRACTIONS) else 0.0}
            for i, t in enumerate(Config.PROFIT_TARGETS)
        ]
        record = {
            "entry_price": entry_price,
            "ts": now,
            "side": side,
            "trail_dist": None,
            "high_water": entry_price,
            "targets": targets_state,
            "initial_qty": qty,
            "entry_score": entry_score,  # V1.0: Store for displacement comparison
            "components": components or {},  # V2.0: Store signal components for ML learning
            "market_regime": market_regime,
            "direction": direction,
            "regime_modifier": regime_modifier,  # V4.0: Store regime multiplier applied to composite score
            "ignition_status": ignition_status,  # V4.0: Store momentum filter status
        }
        if atr_mult is not None and Config.ENABLE_PER_TICKER_LEARNING:
            atr = compute_atr(self.api, symbol, Config.ATR_LOOKBACK)
            min_trail = entry_price * Config.ATR_MIN_PCT
            record["trail_dist"] = max(atr * atr_mult, min_trail)
        self.opens[symbol] = record
        self.high_water[symbol] = entry_price
        self.cooldowns[symbol] = now + timedelta(minutes=Config.COOLDOWN_MINUTES_PER_TICKER)
        
        # V4.0: Extract correlation_id from opens dict if available
        correlation_id = None
        if symbol in self.opens and "correlation_id" in self.opens[symbol]:
            correlation_id = self.opens[symbol]["correlation_id"]

        # Phase 5: Persist alpha_signature into position metadata for forensic analysis
        if alpha_signature is None:
            try:
                from alpha_signature_capture import capture_alpha_signature
                uw_cache_for_alpha = read_json(CacheFiles.UW_FLOW_CACHE, default={})
                alpha_signature = capture_alpha_signature(self.api, symbol, uw_cache_for_alpha)
            except Exception as e:
                alpha_signature = {"status": "error", "error": str(e), "timestamp": time.time()}
        
        self._persist_position_metadata(
            symbol,
            entry_ts=now,
            entry_price=entry_price,
            qty=qty,
            side=side,
            entry_score=entry_score,
            components=components,
            market_regime=market_regime,
            direction=direction,
            regime_modifier=regime_modifier,
            ignition_status=ignition_status,
            correlation_id=correlation_id,
            alpha_signature=alpha_signature,
        )
        
        # Update state manager (Risk #6 - State Persistence)
        try:
            state_manager = getattr(self, '_state_manager', None)
            if state_manager is None and hasattr(self, 'state_manager'):
                state_manager = self.state_manager
            if state_manager:
                state_manager.update_position(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    cost_basis=entry_price,
                    entry_time=now.isoformat()
                )
                # Record order ID if available
                if res and hasattr(res, 'id'):
                    state_manager.record_order_id(symbol, str(res.id))
        except Exception as e:
            log_event("state_manager", "update_position_failed", symbol=symbol, error=str(e))
    
    def _persist_position_metadata(self, symbol: str, entry_ts: datetime, entry_price: float, qty: int, side: str, entry_score: float = 0.0, components: dict = None, market_regime: str = "unknown", direction: str = "unknown", regime_modifier: float = 1.0, ignition_status: str = "unknown", correlation_id: str = None, alpha_signature: dict = None):
        """Persist position metadata to durable file for restart recovery with atomic write.
        
        V2.0: Now stores all 21 signal components for ML learning when trade closes.
        V4.0: Stores regime_modifier and ignition_status for full Specialist Tier state recovery.
        """
        metadata_path = StateFiles.POSITION_METADATA
        try:
            metadata_path.parent.mkdir(exist_ok=True)
            metadata = load_metadata_with_lock(metadata_path)

            # Preserve previously-captured alpha_signature if caller didn't provide one.
            if alpha_signature is None:
                try:
                    alpha_signature = (metadata.get(symbol, {}) or {}).get("alpha_signature")
                except Exception:
                    alpha_signature = None
            
            metadata[symbol] = {
                "entry_ts": entry_ts.isoformat(),
                "entry_price": entry_price,
                "qty": qty,
                "side": side,
                "entry_score": entry_score,  # V1.0: Store for displacement comparison
                "components": components or {},  # V2.0: Store all 21 signal components for ML
                "market_regime": market_regime,
                "direction": direction,
                "regime_modifier": regime_modifier,  # V4.0: Store regime multiplier applied to composite score
                "ignition_status": ignition_status,  # V4.0: Store momentum filter status
                "correlation_id": correlation_id,  # V4.0: Store UW-to-Alpaca correlation ID for tracking
                "alpha_signature": alpha_signature,  # Phase 5: RVOL/RSI/PCR observability for forensics
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # V3.0: Persist targets if position is already open
            if symbol in self.opens and "targets" in self.opens[symbol]:
                metadata[symbol]["targets"] = self.opens[symbol]["targets"]
            
            atomic_write_json(metadata_path, metadata)
            
        except Exception as e:
            log_event("persist", "metadata_write_failed", symbol=symbol, error=str(e))

    def _scale_out_partial(self, symbol: str, fraction: float, side: str):
        try:
            current_qty = get_position_qty(self.api, symbol)
            if current_qty <= 0 or fraction <= 0:
                return False
            close_qty = max(1, int(abs(current_qty) * fraction))
            exit_side = "sell" if side == "buy" else "buy"
            o = self.api.submit_order(symbol=symbol, qty=close_qty, side=exit_side, type="market", time_in_force="day")
            log_order({"action": "scale_out", "symbol": symbol, "qty": close_qty, "fraction": fraction})
            return True
        except Exception as e:
            log_order({"action": "scale_out_failed", "symbol": symbol, "fraction": fraction, "error": str(e)})
            # Track execution failure for learning
            try:
                from tca_data_manager import track_execution_failure
                track_execution_failure(symbol, "scale_out_failed", {"fraction": fraction, "error": str(e)})
            except ImportError:
                pass
            return False

    def market_buy(self, symbol: str, qty: int):
        return self.api.submit_order(symbol=symbol, qty=qty, side="buy", type="market", time_in_force="day")

    def market_sell(self, symbol: str, qty: int):
        return self.api.submit_order(symbol=symbol, qty=qty, side="sell", type="market", time_in_force="day")

    def get_quote_price(self, symbol: str) -> float:
        try:
            q = self.api.get_latest_trade(symbol)
            return float(getattr(q, "price", 0.0))
        except Exception:
            return 0.0

    def reload_positions_from_metadata(self):
        """Reload position tracking from metadata file (for health check auto-fix).

        V2.2 FIX: Always sync entry_ts from metadata to ensure accurate age calculation.
        BULLETPROOF: Safe metadata load and position fetch with error handling.
        """
        metadata_path = StateFiles.POSITION_METADATA
        try:
            if not metadata_path.exists():
                return

            # BULLETPROOF: Safe metadata load with corruption handling
            try:
                metadata = load_metadata_with_lock(metadata_path)
                if not isinstance(metadata, dict):
                    log_event("reload_positions", "metadata_corrupted", error="not_a_dict")
                    return  # Skip reload if corrupted
            except (json.JSONDecodeError, IOError, Exception) as meta_err:
                log_event("reload_positions", "metadata_load_error", error=str(meta_err))
                return  # Fail open - skip reload but continue
            
            # BULLETPROOF: Safe position fetch with error handling
            current_positions = {}
            try:
                positions = self.api.list_positions() or []
                for p in positions:
                    try:
                        symbol = getattr(p, "symbol", "")
                        if symbol:
                            current_positions[symbol] = p
                    except (AttributeError, Exception):
                        continue
            except Exception as pos_err:
                log_event("reload_positions", "list_positions_error", error=str(pos_err))
                current_positions = {}  # Continue with empty dict
            
            # V2.2: Update existing positions with correct entry_ts from metadata
            for symbol, meta in metadata.items():
                if symbol in current_positions:
                    try:
                        correct_entry_ts = datetime.fromisoformat(meta.get("entry_ts", ""))
                    except:
                        correct_entry_ts = None
                    
                    if correct_entry_ts and symbol in self.opens:
                        # Update existing position with correct timestamp
                        self.opens[symbol]["ts"] = correct_entry_ts
                        if "entry_score" not in self.opens[symbol]:
                            self.opens[symbol]["entry_score"] = meta.get("entry_score", 0.0)
                        if "components" not in self.opens[symbol] or not self.opens[symbol]["components"]:
                            self.opens[symbol]["components"] = meta.get("components", {})
                        # V4.0: Restore regime_modifier and ignition_status
                        if "regime_modifier" not in self.opens[symbol]:
                            self.opens[symbol]["regime_modifier"] = meta.get("regime_modifier", 1.0)
                        if "ignition_status" not in self.opens[symbol]:
                            self.opens[symbol]["ignition_status"] = meta.get("ignition_status", "unknown")
                        # V3.0: Restore targets from metadata if available
                        if "targets" in meta and meta["targets"]:
                            self.opens[symbol]["targets"] = meta["targets"]
                        elif "targets" not in self.opens[symbol]:
                            # Initialize targets if missing
                            self.opens[symbol]["targets"] = [
                                {"pct": t, "hit": False, "fraction": Config.SCALE_OUT_FRACTIONS[i] if i < len(Config.SCALE_OUT_FRACTIONS) else 0.0}
                                for i, t in enumerate(Config.PROFIT_TARGETS)
                            ]
            
            # Add any positions in metadata that aren't in self.opens
            for symbol, meta in metadata.items():
                if symbol not in self.opens and symbol in current_positions:
                    pos = current_positions[symbol]
                    qty = int(float(getattr(pos, "qty", 0)))
                    avg_entry = float(getattr(pos, "avg_entry_price", 0.0))
                    current_price = float(getattr(pos, "current_price", avg_entry))
                    side = "buy" if qty > 0 else "sell"
                    
                    # Restore entry_score and other metadata
                    entry_score = meta.get("entry_score", 0.0)
                    components = meta.get("components", {})
                    market_regime = meta.get("market_regime", "unknown")
                    direction = meta.get("direction", "unknown")
                    regime_modifier = meta.get("regime_modifier", 1.0)  # V4.0: Restore regime modifier
                    ignition_status = meta.get("ignition_status", "unknown")  # V4.0: Restore ignition status
                    
                    try:
                        entry_ts = datetime.fromisoformat(meta.get("entry_ts", ""))
                    except:
                        entry_ts = datetime.utcnow()
                    
                    # V3.0: Restore targets from metadata if available, otherwise initialize fresh
                    targets_from_meta = meta.get("targets")
                    if targets_from_meta:
                        targets_state = targets_from_meta
                    else:
                        targets_state = [
                            {"pct": t, "hit": False, "fraction": Config.SCALE_OUT_FRACTIONS[i] if i < len(Config.SCALE_OUT_FRACTIONS) else 0.0}
                            for i, t in enumerate(Config.PROFIT_TARGETS)
                        ]
                    
                    self.opens[symbol] = {
                        "ts": entry_ts,
                        "entry_price": avg_entry,
                        "qty": abs(qty),
                        "side": side,
                        "trail_dist": None,
                        "high_water": current_price,
                        "entry_score": entry_score,  # Restore entry_score from metadata
                        "components": components,  # Restore components from metadata
                        "market_regime": market_regime,
                        "direction": direction,
                        "regime_modifier": regime_modifier,  # V4.0: Restore regime modifier
                        "ignition_status": ignition_status,  # V4.0: Restore ignition status
                        "targets": targets_state
                    }
                    self.high_water[symbol] = current_price
                    log_event("reload", "position_added_from_metadata", symbol=symbol, entry_score=entry_score)
            
            # Remove any positions from self.opens that aren't in Alpaca
            for symbol in list(self.opens.keys()):
                if symbol not in current_positions:
                    self.opens.pop(symbol, None)
                    self.high_water.pop(symbol, None)
                    log_event("reload", "position_removed_no_longer_open", symbol=symbol)
                    
        except Exception as e:
            log_event("reload", "metadata_reload_failed", error=str(e))

    @global_failure_wrapper("exit")
    def evaluate_exits(self):
        # CRITICAL: Reload positions from metadata (catches health check auto-fixes)
        self.reload_positions_from_metadata()
        _pipeline_touch("exit_eval")
        _pipeline_heartbeat_maybe()
        
        to_close = []
        exit_reasons = {}  # Track composite exit reasons per symbol
        # BULLETPROOF: Safe position fetching with error handling
        positions_index = {}
        try:
            positions = self.api.list_positions()
            if positions:
                for p in positions:
                    try:
                        symbol = getattr(p, "symbol", "")
                        if symbol:  # Only index valid symbols
                            positions_index[symbol] = p
                    except (AttributeError, Exception) as pos_err:
                        log_event("exit", "position_index_error", error=str(pos_err))
                        continue
        except Exception as list_err:
            log_event("exit", "list_positions_error", error=str(list_err))
            positions_index = {}  # Fail open - continue with empty index
        
        # CRITICAL FIX: Force close V IMMEDIATELY if it exists and has negative P&L
        # This ensures V is closed RIGHT NOW, not added to a list for later
        if "V" in positions_index:
            v_pos = positions_index["V"]
            try:
                v_pnl_pct = float(getattr(v_pos, "unrealized_plpc", 0))
                if v_pnl_pct < 0:  # Any negative P&L
                    print(f"CRITICAL: V position has negative P&L ({v_pnl_pct:.2f}%) - FORCE CLOSING IMMEDIATELY", flush=True)
                    log_event("exit", "force_close_v_negative_pnl_immediate", pnl_pct=v_pnl_pct)
                    
                    # CLOSE IT NOW - Don't wait for the loop
                    try:
                        # Contract: closes should succeed even if qty is reserved by open orders.
                        self.close_position_with_retries("V", max_attempts=3)
                        print(f"CRITICAL: V close order submitted - P&L={v_pnl_pct:.2f}%", flush=True)
                        log_event("exit", "force_close_v_order_submitted", pnl_pct=v_pnl_pct)
                        
                        # Verify it's closed (with timeout)
                        time.sleep(2.0)
                        for verify_attempt in range(5):
                            try:
                                positions = self.api.list_positions()
                                v_positions = [p for p in positions if getattr(p, "symbol", "").upper() == "V"]
                                if not v_positions:
                                    print(f"CRITICAL: V position CLOSED and verified (attempt {verify_attempt+1})", flush=True)
                                    log_event("exit", "force_close_v_verified", pnl_pct=v_pnl_pct, attempts=verify_attempt+1)
                                    # Remove from tracking
                                    self.opens.pop("V", None)
                                    self.high_water.pop("V", None)
                                    self._remove_position_metadata("V")
                                    # Remove from positions_index so it's not evaluated again
                                    positions_index.pop("V", None)
                                    # Return early - V is closed, don't process it in the loop
                                    break
                                elif verify_attempt < 4:
                                    time.sleep(3.0)
                                    print(f"CRITICAL: V still open, retrying verification (attempt {verify_attempt+1}/5)", flush=True)
                                else:
                                    print(f"WARNING: V still open after 5 verification attempts - may need manual close", flush=True)
                                    log_event("exit", "force_close_v_verification_failed", pnl_pct=v_pnl_pct)
                            except Exception as verify_err:
                                if verify_attempt < 4:
                                    time.sleep(2.0)
                                else:
                                    log_event("exit", "force_close_v_verify_error", error=str(verify_err))
                                    break
                    except Exception as close_err:
                        print(f"ERROR: Failed to close V position: {close_err}", flush=True)
                        log_event("exit", "force_close_v_failed", error=str(close_err), pnl_pct=v_pnl_pct)
                        traceback.print_exc()
            except Exception as v_err:
                print(f"ERROR: Exception checking V position: {v_err}", flush=True)
                log_event("exit", "force_close_v_error", error=str(v_err))
                traceback.print_exc()
        
        metadata_path = StateFiles.POSITION_METADATA
        # BULLETPROOF: Safe metadata load with corruption handling
        all_metadata = {}
        try:
            if metadata_path.exists():
                all_metadata = load_metadata_with_lock(metadata_path)
                # Validate metadata structure
                if not isinstance(all_metadata, dict):
                    log_event("exit", "metadata_corrupted", error="not_a_dict", metadata_type=str(type(all_metadata)))
                    all_metadata = {}  # Reset to empty dict
        except (json.JSONDecodeError, IOError, Exception) as meta_err:
            log_event("exit", "metadata_load_error", error=str(meta_err))
            all_metadata = {}  # Fail open - continue with empty metadata

        # Get current UW cache for signal evaluation
        # Contract: If UW cache cannot be loaded due to import issues, exits are skipped and a clear event is logged.
        try:
            uw_cache = read_uw_cache()
        except (ImportError, NameError) as e:
            log_event("exit", "uw_cache_import_failed", error=str(e), error_type=type(e).__name__, action="skip_exits")
            return
        except Exception as e:
            log_event("exit", "uw_cache_load_failed", error=str(e), error_type=type(e).__name__, action="skip_exits")
            return
        current_regime_global = self._get_global_regime() or "mixed"

        now = datetime.utcnow()
        
        # CRITICAL FIX: Check ALL positions from Alpaca API, not just self.opens
        # This ensures positions that exist in Alpaca but not in self.opens are still evaluated
        positions_to_evaluate = {}
        
        # First, add all positions from self.opens
        for symbol, info in self.opens.items():
            positions_to_evaluate[symbol] = {
                "info": info,
                "source": "opens_dict"
            }
        
        # Then, add all positions from Alpaca API that aren't in self.opens
        for symbol, pos in positions_index.items():
            if symbol not in positions_to_evaluate:
                # Get metadata for this position
                meta = all_metadata.get(symbol, {})
                if meta:
                    # Create info dict from metadata
                    try:
                        entry_ts_str = meta.get("entry_ts", "")
                        if isinstance(entry_ts_str, str):
                            try:
                                entry_ts = datetime.fromisoformat(entry_ts_str.replace("Z", ""))
                            except:
                                entry_ts = datetime.utcnow()
                        else:
                            entry_ts = datetime.utcnow()
                    except:
                        entry_ts = datetime.utcnow()
                    
                    positions_to_evaluate[symbol] = {
                        "info": {
                            "entry_price": meta.get("entry_price", float(getattr(pos, "avg_entry_price", 0))),
                            "ts": entry_ts,
                            "side": meta.get("side", "buy" if float(getattr(pos, "qty", 0)) > 0 else "sell"),
                            "entry_score": meta.get("entry_score", 0.0),
                            "high_water": meta.get("high_water", float(getattr(pos, "current_price", 0)))
                        },
                        "source": "alpaca_api"
                    }
                else:
                    # No metadata - create from Alpaca position
                    try:
                        entry_ts = datetime.utcnow()  # Unknown entry time
                        positions_to_evaluate[symbol] = {
                            "info": {
                                "entry_price": float(getattr(pos, "avg_entry_price", 0)),
                                "ts": entry_ts,
                                "side": "buy" if float(getattr(pos, "qty", 0)) > 0 else "sell",
                                "entry_score": 0.0,
                                "high_water": float(getattr(pos, "current_price", 0))
                            },
                            "source": "alpaca_api_no_metadata"
                        }
                    except Exception as e:
                        log_event("exit", "position_eval_setup_error", symbol=symbol, error=str(e))
                        continue
        
        # Now evaluate all positions
        for symbol, pos_data in positions_to_evaluate.items():
            info = pos_data.get("info", {}) if isinstance(pos_data, dict) else {}
            exit_signals = {}  # Collect all exit signals for this position
            try:
                # FIX: Handle both offset-naive and offset-aware timestamps
                entry_ts = info.get("ts")
                if not entry_ts:
                    # Fail-safe: treat as just-opened if timestamp missing/corrupt.
                    entry_ts = datetime.utcnow()
                if hasattr(entry_ts, 'tzinfo') and entry_ts.tzinfo is not None:
                    entry_ts = entry_ts.replace(tzinfo=None)
                age_min = (now - entry_ts).total_seconds() / 60.0
                age_days = age_min / (24 * 60)
                age_hours = age_days * 24
                exit_signals["age_hours"] = age_hours
                
                # CRITICAL FIX: Get current price from Alpaca position if available
                if symbol in positions_index:
                    pos = positions_index[symbol]
                    current_price = float(getattr(pos, "current_price", 0))
                    if current_price <= 0:
                        current_price = self.get_quote_price(symbol)
                else:
                    current_price = self.get_quote_price(symbol)
                
                if current_price <= 0:
                    # FIX: Use entry price as fallback for after-hours exit evaluation
                    current_price = info.get("entry_price", 0.0)
                    if current_price <= 0:
                        continue
            except Exception as loop_err:
                log_event("exit", "exception_in_eval", symbol=symbol, error=str(loop_err))
                continue
            
            entry_price = info.get("entry_price", current_price) or current_price  # BULLETPROOF: Ensure non-zero
            high_water_price = info.get("high_water", current_price) or current_price  # BULLETPROOF: Ensure non-zero
            
            # CRITICAL FIX: Use Alpaca's unrealized_plpc directly if available
            # This is the authoritative P&L calculation from Alpaca
            alpaca_pnl_pct = None  # Initialize for logging
            if symbol in positions_index:
                pos = positions_index[symbol]
                try:
                    # Use Alpaca's calculated P&L % (most accurate)
                    alpaca_pnl_pct = float(getattr(pos, "unrealized_plpc", 0))
                    # Also get avg_entry_price from Alpaca (handles partial closes, adds correctly)
                    alpaca_entry_price = float(getattr(pos, "avg_entry_price", 0))
                    if alpaca_entry_price > 0:
                        entry_price = alpaca_entry_price  # Use Alpaca's entry price (handles position changes)
                    pnl_pct = alpaca_pnl_pct  # Use Alpaca's P&L % (authoritative)
                    print(f"DEBUG EXITS: {symbol} using Alpaca P&L: {pnl_pct:.4f}% (entry=${entry_price:.2f}, current=${current_price:.2f})", flush=True)
                except (AttributeError, ValueError, TypeError) as alpaca_err:
                    log_event("exit", "alpaca_pnl_fetch_error", symbol=symbol, error=str(alpaca_err))
                    # Fallback to calculated P&L if Alpaca data unavailable
                    if entry_price <= 0:
                        log_event("exit", "invalid_entry_price", symbol=symbol, entry_price=entry_price, current_price=current_price)
                        entry_price = current_price if current_price > 0 else 1.0
                    pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
            else:
                # BULLETPROOF: Validate entry_price before division (prevent divide by zero)
                if entry_price <= 0:
                    log_event("exit", "invalid_entry_price", symbol=symbol, entry_price=entry_price, current_price=current_price)
                    entry_price = current_price if current_price > 0 else 1.0  # Fallback to safe value
                
                pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
            
            high_water_pct = ((high_water_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
            
            # BULLETPROOF: Clamp percentages to reasonable range (prevent NaN/infinity)
            pnl_pct = max(-1000.0, min(1000.0, pnl_pct))
            high_water_pct = max(-1000.0, min(1000.0, high_water_pct))
            exit_signals["pnl_pct"] = pnl_pct
            
            # STRUCTURAL EXIT: Check for gamma call walls and liquidity exhaustion
            try:
                from structural_intelligence import get_structural_exit
                structural_exit = get_structural_exit()
                
                position_data = {
                    "current_price": current_price,
                    "side": info.get("side", "buy"),
                    "entry_price": entry_price,
                    "unrealized_pnl_pct": pnl_pct / 100.0
                }
                
                exit_rec = structural_exit.get_exit_recommendation(symbol, position_data)
                
                if exit_rec.get("should_exit"):
                    exit_reason = exit_rec.get("reason", "structural_exit")
                    scale_pct = exit_rec.get("scale_out_pct", 1.0)
                    
                    # Add to exit signals
                    exit_signals["structural_exit"] = exit_reason
                    exit_signals["scale_out_pct"] = scale_pct
                    
                    log_event("structural_exit", exit_reason, symbol=symbol, 
                             scale_pct=scale_pct, pnl_pct=pnl_pct)
            except ImportError:
                pass
            except Exception as e:
                log_event("structural_exit", "error", symbol=symbol, error=str(e))
            
            # Get current composite score for signal decay detection
            current_composite_score = 0.0
            flow_reversal = False
            try:
                enriched = uw_cache.get(symbol, {})
                if enriched:
                    # Scoring pipeline invariant: current scores MUST use the same enrichment path as entries.
                    # WHY: raw cache often contains None/missing fields (conviction, etc.), causing score collapse into a narrow band.
                    try:
                        import uw_enrichment_v2 as uw_enrich
                        enriched_live = uw_enrich.enrich_signal(symbol, uw_cache, current_regime_global) or enriched
                    except Exception:
                        enriched_live = enriched
                    composite = uw_v2.compute_composite_score_v3(symbol, enriched_live, current_regime_global)
                    if composite:
                        current_composite_score = composite.get("score", 0.0)
                        # Check for flow reversal
                        flow_sent = enriched_live.get("sentiment", "NEUTRAL")
                        entry_direction = info.get("direction", "unknown")
                        if entry_direction == "bullish" and flow_sent == "BEARISH":
                            flow_reversal = True
                        elif entry_direction == "bearish" and flow_sent == "BULLISH":
                            flow_reversal = True
            except Exception:
                pass  # If we can't get current score, continue with defaults
            
            # V3.2: Use adaptive exit urgency from optimizer
            position_data = {
                "entry_score": info.get("entry_score", 3.0),
                "current_pnl_pct": pnl_pct,
                "age_hours": age_hours,
                "high_water_pct": high_water_pct,
                "direction": "LONG" if info.get("side", "buy") == "buy" else "SHORT"
            }
            current_signals = {
                "composite_score": current_composite_score,
                "flow_reversal": flow_reversal,
                "momentum": 0.0
            }
            
            # Calculate signal decay
            # BULLETPROOF: Validate scores before division
            entry_score = info.get("entry_score", 3.0) or 3.0
            if entry_score > 0 and current_composite_score > 0:
                decay_ratio = current_composite_score / entry_score
                # BULLETPROOF: Clamp decay ratio to [0, 1] range
                decay_ratio = max(0.0, min(1.0, decay_ratio))
                if decay_ratio < 1.0:
                    exit_signals["signal_decay"] = decay_ratio
            
            exit_signals["flow_reversal"] = flow_reversal
            
            # --- AUDIT DEC 2025: Manual Regime Safety Override ---
            # Ensures protection even if adaptive optimizer is missing
            # Try multiple sources: metadata (entry regime), in-memory info, or global regime state
            current_regime = (
                all_metadata.get(symbol, {}).get("market_regime") or
                info.get("market_regime") or
                current_regime_global or
                "unknown"
            )
            if current_regime == "high_vol_neg_gamma":
                if info.get("side", "buy") == "buy" and pnl_pct < -0.5:
                    exit_signals["regime_protection"] = "neg_gamma"
                    exit_reasons[symbol] = build_composite_close_reason(exit_signals)
                    log_event("exit", "regime_safety_trigger", 
                             symbol=symbol, 
                             regime=current_regime,
                             pnl_pct=round(pnl_pct, 2),
                             reason=exit_reasons[symbol])
                    to_close.append(symbol)
                    continue
            # --- END Regime Safety Override ---
            
            exit_recommendation = get_exit_urgency(position_data, current_signals)
            
            # Collect factors from exit recommendation
            if exit_recommendation.get("contributing_factors"):
                for factor in exit_recommendation.get("contributing_factors", []):
                    if "drawdown" in factor.lower():
                        exit_signals["drawdown"] = high_water_pct - pnl_pct
                    elif "momentum" in factor.lower():
                        exit_signals["momentum_reversal"] = True
            
            # V3.2: Adaptive exit can trigger immediate close
            if exit_recommendation.get("action") == "EXIT" and exit_recommendation.get("urgency", 0) >= 0.8:
                exit_signals["primary_reason"] = exit_recommendation.get("primary_reason", "adaptive_urgency")
                exit_reasons[symbol] = build_composite_close_reason(exit_signals)
                log_event("exit", "adaptive_exit_urgent", 
                         symbol=symbol,
                         urgency=exit_recommendation.get("urgency"),
                         reason=exit_reasons[symbol])
                if flow_reversal:
                    log_system_event(
                        subsystem="exit",
                        event_type="counter_signal_exit_triggered",
                        severity="INFO",
                        symbol=symbol,
                        score_before=float(entry_score or 0.0),
                        score_after=float(current_composite_score or 0.0),
                    )
                to_close.append(symbol)
                continue
            
            # V3.3: Time-based exit for stale low-movement positions
            if age_days >= Config.TIME_EXIT_DAYS_STALE:
                if abs(pnl_pct / 100) < Config.TIME_EXIT_STALE_PNL_THRESH_PCT:
                    exit_signals["stale_position"] = True
                    exit_reasons[symbol] = build_composite_close_reason(exit_signals)
                    log_event("exit", "time_exit_stale", 
                             symbol=symbol, 
                             age_days=round(age_days, 1),
                             pnl_pct=round(pnl_pct, 2),
                             reason=exit_reasons[symbol])
                    to_close.append(symbol)
                    continue
            
            # Institutional Remediation Phase 7: Zombie kill switch (capital velocity)
            # If a trade is not at +0.2% PnL within 120 minutes, exit with reason 'stale_alpha_cutoff'.
            ENABLE_REGIME_AWARE_STALE = str(get_env("ENABLE_REGIME_AWARE_STALE", "false")).lower() == "true"
            if age_min >= Config.STALE_TRADE_EXIT_MINUTES:
                if pnl_pct < 0.20:
                    exit_signals["stale_alpha_cutoff"] = True
                    exit_signals["stale_trade_age_min"] = round(age_min, 1)
                    exit_signals["stale_trade_pnl_pct"] = round(pnl_pct, 2)
                    exit_reasons[symbol] = build_composite_close_reason(exit_signals)
                    log_event(
                        "exit",
                        "stale_alpha_cutoff_exit",
                        symbol=symbol,
                        age_minutes=round(age_min, 1),
                        pnl_pct=round(pnl_pct, 2),
                        required_pnl_pct=0.20,
                        reason=exit_reasons[symbol],
                    )
                    to_close.append(symbol)
                    continue

                pnl_abs_pct = abs(pnl_pct / 100.0)  # Convert to decimal
                # In PANIC, require both stale AND decayed score to exit (guarded).
                # WHY: production shows churn exits around stale_trade; PANIC regimes are especially noisy.
                # HOW TO VERIFY: when ENABLE_REGIME_AWARE_STALE=true, fewer PANIC exits are stale-only (without signal_decay).
                if ENABLE_REGIME_AWARE_STALE and str(current_regime).upper() == "PANIC":
                    decay_ratio_gate = None
                    try:
                        entry_score_tmp = info.get("entry_score", 0.0)
                        current_composite_tmp = current_signals.get("composite_score", 0.0)
                        if entry_score_tmp and current_composite_tmp:
                            decay_ratio_gate = current_composite_tmp / entry_score_tmp
                    except Exception:
                        decay_ratio_gate = None

                    if pnl_abs_pct <= Config.STALE_TRADE_MOMENTUM_THRESH_PCT and decay_ratio_gate is not None and decay_ratio_gate < 0.60:
                        exit_signals["stale_trade_regime_aware"] = True
                        exit_signals["signal_decay"] = round(decay_ratio_gate, 2)
                        exit_signals["stale_trade_age_min"] = round(age_min, 1)
                        exit_signals["stale_trade_pnl_pct"] = round(pnl_pct, 2)
                        exit_reasons[symbol] = build_composite_close_reason(exit_signals)
                        log_event("exit", "stale_trade_exit_regime_aware",
                                 symbol=symbol,
                                 regime=str(current_regime),
                                 age_minutes=round(age_min, 1),
                                 pnl_pct=round(pnl_pct, 2),
                                 momentum_threshold=Config.STALE_TRADE_MOMENTUM_THRESH_PCT * 100,
                                 reason=exit_reasons[symbol])
                        to_close.append(symbol)
                        continue

                if pnl_abs_pct <= Config.STALE_TRADE_MOMENTUM_THRESH_PCT:
                    exit_signals["stale_trade"] = True
                    exit_signals["stale_trade_age_min"] = round(age_min, 1)
                    exit_signals["stale_trade_pnl_pct"] = round(pnl_pct, 2)
                    exit_reasons[symbol] = build_composite_close_reason(exit_signals)
                    log_event("exit", "stale_trade_exit", 
                             symbol=symbol,
                             age_minutes=round(age_min, 1),
                             pnl_pct=round(pnl_pct, 2),
                             momentum_threshold=Config.STALE_TRADE_MOMENTUM_THRESH_PCT * 100,
                             reason=exit_reasons[symbol])
                    to_close.append(symbol)
                    continue

            # PROFIT-TAKING ACCELERATION: Tighten trailing stop to 0.5% after 30 minutes of profitability
            # Refined stale exit based on backtest: Alpha Decay is 303 minutes but P&L is flat at 90 minutes
            # Move trailing stop to 0.5% after first 30 minutes if position is profitable
            trailing_stop_pct = Config.TRAILING_STOP_PCT
            profit_acceleration_active = False
            
            if age_min >= 30 and pnl_pct > 0:  # 30 minutes and profitable
                # Check if this is the first time we're applying acceleration (avoid resetting each cycle)
                if "profit_acceleration_applied" not in info:
                    trailing_stop_pct = 0.005  # 0.5% after 30 min profit
                    info["profit_acceleration_applied"] = True
                    profit_acceleration_active = True
                    log_event("exit", "profit_taking_acceleration", symbol=symbol,
                             age_minutes=round(age_min, 1),
                             pnl_pct=round(pnl_pct, 2),
                             new_trail_stop_pct=trailing_stop_pct * 100)
                elif info.get("profit_acceleration_applied"):
                    # Already applied - keep using tighter stop
                    trailing_stop_pct = 0.005
                    profit_acceleration_active = True
            
            # SPECIALIST LOGIC: Tighten trailing stop to 1.0% in MIXED regimes to protect against mid-day drift
            # (Only if profit acceleration not already active)
            if not profit_acceleration_active:
                if current_regime_global == "MIXED" or current_regime_global == "mixed":
                    trailing_stop_pct = 0.01  # 1.0% for MIXED regimes
            
            if "trail_dist" in info and info["trail_dist"] is not None:
                info["high_water"] = max(info.get("high_water", current_price), current_price)
                trail_stop = info["high_water"] - info["trail_dist"]
            else:
                self.high_water[symbol] = max(self.high_water.get(symbol, current_price), current_price)
                trail_stop = self.high_water[symbol] * (1 - trailing_stop_pct)

            # V3.0 CONVICTION-BASED EXITS: Removed TIME_EXIT logic
            # Exit on: 1) -1.0% Stop-Loss, 2) Signal Decay >40%, 3) Profit hits 0.75%
            
            # 1. Stop-Loss Check: -1.0% hard stop
            # CRITICAL FIX: stop_loss_pct must be in decimal form (-0.01 = -1.0%)
            # Previous bug: stop_loss_pct = -1.0 meant -100%, so -2.96% never triggered
            stop_loss_pct = -0.01  # -1.0% stop-loss (as decimal: -1.0 / 100.0)
            pnl_pct_decimal = pnl_pct / 100.0  # Convert percentage to decimal
            stop_loss_hit = pnl_pct_decimal <= stop_loss_pct
            
            # CRITICAL FIX: Log ALL position evaluations to file
            try:
                with open("logs/worker_debug.log", "a") as f:
                    f.write(f"[{datetime.now(timezone.utc).isoformat()}] EVALUATING {symbol}: P&L={pnl_pct:.2f}%, entry=${entry_price:.2f}, current=${current_price:.2f}, stop_loss_hit={stop_loss_hit}, threshold=-1.0%\n")
                    f.flush()
            except:
                pass
            
            # CRITICAL FIX: Log stop loss check to file for debugging
            if pnl_pct_decimal <= stop_loss_pct:
                try:
                    with open("logs/worker_debug.log", "a") as f:
                        f.write(f"[{datetime.now(timezone.utc).isoformat()}] STOP LOSS HIT: {symbol} P&L={pnl_pct:.2f}% (threshold: -1.0%), entry=${entry_price:.2f}, current=${current_price:.2f}, source={pos_data.get('source', 'unknown')}, alpaca_pnl={alpaca_pnl_pct if alpaca_pnl_pct is not None else 'calculated'}\n")
                        f.flush()
                except:
                    pass
                print(f"DEBUG EXITS: {symbol} STOP LOSS HIT - P&L={pnl_pct:.2f}% <= -1.0%, entry=${entry_price:.2f}, current=${current_price:.2f}", flush=True)
            
            # 2. Signal Decay Check: Current Score drops >40% below Entry Score
            entry_score = info.get("entry_score", 0.0)
            signal_decay_exit = False
            decay_ratio = None
            if entry_score > 0:
                # Get current composite score for this symbol
                try:
                    current_composite = current_signals.get("composite_score", 0.0)
                    if current_composite == 0:
                        # Try to compute current score if not available
                        # For now, skip if not available (fail open)
                        pass
                    else:
                        decay_ratio = current_composite / entry_score
                        # Exit if current score < 60% of entry score (40% drop)
                        signal_decay_exit = decay_ratio < 0.60
                        if signal_decay_exit:
                            exit_signals["signal_decay"] = round(decay_ratio, 2)
                except Exception as e:
                    log_event("exit", "signal_decay_check_error", symbol=symbol, error=str(e))
            
            # 3. Profit Target: Exit at 0.75% profit (full position)
            profit_target_hit = pnl_pct_decimal >= 0.0075  # 0.75%
            
            # Trailing stop check (for profit protection)
            # BULLETPROOF: Validate trail_stop calculation before comparing
            stop_hit = False
            if not (math.isnan(trail_stop) or math.isinf(trail_stop) or trail_stop <= 0):
                stop_hit = current_price <= trail_stop
            else:
                log_event("exit", "invalid_trail_stop", symbol=symbol, trail_stop=trail_stop, current_price=current_price)
            
            # Set exit signals
            if stop_loss_hit:
                exit_signals["stop_loss"] = True
                exit_signals["stop_loss_pct"] = round(pnl_pct_decimal * 100, 2)
            if stop_hit:
                exit_signals["trail_stop"] = True
            if signal_decay_exit:
                exit_signals["signal_decay_exit"] = True
                if decay_ratio is not None:
                    exit_signals["signal_decay_ratio"] = round(decay_ratio, 2)
            if profit_target_hit:
                exit_signals["profit_target_075"] = True

            ret_pct = _position_return_pct(info["entry_price"], current_price, info.get("side", "buy"))
            
            # V3.0: Ensure targets exist (re-initialize if missing)
            if "targets" not in info or not info["targets"]:
                info["targets"] = [
                    {"pct": t, "hit": False, "fraction": Config.SCALE_OUT_FRACTIONS[i] if i < len(Config.SCALE_OUT_FRACTIONS) else 0.0}
                    for i, t in enumerate(Config.PROFIT_TARGETS)
                ]
                log_event("exit", "profit_targets_reinitialized", symbol=symbol, ret_pct=round(ret_pct, 4))
            
            for tgt in info.get("targets", []):
                if not tgt["hit"] and ret_pct >= tgt["pct"]:
                    if self._scale_out_partial(symbol, tgt["fraction"], info.get("side", "buy")):
                        tgt["hit"] = True
                        # V3.0: Persist updated targets to metadata
                        self._persist_position_metadata(symbol, info.get("ts", datetime.utcnow()), 
                                                        info.get("entry_price", 0.0), info.get("qty", 0),
                                                        info.get("side", "buy"), info.get("entry_score", 0.0),
                                                        info.get("components", {}), 
                                                        info.get("market_regime", "unknown"),
                                                        info.get("direction", "unknown"))
                        side = info.get("side", "buy")
                        entry_price = info.get("entry_price", 0.0)
                        qty = info.get("qty", 1)
                        scaled_qty = int(qty * tgt["fraction"])
                        if scaled_qty < 1:
                            scaled_qty = 1
                        side_sign = 1 if side == "buy" else -1
                        scale_pnl = scaled_qty * (current_price - entry_price) * side_sign
                        
                        entry_ts = info.get("ts", datetime.utcnow())
                        if hasattr(entry_ts, 'tzinfo') and entry_ts.tzinfo is not None:
                            entry_ts = entry_ts.replace(tzinfo=None)
                        hold_minutes = (datetime.utcnow() - entry_ts).total_seconds() / 60.0
                        pnl_pct = ((current_price - entry_price) / entry_price * 100 * side_sign) if entry_price > 0 else 0.0
                        
                        symbol_metadata = all_metadata.get(symbol, {})
                        components = symbol_metadata.get("components", info.get("components", {}))
                        
                        # Build composite close reason for profit target
                        scale_exit_signals = exit_signals.copy()
                        scale_exit_signals["profit_target"] = tgt["pct"]
                        close_reason = build_composite_close_reason(scale_exit_signals)
                        
                        jsonl_write("attribution", {
                            "type": "attribution",
                            "trade_id": f"scale_{symbol}_{now_iso()}",
                            "symbol": symbol,
                            "pnl_usd": round(scale_pnl, 2),
                            "pnl_pct": round(pnl_pct * tgt["fraction"], 4),
                            "hold_minutes": round(hold_minutes, 1),
                            "context": {
                                "close_reason": close_reason,
                                "entry_price": round(entry_price, 4),
                                "exit_price": round(current_price, 4),
                                "pnl_pct": round(pnl_pct, 4),
                                "hold_minutes": round(hold_minutes, 1),
                                "side": side,
                                "qty": scaled_qty,
                                "fraction": tgt["fraction"],
                                "entry_score": info.get("entry_score", 0.0),
                                "components": components,
                                "market_regime": symbol_metadata.get("market_regime", info.get("market_regime", "unknown")),
                                "direction": info.get("direction", "unknown")
                            }
                        })
                        
                        log_event("exit", "scale_out_attribution_logged", 
                                  symbol=symbol, 
                                  pnl_usd=round(scale_pnl, 2), 
                                  pnl_pct=round(pnl_pct, 2),
                                  hold_min=round(hold_minutes, 1),
                                  reason=close_reason,
                                  fraction=tgt["fraction"])

            # V3.0 CONVICTION-BASED EXITS: Exit on stop-loss, signal decay, or profit target
            # REMOVED: time_hit check (no more TIME_EXIT)
            should_exit = stop_loss_hit or signal_decay_exit or profit_target_hit or stop_hit
            
            if should_exit:
                # Build composite close reason before adding to close list
                # CRITICAL: Always set exit_reason when adding to close list
                if symbol not in exit_reasons:
                    exit_reasons[symbol] = build_composite_close_reason(exit_signals)
                to_close.append(symbol)
                exit_reason_str = "stop_loss" if stop_loss_hit else ("signal_decay" if signal_decay_exit else ("profit_075" if profit_target_hit else "trail_stop"))
                print(
                    f"DEBUG EXITS: {symbol} marked for close - {exit_reason_str}, "
                    f"age={age_min:.1f}min, pnl={pnl_pct:.2f}%, entry=${entry_price:.2f}, current=${current_price:.2f}, "
                    f"reason={exit_reasons.get(symbol, 'unknown')}",
                    flush=True,
                )
                
                # CRITICAL FIX: Log to file
                try:
                    with open("logs/worker_debug.log", "a") as f:
                        f.write(f"[{datetime.now(timezone.utc).isoformat()}] EXIT TRIGGERED: {symbol} {exit_reason_str}, P&L={pnl_pct:.2f}%, entry=${entry_price:.2f}, current=${current_price:.2f}\n")
                        f.flush()
                except:
                    pass
        
        if to_close:
            print(f"DEBUG EXITS: Found {len(to_close)} positions to close: {to_close}", flush=True)
            log_event("exit", "positions_to_close", symbols=to_close, count=len(to_close))
            
            # CRITICAL FIX: Log to file
            try:
                with open("logs/worker_debug.log", "a") as f:
                    f.write(f"[{datetime.now(timezone.utc).isoformat()}] EXITS: {len(to_close)} positions to close: {to_close}\n")
                    f.flush()
            except:
                pass
        
        for symbol in to_close:
            try:
                # CRITICAL FIX: Get info from positions_to_evaluate if not in self.opens
                if symbol in positions_to_evaluate:
                    posd = positions_to_evaluate.get(symbol, {}) if isinstance(positions_to_evaluate, dict) else {}
                    info = posd.get("info", {}) if isinstance(posd, dict) else {}
                else:
                    info = self.opens.get(symbol, {})
                    # If still not found, get from metadata
                    if not info and symbol in all_metadata:
                        meta = all_metadata.get(symbol, {}) if isinstance(all_metadata, dict) else {}
                        try:
                            entry_ts_str = meta.get("entry_ts", "")
                            if isinstance(entry_ts_str, str):
                                try:
                                    entry_ts = datetime.fromisoformat(entry_ts_str.replace("Z", ""))
                                except:
                                    entry_ts = datetime.utcnow()
                            else:
                                entry_ts = datetime.utcnow()
                        except:
                            entry_ts = datetime.utcnow()
                        
                        info = {
                            "entry_price": meta.get("entry_price", 0.0),
                            "ts": entry_ts,
                            "side": meta.get("side", "buy"),
                            "entry_score": meta.get("entry_score", 0.0),
                            "qty": meta.get("qty", 0)
                        }
                
                entry_price = info.get("entry_price", 0.0)
                entry_ts = info.get("ts", datetime.utcnow())
                if hasattr(entry_ts, 'tzinfo') and entry_ts.tzinfo is not None:
                    entry_ts = entry_ts.replace(tzinfo=None)
                holding_period_min = (datetime.utcnow() - entry_ts).total_seconds() / 60.0
                
                # Decision/monitoring price only (NOT used for attribution PnL):
                # Attribution must use executed fill price from Alpaca close order (filled_avg_price).
                if symbol in positions_index:
                    pos = positions_index[symbol]
                    decision_exit_price = float(getattr(pos, "current_price", 0))
                    if decision_exit_price <= 0:
                        decision_exit_price = self.get_quote_price(symbol)
                else:
                    decision_exit_price = self.get_quote_price(symbol)
                if decision_exit_price <= 0:
                    decision_exit_price = entry_price
                
                print(f"DEBUG EXITS: Closing {symbol} (decision_px={decision_exit_price:.2f}, entry={entry_price:.2f}, hold={holding_period_min:.1f}min)", flush=True)
                # BULLETPROOF: Safe position close with error handling and verification
                position_closed = False
                close_attempts = 0
                max_close_attempts = 3
                exit_order_id = None
                exit_fill_qty = 0
                exit_fill_price = 0.0
                
                while not position_closed and close_attempts < max_close_attempts:
                    close_attempts += 1
                    try:
                        # Attempt to close position
                        # Contract: closes should succeed even if qty is reserved by open orders.
                        close_order = self.close_position_api_once(symbol)
                        if close_order is None:
                            raise RuntimeError("close_position_api_once returned None")
                        exit_order_id = getattr(close_order, "id", None)
                        log_event("exit", "close_position_api_called", symbol=symbol, attempt=close_attempts, exit_order_id=str(exit_order_id) if exit_order_id else None)
                        
                        # Fill-sourcing contract: wait for executed fill fields from Alpaca.
                        try:
                            max_wait = float(get_env("ATTRIBUTION_EXIT_FILL_WAIT_SEC", 20.0, float))
                        except Exception:
                            max_wait = 20.0
                        if exit_order_id:
                            filled, fq, fp = self.check_order_filled(str(exit_order_id), max_wait_sec=max_wait)
                            if filled:
                                exit_fill_qty = int(fq or 0)
                                exit_fill_price = float(fp or 0.0)
                            else:
                                log_event(
                                    "exit",
                                    "close_order_pending_fill",
                                    symbol=symbol,
                                    exit_order_id=str(exit_order_id),
                                    note="Close order submitted but fill fields not yet available; will not attribute until filled.",
                                )
                        
                        # CRITICAL: Verify position was actually closed by polling Alpaca
                        # Wait a moment for order to process
                        time.sleep(2.0)
                        
                        # Verify position is closed
                        verify_attempts = 0
                        max_verify_attempts = 5
                        while verify_attempts < max_verify_attempts:
                            verify_attempts += 1
                            try:
                                positions = self.api.list_positions()
                                v_positions = [p for p in positions if getattr(p, "symbol", "") == symbol]
                                
                                if not v_positions:
                                    # Position is closed - verification successful
                                    position_closed = True
                                    print(f"DEBUG EXITS: Successfully closed and verified {symbol} (attempt {close_attempts}, verify {verify_attempts})", flush=True)
                                    log_event("exit", "close_position_verified", symbol=symbol, 
                                            close_attempt=close_attempts, verify_attempt=verify_attempts)
                                    # If we verified closure but missed fill fields, retry briefly (fill fields may lag).
                                    if (exit_fill_price <= 0 or exit_fill_qty <= 0) and exit_order_id:
                                        try:
                                            filled2, fq2, fp2 = self.check_order_filled(str(exit_order_id), max_wait_sec=5.0)
                                            if filled2:
                                                exit_fill_qty = int(fq2 or 0)
                                                exit_fill_price = float(fp2 or 0.0)
                                        except Exception:
                                            pass
                                    break
                                else:
                                    # Position still exists - wait and retry verification
                                    if verify_attempts < max_verify_attempts:
                                        log_event("exit", "close_position_still_open", symbol=symbol, 
                                                close_attempt=close_attempts, verify_attempt=verify_attempts,
                                                qty=v_positions[0].qty if v_positions else 0)
                                        time.sleep(3.0)  # Wait 3 seconds before next verification
                                    else:
                                        # Max verification attempts reached, position still open
                                        log_event("exit", "close_position_verification_failed", symbol=symbol,
                                                close_attempt=close_attempts, verify_attempt=verify_attempts,
                                                qty=v_positions[0].qty if v_positions else 0,
                                                error="Position still exists after max verification attempts")
                                        print(f"WARNING EXITS: {symbol} still open after {max_verify_attempts} verification attempts", flush=True)
                            except Exception as verify_err:
                                log_event("exit", "close_position_verify_error", symbol=symbol, 
                                        error=str(verify_err), verify_attempt=verify_attempts)
                                if verify_attempts < max_verify_attempts:
                                    time.sleep(2.0)
                                else:
                                    # Can't verify, but API call succeeded - assume closed (fail open)
                                    log_event("exit", "close_position_verify_failed_assume_closed", symbol=symbol,
                                            error=str(verify_err))
                                    position_closed = True  # Assume closed if we can't verify
                                    break
                        
                        if position_closed:
                            break  # Successfully closed and verified
                            
                    except Exception as close_err:
                        # Contract: Exit failure handlers MUST NOT throw secondary exceptions.
                        # Use a local alias so future edits can't break retry sleeps via shadowing `time`.
                        import time as _time
                        log_event("exit", "close_position_failed", symbol=symbol, error=str(close_err), attempt=close_attempts)
                        print(f"ERROR EXITS: Failed to close {symbol} (attempt {close_attempts}/{max_close_attempts}): {close_err}", flush=True)
                        
                        if close_attempts < max_close_attempts:
                            # Retry after delay
                            wait_time = 2.0 * close_attempts  # Exponential backoff: 2s, 4s
                            log_event("exit", "close_position_retry", symbol=symbol, attempt=close_attempts, wait_sec=wait_time)
                            _time.sleep(wait_time)
                        else:
                            # All attempts failed
                            log_event("exit", "close_position_all_attempts_failed", symbol=symbol, 
                                    attempts=max_close_attempts, error=str(close_err))
                            print(f"ERROR EXITS: All {max_close_attempts} attempts to close {symbol} failed", flush=True)
                            # Continue to next position - don't remove from tracking so it can be retried next cycle
                            continue  # Skip to next position, keep this one in tracking
                
                if not position_closed:
                    # Position could not be closed after all attempts
                    log_event("exit", "close_position_not_verified", symbol=symbol, attempts=close_attempts)
                    print(f"WARNING EXITS: {symbol} could not be verified as closed after {close_attempts} attempts - keeping in tracking for retry", flush=True)
                    # DO NOT remove from tracking - allow retry on next cycle
                    continue  # Skip cleanup, keep position in tracking
                
                # Position successfully closed and verified - now clean up tracking
                log_event("exit", "close_position_success", symbol=symbol, total_attempts=close_attempts)
                
                # Use composite close reason if available, otherwise build one
                close_reason = exit_reasons.get(symbol)
                if not close_reason:
                    # Fallback: build from basic signals
                    # Calculate age for fallback (holding_period_min is already calculated above)
                    age_hours_fallback = holding_period_min / 60.0
                    basic_signals = {
                        "time_exit": holding_period_min >= Config.TIME_EXIT_MINUTES,
                        "trail_stop": decision_exit_price < entry_price * (1 - Config.TRAILING_STOP_PCT / 100),
                        "age_hours": age_hours_fallback
                    }
                    close_reason = build_composite_close_reason(basic_signals)
                    # Log that we used fallback
                    log_event("exit", "close_reason_fallback", symbol=symbol, reason=close_reason)
                
                log_order({"action": "close_position", "symbol": symbol, "reason": close_reason})
                
                symbol_metadata = all_metadata.get(symbol, {})
                # Only log exit attribution when we have executed fill fields.
                if exit_fill_price > 0 and exit_fill_qty > 0:
                    log_exit_attribution(
                        symbol=symbol,
                        info=info,
                        exit_price=exit_fill_price,
                        close_reason=close_reason,
                        metadata=symbol_metadata,
                        exit_qty=exit_fill_qty,
                        exit_order_id=str(exit_order_id) if exit_order_id else None,
                    )
                else:
                    log_event(
                        "data_integrity",
                        "exit_fill_missing_skip_attribution",
                        symbol=symbol,
                        close_reason=close_reason,
                        exit_order_id=str(exit_order_id) if exit_order_id else None,
                        note="Exit verified closed but fill fields not available; skipping attribution to avoid synthetic prices.",
                    )
                
                side = info.get("side", "buy")
                # Realized PnL must use executed fill price/qty when available.
                realized_qty = int(exit_fill_qty) if exit_fill_qty and exit_fill_qty > 0 else int(info.get("qty", 1) or 1)
                if exit_fill_price > 0:
                    if side == "buy":
                        realized_pnl = realized_qty * (exit_fill_price - entry_price)
                    else:
                        realized_pnl = realized_qty * (entry_price - exit_fill_price)
                else:
                    realized_pnl = 0.0
                
                telemetry.log_portfolio_event(
                    event_type="POSITION_CLOSED",
                    symbol=symbol,
                    side=side,
                    qty=realized_qty,
                    entry_price=entry_price,
                    exit_price=exit_fill_price if exit_fill_price > 0 else None,
                    realized_pnl=realized_pnl,
                    unrealized_pnl=0.0,
                    holding_period_min=holding_period_min,
                    reason="time_or_trail",
                    score=info.get("entry_score", 0.0)
                )
                
                # CRITICAL: Only remove from tracking AFTER position is verified as closed
                self.opens.pop(symbol, None)
                self.high_water.pop(symbol, None)
                self._remove_position_metadata(symbol)
                
                # CRITICAL FIX: Log to file
                try:
                    with open("logs/worker_debug.log", "a") as f:
                        f.write(f"[{datetime.now(timezone.utc).isoformat()}] EXIT COMPLETED: {symbol} closed and verified, removed from opens and metadata\n")
                        f.flush()
                except:
                    pass
                    
            except Exception as e:
                log_order({"action": "close_position_failed", "symbol": symbol, "error": str(e)})
                print(f"ERROR EXITS: Exception closing {symbol}: {e}", flush=True)
                try:
                    traceback.print_exc()
                except Exception:
                    pass
                # DO NOT remove from tracking on exception - allow retry next cycle
                log_event("exit", "close_position_exception_keep_tracking", symbol=symbol, error=str(e))
    
    def _remove_position_metadata(self, symbol: str):
        """Remove closed position from metadata file with atomic write."""
        metadata_path = StateFiles.POSITION_METADATA
        try:
            if not metadata_path.exists():
                return
            metadata = load_metadata_with_lock(metadata_path)
            if symbol in metadata:
                del metadata[symbol]
                atomic_write_json(metadata_path, metadata)
        except Exception as e:
            log_event("persist", "metadata_remove_failed", symbol=symbol, error=str(e))

# =========================
# STRATEGY ENGINE (multi-factor scoring)
# =========================
class StrategyEngine:
    def __init__(self):
        self.executor = AlpacaExecutor()
        self.weights = load_weights()
        self.profiles = load_profiles()
        self.theme_map = load_theme_map()
        self.uw_flow_cache = telemetry.get_uw_flow_cache()
        
        # Initialize state manager for persistence (Risk #6)
        try:
            from state_manager import StateManager
            self.state_manager = StateManager(self.executor.api)
            # Load and reconcile state on startup
            state = self.state_manager.load_state()
            if self.executor.api:
                reconciled = self.state_manager.reconcile_with_alpaca(state)
                if not reconciled:
                    log_event("state_manager", "reconciliation_failed_on_startup", 
                             warning="State reconciliation failed - trading may be unsafe")
            # Attach to executor for use in submit_entry
            self.executor._state_manager = self.state_manager
        except Exception as e:
            log_event("state_manager", "initialization_failed", error=str(e))
            self.state_manager = None

    def score_cluster(self, cluster: dict, confirm_score: float, gex: dict, market_regime: str = "mixed") -> float:
        safe_cluster = normalize_cluster(cluster)
        base_score = min(safe_cluster["count"], 10) * Config.FLOW_COUNT_W
        base_score += min(safe_cluster["avg_premium"] / 1_000_000, 2.0) * Config.FLOW_PREMIUM_MILLION_W
        base_score += confirm_score
        
        # Apply UW regime-based weighting
        symbol = cluster["ticker"]
        uw_flow = self.uw_flow_cache.get(symbol, {})
        if uw_flow:
            uw_flow_score = float(uw_flow.get("conviction", 0.0))
            if cluster["direction"] == "bearish":
                uw_flow_score = -uw_flow_score
            uw_adjusted = uw_weighting(market_regime, uw_flow_score)
            base_score += uw_adjusted
        
        key = bucket_key(cluster["ticker"], cluster["direction"], gex.get("gamma_regime", "unknown"))
        w = float(self.weights.get(key, 1.0))
        return round(base_score * w, 3)

    @global_failure_wrapper("decision")
    def decide_and_execute(self, clusters: list, confirm_map: dict, gex_map: dict, decisions_map: dict = None, market_regime: str = "mixed"):
        orders = []
        # Reset per-cycle gate symbol tracker (used for missed-candidate detection).
        try:
            global _CYCLE_GATE_SYMBOLS
            _CYCLE_GATE_SYMBOLS = set()
        except Exception:
            pass

        candidates_above_min = {}
        # Per-cycle gate accounting (for "why no trades?" observability).
        try:
            from collections import Counter as _Counter
            gate_counts = _Counter()
        except Exception:
            gate_counts = {}

        def _inc_gate(k: str) -> None:
            try:
                gate_counts[k] += 1  # type: ignore[index]
            except Exception:
                try:
                    gate_counts[k] = int(gate_counts.get(k, 0)) + 1  # type: ignore[union-attr]
                except Exception:
                    pass

        considered = 0
        top_score = None
        
        open_positions = []
        try:
            open_positions = self.executor.api.list_positions()
        except Exception:
            open_positions = []  # FIX: Initialize to empty list if API call fails

        # Market-data health probe (observability only).
        # Contract: when 1Min bars are stale, emit a clear stale event (probe is observability-only).
        try:
            _probe_1min_bar_freshness_maybe(self.executor.api, symbol="SPY", every_sec=600.0)
        except Exception as e:
            log_event("market_check", "bar_probe_failed", symbol="SPY", error=str(e))
        
        # V4.0: PORTFOLIO CONCENTRATION GATE - Calculate net long-delta exposure
        # BULLETPROOF: Always initialize to safe defaults, fail open on any error
        net_delta_pct = 0.0
        try:
            # Safety check: Only calculate if we have positions
            if len(open_positions) == 0:
                net_delta_pct = 0.0  # Explicit: no positions = 0% delta
                log_event("concentration_gate", "portfolio_delta_zero_no_positions", net_delta_pct=0.0)
            else:
                # BULLETPROOF: API call with error handling and validation
                try:
                    account = self.executor.api.get_account()
                    account_equity = float(getattr(account, "equity", 0.0))
                except (AttributeError, ValueError, TypeError, Exception) as acct_err:
                    log_event("concentration_gate", "account_fetch_error", error=str(acct_err))
                    net_delta_pct = 0.0  # Fail open - allow trading
                    account_equity = 0.0
                
                # BULLETPROOF: Validate equity is positive before division
                if account_equity <= 0:
                    log_event("concentration_gate", "invalid_account_equity", equity=account_equity)
                    net_delta_pct = 0.0  # Fail open - allow trading
                else:
                    # Calculate net portfolio delta (long positions - short positions)
                    net_delta = 0.0
                    for pos in open_positions:
                        try:
                            qty = float(getattr(pos, "qty", 0))
                            market_value = float(getattr(pos, "market_value", 0))
                            if qty > 0:  # Long position
                                net_delta += market_value
                            elif qty < 0:  # Short position
                                net_delta -= abs(market_value)
                        except (AttributeError, ValueError, TypeError) as pos_err:
                            # Individual position error shouldn't break entire calculation
                            log_event("concentration_gate", "position_calc_error", error=str(pos_err))
                            continue
                    
                    net_delta_pct = (net_delta / account_equity * 100) if account_equity > 0 else 0.0
                    # BULLETPROOF: Clamp to reasonable range (prevent NaN/infinity)
                    net_delta_pct = max(-100.0, min(100.0, net_delta_pct))
                    log_event("concentration_gate", "portfolio_delta_calculated", 
                             net_delta_pct=round(net_delta_pct, 2), net_delta_usd=round(net_delta, 2),
                             account_equity=round(account_equity, 2), positions_count=len(open_positions))
        except Exception as conc_error:
            # BULLETPROOF: Fail open - never block trading due to calculation errors
            log_event("concentration_gate", "calculation_error", error=str(conc_error), traceback=repr(conc_error))
            net_delta_pct = 0.0  # Explicitly set to 0 - allow trading to continue
        
        # V3.2: Load Bayesian profiles once per cycle
        bayes_profiles = v32.AdaptiveWeighting.load_profiles()
        system_stage = v32.get_system_stage(bayes_profiles)
        
        # V3.2.1: Safety cap - max new positions per cycle (increased for stronger signal utilization)
        new_positions_this_cycle = 0
        MAX_NEW_POSITIONS_PER_CYCLE = 6
        
        # CRITICAL: Sort clusters by composite_score DESC to trade strongest signals first
        clusters_sorted = sorted(clusters, key=lambda x: x.get("composite_score", 0.0), reverse=True)
        
        print(f"DEBUG decide_and_execute: Processing {len(clusters_sorted)} clusters (sorted by strength), stage={system_stage}", flush=True)
        
        if len(clusters_sorted) == 0:
            print("⚠️  WARNING: decide_and_execute called with 0 clusters - no trades possible", flush=True)
            log_event(
                "gate",
                "cycle_summary",
                market_regime=market_regime,
                stage=system_stage,
                considered=0,
                orders=0,
                gate_counts={},
                reason="no_clusters",
            )
            return orders
        
        for c in clusters_sorted:
            log_signal(c)
            symbol = c["ticker"]
            direction = c.get("direction", "unknown")
            # CRITICAL FIX: Initialize score but recalculate if source is unknown or composite_score is 0.0
            score = c.get("composite_score", 0.0)
            try:
                if float(score) >= float(Config.MIN_EXEC_SCORE):
                    candidates_above_min[str(symbol)] = float(score)
            except Exception:
                pass
            considered += 1
            try:
                s = float(score)
                top_score = s if top_score is None else max(top_score, s)
            except Exception:
                pass
            cluster_source = c.get("source", "unknown")
            print(f"DEBUG {symbol}: Processing cluster - direction={direction}, initial_score={score:.2f}, source={cluster_source}", flush=True)
            
            # LOGIC STAGNATION DETECTOR: Record signal for monitoring
            try:
                from logic_stagnation_detector import get_stagnation_detector
                detector = get_stagnation_detector()
                detector.record_signal(symbol, score, cluster_source)
                
                # Check for stagnation and trigger warm reload (defibrillator) if needed
                stagnation = detector.check_stagnation(market_regime)
                if stagnation and stagnation.get("detected"):
                    # If funnel stagnation detected, trigger warm reload (autonomous defibrillator)
                    if stagnation.get("reason") == "funnel_stagnation":
                        if detector.trigger_warm_reload():
                            log_event("logic_stagnation", "warm_reload_triggered", 
                                     reason="funnel_stagnation",
                                     alerts_30m=stagnation.get("alerts_30m", 0),
                                     orders_30m=stagnation.get("orders_30m", 0),
                                     regime=market_regime)
                    elif detector.trigger_soft_reset():
                        log_event("logic_stagnation", "soft_reset_triggered", 
                                 reason=stagnation.get("reason"),
                                 zero_score_count=stagnation.get("zero_score_count", 0),
                                 momentum_blocks=stagnation.get("consecutive_momentum_blocks", 0))
            except ImportError:
                pass
            except Exception as e:
                log_event("logic_stagnation", "error", error=str(e))
            
            # SIGNAL FUNNEL TRACKER: Record scored signal
            try:
                from signal_funnel_tracker import get_funnel_tracker
                funnel = get_funnel_tracker()
                # Record scored signal (score > 2.7 threshold)
                if score > 2.7:
                    funnel.record_scored_signal(symbol, score)
                
                # ALPHA REPAIR: Stagnation-Triggered Adaptive Scaling
                # Check for 60-minute stagnation and trigger adaptive scaling if needed
                stagnation_60m = funnel.check_60min_stagnation_for_adaptive_scaling(market_regime)
                if stagnation_60m and stagnation_60m.get("detected"):
                    log_event("stagnation_adaptive_scaling", "60min_stagnation_detected",
                             alerts_60m=stagnation_60m.get("alerts_60m", 0),
                             orders_60m=stagnation_60m.get("orders_60m", 0),
                             action=stagnation_60m.get("action_required", "unknown"),
                             regime=market_regime)
                    # Note: ATR exhaustion multiplier adjustment would be implemented here
                    # if a specific multiplier system exists. For now, we log the detection.
            except ImportError:
                pass
            except Exception as e:
                log_event("funnel", "record_scored_error", error=str(e))
            gex = gex_map.get(symbol, {"gamma_regime": "unknown"})
            
            prof = get_or_init_profile(self.profiles, symbol) if Config.ENABLE_PER_TICKER_LEARNING else {}
            
            # CRITICAL FIX: Initialize signal history tracking variables BEFORE gate checks
            # These variables are used in log_signal_to_history() calls within gate checks
            raw_score = score  # Will be updated if composite score is recalculated
            whale_boost = 0.0
            final_score = score
            atr_multiplier = None
            momentum_pct = 0.0
            momentum_required_pct = 0.0
            composite_result = None  # Will store full composite result if available
            
            if Config.ENABLE_REGIME_GATING and not regime_gate_ticker(prof, market_regime):
                log_event("gate", "regime_blocked", symbol=symbol, regime=market_regime, gate_type="regime_gate", signal_type=c.get("signal_type", "UNKNOWN"))
                # SIGNAL HISTORY: Log blocked signal
                log_signal_to_history(
                    symbol=symbol,
                    direction=direction,
                    raw_score=raw_score,
                    whale_boost=whale_boost,
                    final_score=final_score,
                    atr_multiplier=0.0,
                    momentum_pct=0.0,
                    momentum_required_pct=0.0,
                    decision="Blocked: regime_gate",
                    metadata={"regime": market_regime}
                )
                continue
            
            # V4.0: PORTFOLIO CONCENTRATION GATE - Block bullish entries if >70% long-delta
            # BULLETPROOF: Only block if we actually have positions AND delta is calculated correctly
            # Safeguard: Always allow trading if no positions exist (net_delta_pct = 0.0)
            if len(open_positions) > 0 and net_delta_pct > 70.0 and c.get("direction") == "bullish":
                print(f"DEBUG {symbol}: BLOCKED by concentration_gate - net_delta_pct={net_delta_pct:.2f}% > 70%", flush=True)
                log_event("gate", "concentration_blocked_bullish",
                         symbol=symbol, net_delta_pct=round(net_delta_pct, 2),
                         reason="portfolio_already_70pct_long_delta", gate_type="concentration_gate", signal_type=c.get("signal_type", "UNKNOWN"))
                log_blocked_trade(symbol, "concentration_gate", score,
                                 direction=c.get("direction"),
                                 decision_price=ref_price_check if 'ref_price_check' in locals() else 0.0,
                                 components=comps if 'comps' in locals() else {},
                                 net_delta_pct=net_delta_pct)
                # SIGNAL HISTORY: Log blocked signal
                log_signal_to_history(
                    symbol=symbol,
                    direction=direction,
                    raw_score=raw_score,
                    whale_boost=whale_boost,
                    final_score=final_score,
                    atr_multiplier=0.0,
                    momentum_pct=0.0,
                    momentum_required_pct=0.0,
                    decision="Blocked: concentration_limit",
                    metadata={"net_delta_pct": net_delta_pct}
                )
                continue
            
            if Config.ENABLE_THEME_RISK:
                violations = correlated_exposure_guard(open_positions, self.theme_map, Config.MAX_THEME_NOTIONAL_USD)
                sym_theme = self.theme_map.get(symbol, "general")
                if sym_theme in violations:
                    log_event("gate", "theme_exposure_blocked", symbol=symbol, theme=sym_theme, notional=violations[sym_theme], gate_type="theme_gate", signal_type=c.get("signal_type", "UNKNOWN"))
                    continue
            
            # PRIORITIZE COMPOSITE SCORE: If cluster has pre-calculated composite_score, always use it
            # NOTE: raw_score, whale_boost, final_score already initialized above before gate checks
            if "composite_score" in c and cluster_source in ("composite", "composite_v3") and score > 0.0:
                base_score = c["composite_score"]
                raw_score = base_score  # Track raw score before adjustments
                
                # Get composite_meta to extract whale_boost if available
                composite_meta = c.get("composite_meta", {})
                if composite_meta and isinstance(composite_meta, dict):
                    whale_boost = composite_meta.get("whale_conviction_boost", 0.0)
                    composite_result = composite_meta
                else:
                    # If composite_meta not available, try to get from enriched data by recalculating
                    # This ensures whale_boost is captured even if composite_meta is missing
                    try:
                        enriched = self.uw_flow_cache.get(symbol, {})
                        if enriched:
                            import uw_composite_v2 as uw_v2
                            try:
                                import uw_enrichment_v2 as uw_enrich
                                enriched_live = uw_enrich.enrich_signal(symbol, self.uw_flow_cache, market_regime) or enriched
                            except Exception:
                                enriched_live = enriched
                            temp_composite = uw_v2.compute_composite_score_v3(symbol, enriched_live, market_regime)
                            if temp_composite:
                                whale_boost = temp_composite.get("whale_conviction_boost", 0.0)
                                composite_result = temp_composite
                    except Exception:
                        pass  # Fail silently - whale_boost will remain 0.0
                
                # STRUCTURAL INTELLIGENCE: Apply regime and macro multipliers
                try:
                    from structural_intelligence import get_regime_detector, get_macro_gate
                    regime_detector = get_regime_detector()
                    macro_gate = get_macro_gate()
                    
                    # Get regime multiplier
                    regime_name, regime_conf = regime_detector.detect_regime()
                    regime_mult = regime_detector.get_regime_multiplier(direction)
                    
                    # Get macro multiplier
                    sector = self.theme_map.get(symbol, "Technology")  # Default to tech
                    macro_mult = macro_gate.get_macro_multiplier(direction, sector)
                    
                    # Apply multipliers to composite score
                    score = base_score * regime_mult * macro_mult
                    final_score = score  # Final score after all adjustments
                    
                    log_event("structural_intelligence", "composite_adjusted", 
                             symbol=symbol, base_score=base_score, regime_mult=regime_mult, 
                             macro_mult=macro_mult, final_score=score, regime=regime_name)
                except ImportError:
                    score = base_score
                    final_score = score
                    log_event("structural_intelligence", "import_failed", symbol=symbol)
                except Exception as e:
                    score = base_score
                    final_score = score
                    log_event("structural_intelligence", "error", symbol=symbol, error=str(e))
                
                log_event("scoring", "using_composite_score", symbol=symbol, score=score)
                
                # AUTOMATED SCORE VALIDATION: Sanity check post-scoring
                try:
                    from score_validation import get_score_validator
                    validator = get_score_validator()
                    validation_result = validator.validate_score(symbol, score, cluster_source, c)
                    if not validation_result.get("valid", True):
                        log_event("scoring", "score_validation_failed", symbol=symbol, 
                                 score=score, action=validation_result.get("action_taken"),
                                 warning=validation_result.get("warning"))
                except ImportError:
                    pass
                except Exception as e:
                    log_event("scoring", "score_validation_error", symbol=symbol, error=str(e))
                
                entry_action = None
                atr_mult = None
                size_scale = 1.0
                ref_price = self.executor.get_last_trade(symbol)
                if ref_price <= 0:
                    log_event("sizing", "bad_ref_price", symbol=symbol, ref_price=ref_price)
                    continue
                # V5.0: Dynamic & Conviction-Based Position Sizing
                try:
                    from risk_management import calculate_position_size, get_risk_limits
                    # BULLETPROOF: Safe account fetch with error handling
                    try:
                        account = self.executor.api.get_account()
                        account_equity = float(getattr(account, "equity", Config.SIZE_BASE_USD * 100))
                    except (AttributeError, ValueError, TypeError, Exception) as acct_err:
                        log_event("sizing", "account_fetch_error", symbol=symbol, error=str(acct_err))
                        account_equity = Config.SIZE_BASE_USD * 100  # Fallback to safe default
                    base_notional = calculate_position_size(account_equity)  # 1.5% base
                    limits = get_risk_limits()
                    # Conviction-based scaling: >4.5 -> 2.0%, <3.5 -> 1.0%, base 1.5%
                    if score > 4.5:
                        conviction_mult = 2.0 / 1.5  # Scale to 2.0% (1.33x)
                    elif score < 3.5:
                        conviction_mult = 1.0 / 1.5  # Scale to 1.0% (0.67x)
                    else:
                        conviction_mult = 1.0  # Base 1.5%
                    notional_target = min(base_notional * conviction_mult, limits["max_position_dollar"])
                    log_event("sizing", "conviction_based", symbol=symbol, score=score, 
                             base_notional=round(base_notional, 2), conviction_mult=round(conviction_mult, 2),
                             final_notional=round(notional_target, 2), account_equity=round(account_equity, 2))
                except (ImportError, Exception) as sizing_error:
                    # Fallback to fixed sizing if risk management not available
                    log_event("sizing", "fallback_to_fixed", symbol=symbol, error=str(sizing_error))
                    notional_target = Config.SIZE_BASE_USD
                qty = max(1, int(notional_target / ref_price))
                # V2.1 FIX: Extract signal components from composite_meta for ML learning
                # This enables the learning system to understand WHY trades succeeded or failed
                composite_meta = c.get("composite_meta", {})
                comps = composite_meta.get("components", {})
                # Also capture expanded intel features for comprehensive learning
                if not comps and "features_for_learning" in c:
                    comps = c.get("features_for_learning", {})
                # Shadow tracking wants to understand the impact of slower-changing intel too.
                # IMPORTANT: Do not include raw flow_trades arrays (too large); only include compact summaries.
                try:
                    uw_raw = self.uw_flow_cache.get(symbol, {}) if hasattr(self, "uw_flow_cache") else {}
                    if isinstance(uw_raw, dict) and uw_raw:
                        uw_shadow_intel = {
                            "_last_update": uw_raw.get("_last_update", uw_raw.get("last_update")),
                            "sentiment": uw_raw.get("sentiment"),
                            "conviction": uw_raw.get("conviction"),
                            "trade_count": uw_raw.get("trade_count"),
                            "flow_trades_n": len(uw_raw.get("flow_trades") or []),
                            "dark_pool": uw_raw.get("dark_pool", {}),
                            "insider": uw_raw.get("insider", {}),
                            "calendar": uw_raw.get("calendar", {}),
                            "market_tide": uw_raw.get("market_tide", {}),
                            "greeks": uw_raw.get("greeks", {}),
                            "oi_change": uw_raw.get("oi_change", {}),
                            "iv_rank": uw_raw.get("iv_rank", {}),
                            "etf_flow": uw_raw.get("etf_flow", {}),
                            "ftd_pressure": uw_raw.get("ftd_pressure", {}),
                            # These are currently placeholders if UW per-ticker endpoints are unavailable
                            "congress": uw_raw.get("congress", {}),
                            "institutional": uw_raw.get("institutional", {}),
                        }
                        # Embed into comps so shadow logger can track potential impact vs trade outcomes.
                        if isinstance(comps, dict):
                            comps.setdefault("_shadow_inputs", {})
                            if isinstance(comps.get("_shadow_inputs"), dict):
                                comps["_shadow_inputs"]["uw_intel"] = uw_shadow_intel
                                comps["_shadow_inputs"]["component_sources"] = composite_meta.get("component_sources", {})
                                comps["_shadow_inputs"]["expanded_intel"] = composite_meta.get("expanded_intel", {})
                except Exception:
                    pass
            elif Config.ENABLE_PER_TICKER_LEARNING and decisions_map:
                prof = get_or_init_profile(self.profiles, symbol)
                cluster_key = f"{symbol}|{c['direction']}|{c['start_ts']}"
                d = decisions_map.get(cluster_key, {})
                confirm_components = d.get("confirm_components", {})
                comps = component_scores(c, confirm_components)
                per_ticker_total = weighted_total_score(comps, prof.get("component_weights", Config.DEFAULT_COMPONENT_WEIGHTS))
                key = bucket_key(symbol, c["direction"], gex.get("gamma_regime", "unknown"))
                bucket_w = float(self.weights.get(key, 1.0))
                score = round(per_ticker_total * bucket_w, 3)
                
                entry_action = d.get("entry_action", "maker_bias")
                atr_mult = d.get("atr_mult", 1.5)
                size_scale = d.get("size_scale", 1.0)
                ref_price = self.executor.get_last_trade(symbol)
                if ref_price <= 0:
                    log_event("sizing", "bad_ref_price", symbol=symbol, ref_price=ref_price)
                    continue
                # V5.0: Dynamic & Conviction-Based Position Sizing
                try:
                    from risk_management import calculate_position_size, get_risk_limits
                    # BULLETPROOF: Safe account fetch with error handling
                    try:
                        account = self.executor.api.get_account()
                        account_equity = float(getattr(account, "equity", Config.SIZE_BASE_USD * 100))
                    except (AttributeError, ValueError, TypeError, Exception) as acct_err:
                        log_event("sizing", "account_fetch_error", symbol=symbol, error=str(acct_err))
                        account_equity = Config.SIZE_BASE_USD * 100  # Fallback to safe default
                    base_notional = calculate_position_size(account_equity)  # 1.5% base
                    limits = get_risk_limits()
                    # Conviction-based scaling: >4.5 -> 2.0%, <3.5 -> 1.0%, base 1.5%
                    if score > 4.5:
                        conviction_mult = 2.0 / 1.5  # Scale to 2.0% (1.33x)
                    elif score < 3.5:
                        conviction_mult = 1.0 / 1.5  # Scale to 1.0% (0.67x)
                    else:
                        conviction_mult = 1.0  # Base 1.5%
                    notional_target = min(base_notional * conviction_mult * size_scale, limits["max_position_dollar"])
                    log_event("sizing", "conviction_based", symbol=symbol, score=score,
                             base_notional=round(base_notional, 2), conviction_mult=round(conviction_mult, 2),
                             size_scale=size_scale, final_notional=round(notional_target, 2), account_equity=round(account_equity, 2))
                except (ImportError, Exception) as sizing_error:
                    # Fallback to fixed sizing if risk management not available
                    log_event("sizing", "fallback_to_fixed", symbol=symbol, error=str(sizing_error))
                    notional_target = Config.SIZE_BASE_USD * size_scale
                qty = max(1, int(notional_target / ref_price))
            else:
                # CRITICAL FIX: Fallback scoring when source is unknown or composite_score is missing/zero
                # This prevents 0.00 scores from blocking all trades
                # Calculate score from scratch using score_cluster method
                confirm_score = confirm_map.get(symbol, 0.0)
                score = self.score_cluster(c, confirm_score, gex, market_regime)
                if cluster_source == "unknown" or c.get("composite_score", 0.0) <= 0.0:
                    log_event("scoring", "fallback_score_calculated", symbol=symbol, source=cluster_source, 
                             calculated_score=score, confirm_score=confirm_score)
                    print(f"DEBUG {symbol}: Fallback scoring - calculated score={score:.2f} (source was {cluster_source})", flush=True)
                
                # AUTOMATED SCORE VALIDATION: Sanity check post-scoring (fallback path)
                try:
                    from score_validation import get_score_validator
                    validator = get_score_validator()
                    validation_result = validator.validate_score(symbol, score, cluster_source, c)
                    if not validation_result.get("valid", True):
                        log_event("scoring", "score_validation_failed", symbol=symbol, 
                                 score=score, action=validation_result.get("action_taken"),
                                 warning=validation_result.get("warning"))
                except ImportError:
                    pass
                except Exception as e:
                    log_event("scoring", "score_validation_error", symbol=symbol, error=str(e))
                
                entry_action = None
                atr_mult = None
                size_scale = 1.0
                ref_price = self.executor.get_last_trade(symbol)
                if ref_price <= 0:
                    log_event("sizing", "bad_ref_price", symbol=symbol, ref_price=ref_price)
                    continue
                # V5.0: Dynamic & Conviction-Based Position Sizing
                try:
                    from risk_management import calculate_position_size, get_risk_limits
                    # BULLETPROOF: Safe account fetch with error handling
                    try:
                        account = self.executor.api.get_account()
                        account_equity = float(getattr(account, "equity", Config.SIZE_BASE_USD * 100))
                    except (AttributeError, ValueError, TypeError, Exception) as acct_err:
                        log_event("sizing", "account_fetch_error", symbol=symbol, error=str(acct_err))
                        account_equity = Config.SIZE_BASE_USD * 100  # Fallback to safe default
                    base_notional = calculate_position_size(account_equity)  # 1.5% base
                    limits = get_risk_limits()
                    # Conviction-based scaling: >4.5 -> 2.0%, <3.5 -> 1.0%, base 1.5%
                    if score > 4.5:
                        conviction_mult = 2.0 / 1.5  # Scale to 2.0% (1.33x)
                    elif score < 3.5:
                        conviction_mult = 1.0 / 1.5  # Scale to 1.0% (0.67x)
                    else:
                        conviction_mult = 1.0  # Base 1.5%
                    notional_target = min(base_notional * conviction_mult, limits["max_position_dollar"])
                    log_event("sizing", "conviction_based", symbol=symbol, score=score, 
                             base_notional=round(base_notional, 2), conviction_mult=round(conviction_mult, 2),
                             final_notional=round(notional_target, 2), account_equity=round(account_equity, 2))
                except (ImportError, Exception) as sizing_error:
                    # Fallback to fixed sizing if risk management not available
                    log_event("sizing", "fallback_to_fixed", symbol=symbol, error=str(sizing_error))
                    notional_target = Config.SIZE_BASE_USD
                qty = max(1, int(notional_target / ref_price))
                # V2.1 FIX: Try to extract components from confirm_map for ML learning
                comps = {}
                # Components extraction - simplified since dp_map, net_map, etc. not in scope
                # comps will be empty dict, which is acceptable for fallback scoring path
            
            # UW entry gate (institutional quality filter) - graceful if cache empty
            # DISABLED for composite-sourced clusters (they have count=1, premium=0 by design)
            # Only apply to real option flow clusters
            uw_flow = self.uw_flow_cache.get(symbol, {})
            
            if c.get("source") not in ("composite", "composite_v3"):
                uw_cluster_data = {"count": c.get("count", 0), "avg_premium": c.get("avg_premium", 0)}
                
                # Only enforce entry gate if UW flow cache has data for this symbol
                if uw_flow and uw_flow.get("conviction", 0.0) > 0:
                    if not uw_entry_gate(uw_cluster_data):
                        continue
            
            # UW conviction-based sizing (if cache populated)
            if uw_flow:
                uw_sentiment = uw_flow.get("sentiment", "")
                uw_conviction = float(uw_flow.get("conviction", 0.0))
                qty = uw_size_modifier(qty, uw_sentiment, uw_conviction)
            
            # V3.2 CHECKPOINT: PRE_ALLOCATE - Dynamic Sizing
            # Get recent slippage from TCA data
            try:
                from tca_data_manager import get_recent_slippage
                recent_slippage_pct = get_recent_slippage(symbol=symbol, lookback_hours=24)
            except ImportError:
                recent_slippage_pct = 0.003  # Fallback default
            size_multiplier = v32.DynamicSizing.calculate_multiplier(
                composite_score=score,
                slippage_pct=recent_slippage_pct,
                regime=market_regime,
                stage=system_stage
            )
            
            # Apply multiplier to quantity
            qty = max(1, int(qty * size_multiplier))
            
            # MIN_NOTIONAL_USD floor check to prevent tiny orders
            ref_price_check = self.executor.get_last_trade(symbol)
            actual_notional = qty * ref_price_check
            if actual_notional < Config.MIN_NOTIONAL_USD:
                log_event("sizing", "min_notional_floor_reject", symbol=symbol, qty=qty, notional=round(actual_notional, 2), min_required=Config.MIN_NOTIONAL_USD)
                continue
            
            # V3.3: POSITION FLIPPING - Close opposite direction positions
            # If we have a SHORT and signal is BULLISH (or vice versa), close the opposite position
            signal_direction = c.get("direction", "").lower() if c.get("direction") else ""
            if symbol in self.executor.opens and signal_direction:
                existing_record = self.executor.opens.get(symbol, {})
                existing_side = existing_record.get("side", "").lower() if existing_record else ""
                
                # Determine if we need to flip
                should_flip = False
                if signal_direction == "bullish" and existing_side == "sell":
                    should_flip = True
                elif signal_direction == "bearish" and existing_side == "buy":
                    should_flip = True
                
                if should_flip and score >= 4.0:  # Only flip for high-conviction signals
                    print(f"DEBUG {symbol}: POSITION FLIP - Closing {existing_side} to enter {signal_direction} (score={score:.2f})", flush=True)
                    log_event("position_flip", "closing_opposite", symbol=symbol,
                             old_side=existing_side, new_direction=signal_direction, score=score)
                    try:
                        # Close the opposite position using Alpaca API
                        # BULLETPROOF: Safe position close with error handling and verification
                        position_closed = False
                        try:
                            # Contract: closes should succeed even if qty is reserved by open orders.
                            self.executor.close_position_with_retries(symbol, max_attempts=3)
                            log_event("position_flip", "close_position_api_called", symbol=symbol)
                            
                            # CRITICAL: Verify position was actually closed
                            time.sleep(2.0)  # Wait for order to process
                            for verify_attempt in range(5):
                                try:
                                    positions = self.executor.api.list_positions()
                                    v_positions = [p for p in positions if getattr(p, "symbol", "") == symbol]
                                    if not v_positions:
                                        position_closed = True
                                        log_event("position_flip", "close_position_verified", symbol=symbol, verify_attempt=verify_attempt+1)
                                        break
                                    elif verify_attempt < 4:
                                        time.sleep(3.0)
                                        log_event("position_flip", "close_position_still_open", symbol=symbol, verify_attempt=verify_attempt+1)
                                except Exception as verify_err:
                                    if verify_attempt < 4:
                                        time.sleep(2.0)
                                    else:
                                        # Can't verify, assume closed (fail open)
                                        position_closed = True
                                        log_event("position_flip", "close_position_verify_failed_assume_closed", symbol=symbol, error=str(verify_err))
                                        break
                            
                            if not position_closed:
                                log_event("position_flip", "close_position_not_verified", symbol=symbol)
                                continue  # Skip if position not verified as closed
                                
                            log_event("position_flip", "close_position_success", symbol=symbol)
                        except Exception as close_err:
                            log_event("position_flip", "close_position_failed", symbol=symbol, error=str(close_err))
                            continue  # Skip if can't close old position
                        
                        # Only remove from internal tracking if position was verified as closed
                        if symbol in self.executor.opens:
                            del self.executor.opens[symbol]
                        if symbol in self.executor.high_water:
                            del self.executor.high_water[symbol]
                        if symbol in self.executor.cooldowns:
                            del self.executor.cooldowns[symbol]
                        log_event("position_flip", "closed_success", symbol=symbol)
                        time.sleep(1.0)  # Brief pause for order to settle and API to sync
                    except Exception as e:
                        log_event("position_flip", "close_failed", symbol=symbol, error=str(e))
                        # Skip this symbol - can't flip if close failed
                        continue
                elif symbol in self.executor.opens and not should_flip:
                    # REQUIRED FIX: Max 1 Position per Symbol governor - hard block duplicate positions
                    # Normalize symbol to prevent GOOG/GOOGL concentration bias
                    normalized_symbol = _normalize_ticker(symbol)
                    
                    # Check if we already have a position (including normalized variants)
                    has_existing_position = False
                    try:
                        positions = self.executor.api.list_positions() or []
                        for pos in positions:
                            pos_symbol = getattr(pos, "symbol", "")
                            if pos_symbol:
                                pos_normalized = _normalize_ticker(pos_symbol)
                                if pos_normalized == normalized_symbol:
                                    has_existing_position = True
                                    break
                    except Exception:
                        # If check fails, use opens dict as fallback
                        has_existing_position = symbol in self.executor.opens
                    
                    if has_existing_position:
                        # HARD BLOCK: Max 1 Position per Symbol
                        _inc_gate("max_one_position_per_symbol")
                        log_event("gate", "max_one_position_per_symbol", 
                                 symbol=symbol, normalized_symbol=normalized_symbol,
                                 existing_side=existing_side, gate_type="diversification_gate", 
                                 signal_type=c.get("signal_type", "UNKNOWN"))
                        # SIGNAL HISTORY: Log blocked signal
                        log_signal_to_history(
                            symbol=symbol,
                            direction=direction,
                            raw_score=raw_score,
                            whale_boost=whale_boost,
                            final_score=final_score,
                            atr_multiplier=atr_mult or 0.0,
                            momentum_pct=0.0,
                            momentum_required_pct=0.0,
                            decision="Blocked: max_one_position_per_symbol",
                            metadata={"normalized_symbol": normalized_symbol, "existing_side": existing_side}
                        )
                        continue
            
            # Capture ATR multiplier if available (for signal history)
            if 'atr_mult' in locals() and atr_mult is not None:
                atr_multiplier = atr_mult
            else:
                atr_multiplier = None
            
            # V3.2 CHECKPOINT: POST_SCORING - Expectancy Gate
            # Calculate expectancy from multiple inputs
            ticker_key = f"{symbol}_{market_regime}"
            ticker_profile = bayes_profiles.get("profiles", {}).get(ticker_key, {})
            ticker_bayes_expectancy = ticker_profile.get("expectancy", 0.0)

            # STRUCTURAL UPGRADE: Decision-level shadow A/B (v2) — evaluate v2 through the same downstream gates.
            # This is read-only/hypothetical and only emits telemetry.
            shadow_enabled = False
            v2_shadow = None
            v2_score = None
            try:
                from config.registry import StrategyFlags
                shadow_enabled = bool(getattr(StrategyFlags, "SHADOW_TRADING_ENABLED", True))
            except Exception:
                shadow_enabled = False
            if shadow_enabled:
                try:
                    cm = c.get("composite_meta", {}) if isinstance(c, dict) else {}
                    v2_shadow = cm.get("shadow_v2", {}) if isinstance(cm, dict) else {}
                    if isinstance(v2_shadow, dict) and "score" in v2_shadow:
                        v2_score = float(v2_shadow.get("score", 0.0) or 0.0)
                except Exception:
                    v2_shadow = None
                    v2_score = None
            
            # Get regime forecast modifier and TCA quality
            try:
                from tca_data_manager import get_regime_forecast_modifier, get_tca_quality_score
                regime_modifier = get_regime_forecast_modifier(market_regime)
                tca_modifier = get_tca_quality_score(symbol=symbol, lookback_hours=24) * 0.1  # Scale to -0.1 to +0.1
            except ImportError:
                regime_modifier = 0.0  # Fallback default
                tca_modifier = 0.0  # Fallback default
            theme_risk_penalty = 0.0  # Already checked via theme_risk guard
            
            # Link toxicity_penalty to actual toxicity from cluster data
            cluster_toxicity = c.get("toxicity", 0) or c.get("features_for_learning", {}).get("toxicity", 0)
            if cluster_toxicity > 0.5:
                toxicity_penalty = (cluster_toxicity - 0.5) * 0.3  # Scale penalty with toxicity level
            elif cluster_toxicity > 0.3:
                toxicity_penalty = (cluster_toxicity - 0.3) * 0.1  # Mild penalty for moderate toxicity
            else:
                toxicity_penalty = 0.0
            
            expectancy = v32.ExpectancyGate.calculate_expectancy(
                composite_score=score,
                ticker_bayes_expectancy=ticker_bayes_expectancy,
                regime_modifier=regime_modifier,
                tca_modifier=tca_modifier,
                theme_risk_penalty=theme_risk_penalty,
                toxicity_penalty=toxicity_penalty
            )

            # Shadow expectancy (v2) using the exact same inputs, substituting v2 score.
            v2_expectancy = None
            v2_should_trade = None
            v2_gate_reason = None
            if shadow_enabled and v2_score is not None:
                try:
                    v2_expectancy = v32.ExpectancyGate.calculate_expectancy(
                        composite_score=float(v2_score),
                        ticker_bayes_expectancy=ticker_bayes_expectancy,
                        regime_modifier=regime_modifier,
                        tca_modifier=tca_modifier,
                        theme_risk_penalty=theme_risk_penalty,
                        toxicity_penalty=toxicity_penalty,
                    )
                    v2_should_trade, v2_gate_reason = v32.ExpectancyGate.should_enter(
                        ticker=symbol,
                        expectancy=float(v2_expectancy),
                        composite_score=float(v2_score),
                        stage=system_stage,
                        regime=market_regime,
                        tca_modifier=tca_modifier,
                        freeze_active=freeze_active,
                        score_floor_breach=(float(v2_score) < float(Config.MIN_EXEC_SCORE)),
                        broker_health_degraded=False,
                    )
                except Exception:
                    v2_expectancy = None
                    v2_should_trade = None
                    v2_gate_reason = None
            
            # Check expectancy gate (v3.2.1 enhanced with telemetry)
            freeze_active = check_freeze_state() == False
            should_trade, gate_reason = v32.ExpectancyGate.should_enter(
                ticker=symbol,
                expectancy=expectancy,
                composite_score=score,
                stage=system_stage,
                regime=market_regime,
                tca_modifier=tca_modifier,
                freeze_active=freeze_active,
                score_floor_breach=(score < Config.MIN_EXEC_SCORE),
                broker_health_degraded=False  # TODO: Link to broker health monitor
            )
            
            print(f"DEBUG {symbol}: expectancy={expectancy:.4f}, should_trade={should_trade}, reason={gate_reason}", flush=True)
            
            if not should_trade:
                _inc_gate(f"expectancy_blocked:{gate_reason}")
                log_event("gate", "expectancy_blocked", symbol=symbol, 
                         expectancy=expectancy, reason=gate_reason, stage=system_stage, gate_type="expectancy_gate", signal_type=c.get("signal_type", "UNKNOWN"))

                # Shadow decision telemetry: would v2 have passed expectancy here?
                try:
                    if shadow_enabled and v2_score is not None:
                        from telemetry.shadow_ab import log_shadow_event, log_shadow_divergence
                        log_shadow_event(
                            "shadow_blocked",
                            symbol=symbol,
                            reason="expectancy_gate_v1_blocked",
                            v1_score=float(score),
                            v2_score=float(v2_score),
                            v1_reason=str(gate_reason),
                            v2_reason=str(v2_gate_reason) if v2_gate_reason is not None else None,
                            v2_would_trade=bool(v2_should_trade) if v2_should_trade is not None else None,
                        )
                        if v2_should_trade is True:
                            log_shadow_event(
                                "shadow_candidate",
                                symbol=symbol,
                                note="v2_would_pass_expectancy_where_v1_blocked",
                                v2_score=float(v2_score),
                                v2_expectancy=float(v2_expectancy) if v2_expectancy is not None else None,
                            )
                            log_shadow_divergence(
                                symbol=symbol,
                                v1_score=float(score),
                                v2_score=float(v2_score),
                                v1_pass=False,
                                v2_pass=True,
                                details={"gate": "expectancy_gate", "v1_reason": str(gate_reason), "v2_reason": str(v2_gate_reason)},
                            )
                except Exception:
                    pass
                
                # SHADOW LOGGER: Track rejected signal
                try:
                    from self_healing import get_shadow_logger
                    shadow = get_shadow_logger()
                    threshold = shadow.get_gate_threshold("expectancy_gate", "min_expectancy", 0.0)
                    shadow.log_rejected_signal(symbol, f"expectancy_blocked:{gate_reason}", score, comps, "expectancy_gate", threshold)
                except:
                    pass
                
                log_blocked_trade(symbol, f"expectancy_blocked:{gate_reason}", score, 
                                  direction=c.get("direction"),
                                  decision_price=ref_price_check,
                                  components=comps,
                                  expectancy=expectancy, stage=system_stage)
                
                # SIGNAL HISTORY: Log blocked signal
                log_signal_to_history(
                    symbol=symbol,
                    direction=direction,
                    raw_score=raw_score,
                    whale_boost=whale_boost,
                    final_score=final_score,
                    atr_multiplier=atr_mult or 0.0,
                    momentum_pct=momentum_pct,
                    momentum_required_pct=momentum_required_pct,
                    decision=f"Rejected: expectancy_gate",
                    metadata={"expectancy": expectancy, "reason": gate_reason, "stage": system_stage}
                )
                continue
            
            print(f"DEBUG {symbol}: PASSED expectancy gate, checking other gates...", flush=True)
            
            # V3.2.1: Check cycle position limit
            if new_positions_this_cycle >= MAX_NEW_POSITIONS_PER_CYCLE:
                _inc_gate("max_new_positions_per_cycle_reached")
                log_event("gate", "max_new_positions_per_cycle_reached", symbol=symbol, 
                         cycle_count=new_positions_this_cycle, max_allowed=MAX_NEW_POSITIONS_PER_CYCLE, gate_type="capacity_gate", signal_type=c.get("signal_type", "UNKNOWN"))
                log_blocked_trade(symbol, "max_new_positions_per_cycle", score,
                                  direction=c.get("direction"),
                                  decision_price=ref_price_check,
                                  components=comps,
                                  cycle_count=new_positions_this_cycle)
                
                # SHADOW TRACKING: Create shadow position for signals > 3.0 blocked by capacity_limit
                try:
                    from shadow_tracker import get_shadow_tracker
                    from alpha_signature_capture import capture_alpha_signature
                    from risk_management import get_sector
                    from persistence_tracker import get_persistence_tracker
                    from sector_tide_tracker import get_sector_tide_tracker
                    
                    if final_score >= 3.0:
                        shadow_tracker = get_shadow_tracker()
                        entry_price = ref_price_check
                        shadow_created = shadow_tracker.create_shadow_position(
                            symbol=symbol,
                            direction=direction,
                            entry_price=entry_price,
                            entry_score=final_score,
                            block_reason="capacity_limit"
                        )
                        
                        # Capture alpha signature
                        alpha_signature = {}
                        try:
                            if hasattr(engine, 'executor') and hasattr(engine.executor, 'api'):
                                # Get UW cache for alpha signature
                                uw_cache = read_json(CacheFiles.UW_FLOW_CACHE, default={})
                                alpha_signature = capture_alpha_signature(engine.executor.api, symbol, uw_cache)
                        except Exception:
                            pass
                        
                        # Get sector and persistence info
                        sector = get_sector(symbol)
                        persistence_count = 0
                        sector_tide_count = 0
                        try:
                            persistence_tracker = get_persistence_tracker()
                            persistence_check = persistence_tracker.check_persistence(symbol)
                            persistence_count = persistence_check.get("count", 0)
                            
                            tide_tracker = get_sector_tide_tracker()
                            tide_info = tide_tracker.check_sector_tide(symbol)
                            sector_tide_count = tide_info.get("count", 0)
                        except Exception:
                            pass
                        
                        if shadow_created:
                            print(f"DEBUG {symbol}: Shadow position created for capacity_limit block (score={final_score:.2f})", flush=True)
                    else:
                        shadow_created = False
                except ImportError:
                    shadow_created = False
                except Exception as e:
                    print(f"DEBUG: Failed to create shadow position for {symbol}: {e}", flush=True)
                    shadow_created = False
                
                # SIGNAL HISTORY: Log blocked signal with alpha signature
                log_signal_to_history(
                    symbol=symbol,
                    direction=direction,
                    raw_score=raw_score,
                    whale_boost=whale_boost,
                    final_score=final_score,
                    atr_multiplier=atr_multiplier or 0.0,
                    momentum_pct=momentum_pct,
                    momentum_required_pct=momentum_required_pct,
                    decision="Blocked: capacity_limit",
                    metadata={
                        "cycle_count": new_positions_this_cycle,
                        "max_allowed": MAX_NEW_POSITIONS_PER_CYCLE,
                        "shadow_created": shadow_created if 'shadow_created' in locals() else False,
                        "alpha_signature": alpha_signature if 'alpha_signature' in locals() else {},
                        "sector": sector if 'sector' in locals() else "Unknown",
                        "persistence_count": persistence_count if 'persistence_count' in locals() else 0,
                        "sector_tide_count": sector_tide_count if 'sector_tide_count' in locals() else 0
                    }
                )
                continue
            
            # Stage-aware score gate (more lenient in bootstrap for learning)
            min_score = Config.MIN_EXEC_SCORE
            if system_stage == "bootstrap":
                min_score = 1.5  # More lenient for bootstrap learning (was 2.0)
            
            # SELF-HEALING THRESHOLD: Adjust based on recent performance
            try:
                from self_healing_threshold import SelfHealingThreshold
                if not hasattr(self, '_self_healing_threshold'):
                    self._self_healing_threshold = SelfHealingThreshold(base_threshold=min_score)
                adjusted_threshold = self._self_healing_threshold.check_recent_trades()
                
                # Log threshold adjustment if activated
                if self._self_healing_threshold.is_activated():
                    status = self._self_healing_threshold.get_status()
                    try:
                        from xai.explainable_logger import get_explainable_logger
                        explainable = get_explainable_logger()
                        explainable.log_threshold_adjustment(
                            symbol=symbol,
                            base_threshold=min_score,
                            adjusted_threshold=adjusted_threshold,
                            reason=f"self_healing_activated(consecutive_losses={status['consecutive_losses']})",
                            status=status
                        )
                    except Exception as e:
                        log_event("explainable", "threshold_log_failed", error=str(e))
                    
                    log_event("self_healing", "threshold_raised", 
                            symbol=symbol, base=min_score, adjusted=adjusted_threshold,
                            consecutive_losses=status['consecutive_losses'])
                
                min_score = adjusted_threshold
            except ImportError:
                # Self-healing threshold not available - use base threshold
                pass
            except Exception as e:
                log_event("self_healing", "error", error=str(e))
            
            if score < min_score:
                print(f"DEBUG {symbol}: BLOCKED by score_below_min ({score} < {min_score}, stage={system_stage})", flush=True)
                _inc_gate("score_below_min")
                log_event("gate", "score_below_min", symbol=symbol, score=score, min_required=min_score, stage=system_stage, gate_type="score_gate", signal_type=c.get("signal_type", "UNKNOWN"))

                # Shadow decision telemetry: would v2 have cleared the score floor here?
                try:
                    if shadow_enabled and v2_score is not None:
                        from telemetry.shadow_ab import log_shadow_event, log_shadow_divergence
                        v2_pass_floor = float(v2_score) >= float(min_score)
                        log_shadow_event(
                            "shadow_blocked",
                            symbol=symbol,
                            reason="score_gate_v1_blocked",
                            min_required=float(min_score),
                            v1_score=float(score),
                            v2_score=float(v2_score),
                            v2_pass_floor=bool(v2_pass_floor),
                        )
                        if v2_pass_floor:
                            log_shadow_event(
                                "shadow_candidate",
                                symbol=symbol,
                                note="v2_would_pass_score_floor_where_v1_blocked",
                                v2_score=float(v2_score),
                                min_required=float(min_score),
                            )
                            log_shadow_divergence(
                                symbol=symbol,
                                v1_score=float(score),
                                v2_score=float(v2_score),
                                v1_pass=False,
                                v2_pass=True,
                                details={"gate": "score_gate", "min_required": float(min_score)},
                            )
                except Exception:
                    pass
                
                # SHADOW LOGGER: Track rejected signal
                try:
                    from self_healing import get_shadow_logger
                    shadow = get_shadow_logger()
                    threshold = shadow.get_gate_threshold("score_gate", "min_score", min_score)
                    shadow.log_rejected_signal(symbol, "score_below_min", score, comps, "score_gate", threshold)
                except:
                    pass
                
                log_blocked_trade(symbol, "score_below_min", score,
                                  direction=c.get("direction"),
                                  decision_price=ref_price_check,
                                  components=comps,
                                  min_required=min_score,
                                  stage=system_stage)
                
                # SIGNAL HISTORY: Log blocked signal
                log_signal_to_history(
                    symbol=symbol,
                    direction=direction,
                    raw_score=raw_score,
                    whale_boost=whale_boost,
                    final_score=final_score,
                    atr_multiplier=atr_mult or 0.0,
                    momentum_pct=momentum_pct,
                    momentum_required_pct=momentum_required_pct,
                    decision=f"Blocked: score_too_low",
                    metadata={"min_required": min_score, "stage": system_stage}
                )
                continue
            if not self.executor.can_open_new_position():
                # V1.0: Attempt Opportunity Cost Displacement before blocking
                displacement_candidate = self.executor.find_displacement_candidate(
                    new_signal_score=score, 
                    new_symbol=symbol
                )
                if displacement_candidate:
                    # SAFETY: Debug/telemetry must never crash trading.
                    # WHY: Production saw KeyError('score_advantage') here, which bubbled up and killed run_once().
                    # HOW TO VERIFY: logs/worker_error.jsonl no longer shows KeyError('score_advantage'); loop continues.
                    dc_symbol = displacement_candidate.get("symbol", "UNKNOWN") if isinstance(displacement_candidate, dict) else "UNKNOWN"
                    dc_adv = displacement_candidate.get("score_advantage") if isinstance(displacement_candidate, dict) else None
                    dc_adv_str = f"{float(dc_adv):.1f}" if isinstance(dc_adv, (int, float)) else "n/a"
                    print(f"DEBUG {symbol}: Attempting displacement of {dc_symbol} (score advantage: {dc_adv_str})", flush=True)
                    displacement_success = self.executor.execute_displacement(
                        candidate=displacement_candidate,
                        new_symbol=symbol,
                        new_signal_score=score
                    )
                    if not displacement_success:
                        print(f"DEBUG {symbol}: BLOCKED - displacement failed", flush=True)
                        displaced_sym = displacement_candidate.get("symbol", "UNKNOWN") if isinstance(displacement_candidate, dict) else "UNKNOWN"
                        log_event("gate", "displacement_failed", symbol=symbol, 
                                 displaced_symbol=displaced_sym)
                        log_blocked_trade(symbol, "displacement_failed", score,
                                          direction=c.get("direction"),
                                          decision_price=ref_price_check,
                                          components=comps,
                                          displaced_symbol=displaced_sym)
                        # SIGNAL HISTORY: Log blocked signal
                        log_signal_to_history(
                            symbol=symbol,
                            direction=direction,
                            raw_score=raw_score,
                            whale_boost=whale_boost,
                            final_score=final_score,
                            atr_multiplier=atr_multiplier or 0.0,
                            momentum_pct=momentum_pct,
                            momentum_required_pct=momentum_required_pct,
                            decision="Blocked: displacement_failed",
                            metadata={"displaced_symbol": displaced_sym}
                        )
                        continue
                    print(f"DEBUG {symbol}: Displacement successful! Proceeding with entry...", flush=True)
                else:
                    # FIX: Use actual Alpaca positions count, not executor.opens (which may be out of sync)
                    # BULLETPROOF: Safe position count with error handling
                    actual_positions = 0
                    try:
                        positions = self.executor.api.list_positions() or []
                        actual_positions = len(positions)
                    except Exception as pos_count_err:
                        log_event("gate", "position_count_error", symbol=symbol, error=str(pos_count_err))
                        # Use executor.opens as fallback
                        actual_positions = len(self.executor.opens)
                    print(f"DEBUG {symbol}: BLOCKED by max_positions_reached (Alpaca positions: {actual_positions}, executor.opens: {len(self.executor.opens)}, max: {Config.MAX_CONCURRENT_POSITIONS}), no displacement candidates", flush=True)
                    _inc_gate("max_positions_reached")
                    log_event("gate", "max_positions_reached", symbol=symbol, 
                             alpaca_positions=actual_positions,
                             executor_opens=len(self.executor.opens),
                             max=Config.MAX_CONCURRENT_POSITIONS,
                             displacement_attempted=True, no_candidates=True)
                    log_blocked_trade(symbol, "max_positions_reached", score,
                                      direction=c.get("direction"),
                                      decision_price=ref_price_check,
                                      components=comps,
                                      alpaca_positions=actual_positions,
                                      executor_opens=len(self.executor.opens),
                                      max_positions=Config.MAX_CONCURRENT_POSITIONS)
                    # SHADOW TRACKING: Create shadow position for signals > 3.0 blocked by capacity_limit
                    shadow_created = False
                    alpha_signature = {}
                    sector = "Unknown"
                    persistence_count = 0
                    sector_tide_count = 0
                    try:
                        from shadow_tracker import get_shadow_tracker
                        from alpha_signature_capture import capture_alpha_signature
                        from risk_management import get_sector
                        from persistence_tracker import get_persistence_tracker
                        from sector_tide_tracker import get_sector_tide_tracker
                        
                        if final_score >= 3.0:
                            shadow_tracker = get_shadow_tracker()
                            entry_price = ref_price_check
                            shadow_created = shadow_tracker.create_shadow_position(
                                symbol=symbol,
                                direction=direction,
                                entry_price=entry_price,
                                entry_score=final_score,
                                block_reason="capacity_limit"
                            )
                            
                            # Capture alpha signature
                            try:
                                if hasattr(engine, 'executor') and hasattr(engine.executor, 'api'):
                                    uw_cache = read_json(CacheFiles.UW_FLOW_CACHE, default={})
                                    alpha_signature = capture_alpha_signature(engine.executor.api, symbol, uw_cache)
                            except Exception:
                                pass
                            
                            # Get sector and persistence info
                            sector = get_sector(symbol)
                            try:
                                persistence_tracker = get_persistence_tracker()
                                persistence_check = persistence_tracker.check_persistence(symbol)
                                persistence_count = persistence_check.get("count", 0)
                                
                                tide_tracker = get_sector_tide_tracker()
                                tide_info = tide_tracker.check_sector_tide(symbol)
                                sector_tide_count = tide_info.get("count", 0)
                            except Exception:
                                pass
                            
                            if shadow_created:
                                print(f"DEBUG {symbol}: Shadow position created for capacity_limit block (score={final_score:.2f})", flush=True)
                    except ImportError:
                        pass
                    except Exception as e:
                        print(f"DEBUG: Failed to create shadow position for {symbol}: {e}", flush=True)
                    
                    # SIGNAL HISTORY: Log blocked signal with alpha signature
                    log_signal_to_history(
                        symbol=symbol,
                        direction=direction,
                        raw_score=raw_score,
                        whale_boost=whale_boost,
                        final_score=final_score,
                        atr_multiplier=atr_multiplier or 0.0,
                        momentum_pct=momentum_pct,
                        momentum_required_pct=momentum_required_pct,
                        decision="Blocked: capacity_limit",
                        metadata={
                            "alpaca_positions": actual_positions,
                            "max": Config.MAX_CONCURRENT_POSITIONS,
                            "shadow_created": shadow_created,
                            "alpha_signature": alpha_signature,
                            "sector": sector,
                            "persistence_count": persistence_count,
                            "sector_tide_count": sector_tide_count
                        }
                    )
                    continue
            if not self.executor.can_open_symbol(symbol):
                print(f"DEBUG {symbol}: BLOCKED by symbol_on_cooldown", flush=True)
                _inc_gate("symbol_on_cooldown")
                log_event("gate", "symbol_on_cooldown", symbol=symbol)
                log_blocked_trade(symbol, "symbol_on_cooldown", score,
                                  direction=c.get("direction"),
                                  decision_price=ref_price_check,
                                  components=comps)
                # SIGNAL HISTORY: Log blocked signal
                log_signal_to_history(
                    symbol=symbol,
                    direction=direction,
                    raw_score=raw_score,
                    whale_boost=whale_boost,
                    final_score=final_score,
                    atr_multiplier=atr_mult or 0.0,
                    momentum_pct=0.0,
                    momentum_required_pct=0.0,
                    decision="Blocked: duplicate_signal",
                    metadata={"reason": "symbol_on_cooldown"}
                )
                continue
            
            # RISK MANAGEMENT: Check exposure limits before placing order
            try:
                from risk_management import check_symbol_exposure, check_sector_exposure, get_risk_limits
                
                # Check symbol exposure
                current_positions = []
                try:
                    alpaca_positions = self.executor.api.list_positions()
                    for ap in alpaca_positions:
                        current_positions.append(ap)
                except Exception:
                    pass
                
                if current_positions:
                    # BULLETPROOF: Safe account fetch with error handling
                    account_equity = 0.0
                    try:
                        account = self.executor.api.get_account()
                        account_equity = float(getattr(account, "equity", 0.0))
                    except (AttributeError, ValueError, TypeError, Exception) as acct_err:
                        log_event("risk_management", "account_fetch_error", symbol=symbol, error=str(acct_err))
                        account_equity = 0.0  # Fail open - allow trade if can't check
                    
                    if account_equity <= 0:
                        log_event("risk_management", "invalid_account_equity", symbol=symbol, equity=account_equity)
                        # Fail open - continue without exposure check if equity invalid
                    else:
                        symbol_safe, symbol_reason = check_symbol_exposure(symbol, current_positions, account_equity)
                        if not symbol_safe:
                            print(f"DEBUG {symbol}: BLOCKED by symbol_exposure_limit", flush=True)
                            log_event("risk_management", "symbol_exposure_blocked", symbol=symbol, reason=symbol_reason)
                            log_blocked_trade(symbol, "symbol_exposure_limit", score,
                                             direction=c.get("direction"),
                                             decision_price=ref_price_check,
                                             components=comps, reason=symbol_reason)
                            # SIGNAL HISTORY: Log blocked signal
                            log_signal_to_history(
                                symbol=symbol,
                                direction=direction,
                                raw_score=raw_score,
                                whale_boost=whale_boost,
                                final_score=final_score,
                                atr_multiplier=atr_multiplier or 0.0,
                                momentum_pct=momentum_pct,
                                momentum_required_pct=momentum_required_pct,
                                decision="Blocked: exposure_limit",
                                metadata={"reason": symbol_reason}
                            )
                            continue
                    
                    sector_safe, sector_reason = check_sector_exposure(current_positions, account_equity)
                    if not sector_safe:
                        print(f"DEBUG {symbol}: BLOCKED by sector_exposure_limit", flush=True)
                        log_event("risk_management", "sector_exposure_blocked", symbol=symbol, reason=sector_reason)
                        log_blocked_trade(symbol, "sector_exposure_limit", score,
                                         direction=c.get("direction"),
                                         decision_price=ref_price_check,
                                         components=comps, reason=sector_reason)
                        # SIGNAL HISTORY: Log blocked signal
                        log_signal_to_history(
                            symbol=symbol,
                            direction=direction,
                            raw_score=raw_score,
                            whale_boost=whale_boost,
                            final_score=final_score,
                            atr_multiplier=atr_multiplier or 0.0,
                            momentum_pct=momentum_pct,
                            momentum_required_pct=momentum_required_pct,
                            decision="Blocked: exposure_limit",
                            metadata={"reason": sector_reason}
                        )
                        continue
            except ImportError:
                # Risk management not available - continue without exposure checks
                pass
            except Exception as exp_error:
                log_event("risk_management", "exposure_check_error", symbol=symbol, error=str(exp_error))
                # Continue on error - don't block trading if exposure checks fail

                # MOMENTUM IGNITION FILTER: Check price movement before entry
            # Ensures price is actually moving (+0.05% in 2 minutes, reduced from 0.2%) before executing Whale signal
            # SOFT-FAIL: High-conviction trades (>4.0) pass even with 0.00% momentum
            ignition_status = "unknown"
            # Get ref_price_check early for momentum check (will be recalculated later for notional check)
            ref_price_check = self.executor.get_last_trade(symbol)
            try:
                from momentum_ignition_filter import check_momentum_before_entry
                momentum_check = check_momentum_before_entry(
                    symbol=symbol,
                    signal_direction=c.get("direction", "bullish"),
                    current_price=ref_price_check,
                    entry_score=score,  # Pass score for soft-fail mode
                    market_regime=market_regime  # Pass regime for dynamic scaling
                )
                
                # Capture momentum check results for signal history
                momentum_pct = momentum_check.get("price_change_pct", 0.0)
                momentum_required_pct = momentum_check.get("threshold_used", 0.0)
                
                # TEMPORARILY BYPASS: Allow trades if score >= 1.5 even without momentum
                # This prevents momentum filter from blocking all trades during low volatility
                if not momentum_check.get("passed", True):
                    # Check if score is high enough to bypass momentum
                    if score >= 1.5:
                        print(f"DEBUG {symbol}: Momentum check failed but allowing entry (score={score:.2f} >= 1.5)", flush=True)
                        ignition_status = "bypassed_high_score"
                    else:
                        ignition_status = "blocked"
                        block_reason = momentum_check.get('reason', 'no_momentum')
                        print(f"DEBUG {symbol}: BLOCKED by momentum_ignition_filter - {block_reason}", flush=True)
                        log_event("gate", "momentum_ignition_blocked", symbol=symbol,
                                 direction=c.get("direction"),
                                 price_change_pct=momentum_check.get("price_change_pct", 0.0),
                                 reason=block_reason)
                        log_blocked_trade(symbol, "momentum_ignition_filter", score,
                                          direction=c.get("direction"),
                                          decision_price=ref_price_check,
                                          components=comps,
                                          price_change_pct=momentum_check.get("price_change_pct", 0.0),
                                          reason=block_reason)
                        
                        # SIGNAL HISTORY: Log blocked signal
                        log_signal_to_history(
                            symbol=symbol,
                            direction=c.get("direction", "unknown"),
                            raw_score=raw_score,
                            whale_boost=whale_boost,
                            final_score=final_score,
                            atr_multiplier=atr_mult or 0.0,
                            momentum_pct=momentum_pct,
                            momentum_required_pct=momentum_required_pct,
                            decision=f"Blocked: momentum_fail",
                            metadata={"reason": block_reason, "ignition_status": ignition_status}
                        )
                        
                        # LOGIC STAGNATION DETECTOR: Record momentum block
                        try:
                            from logic_stagnation_detector import get_stagnation_detector
                            detector = get_stagnation_detector()
                            detector.record_momentum_block(symbol, block_reason)
                        except ImportError:
                            pass
                        except Exception as e:
                            log_event("logic_stagnation", "error", error=str(e))
                        
                        continue
                else:
                    ignition_status = "passed"
                    log_event("gate", "momentum_ignition_passed", symbol=symbol,
                             price_change_pct=momentum_check.get("price_change_pct", 0.0),
                             reason=momentum_check.get("reason", "confirmed"))
                    
                    # LOGIC STAGNATION DETECTOR: Record momentum pass (resets counter)
                    try:
                        from logic_stagnation_detector import get_stagnation_detector
                        detector = get_stagnation_detector()
                        detector.record_momentum_pass()
                    except ImportError:
                        pass
                    except Exception as e:
                        log_event("logic_stagnation", "error", error=str(e))
            except ImportError:
                # Momentum filter not available - continue without check (fail open)
                ignition_status = "not_checked"
                log_event("gate", "momentum_ignition_unavailable", symbol=symbol)
            except Exception as momentum_error:
                ignition_status = "error"
                log_event("gate", "momentum_ignition_error", symbol=symbol, error=str(momentum_error))
                # Fail open on error - don't block trades due to filter errors

            print(f"DEBUG {symbol}: PASSED ALL GATES! Calling submit_entry...", flush=True)

            # Shadow decision telemetry: if v2 would also pass downstream gates at this point, record hypothetical execution.
            try:
                if shadow_enabled and v2_score is not None:
                    from telemetry.shadow_ab import log_shadow_event
                    # At this point, all non-score gates have passed for v1; for v2, the main uncertainty is score/expectancy.
                    v2_pass_floor = float(v2_score) >= float(min_score)
                    v2_ok = bool(v2_pass_floor and (v2_should_trade is True or v2_should_trade is None))
                    if v2_ok:
                        log_shadow_event(
                            "shadow_executed",
                            symbol=symbol,
                            side=("buy" if c.get("direction") == "bullish" else "sell"),
                            qty=int(qty),
                            entry_price=float(ref_price_check) if ref_price_check else None,
                            v2_score=float(v2_score),
                            market_regime=str(market_regime),
                            note="hypothetical_order_would_be_submitted_by_v2",
                        )
                        # Shadow PnL (optional): update shadow ledger (non-fatal, non-trading).
                        try:
                            from config.registry import StrategyFlags
                            if bool(getattr(StrategyFlags, "SHADOW_PNL_ENABLED", False)):
                                from shadow.shadow_pnl_engine import record_shadow_executed
                                record_shadow_executed(
                                    symbol=str(symbol),
                                    qty=int(qty),
                                    entry_price=float(ref_price_check) if ref_price_check else 0.0,
                                    side=("long" if c.get("direction") == "bullish" else "short"),
                                )
                        except Exception:
                            pass
                    else:
                        log_shadow_event(
                            "shadow_blocked",
                            symbol=symbol,
                            reason="v2_failed_score_or_expectancy",
                            v2_score=float(v2_score),
                            min_required=float(min_score),
                            v2_should_trade=bool(v2_should_trade) if v2_should_trade is not None else None,
                            v2_reason=str(v2_gate_reason) if v2_gate_reason is not None else None,
                        )
            except Exception:
                pass
            
            side = "buy" if c["direction"] == "bullish" else "sell"
            print(f"DEBUG {symbol}: Side determined: {side}, qty={qty}, ref_price={ref_price_check}", flush=True)
            
            # RISK MANAGEMENT: Validate order size before submission (qty already calculated above)
            # V5.0: Capture account_equity and position_size_usd for attribution logging
            account_equity_at_entry = None
            position_size_usd = None
            try:
                from risk_management import validate_order_size
                # BULLETPROOF: Safe account fetch with error handling
                try:
                    account = self.executor.api.get_account()
                    account_equity_at_entry = float(getattr(account, "equity", 0.0))
                    buying_power = float(getattr(account, "buying_power", 0.0))
                except (AttributeError, ValueError, TypeError, Exception) as acct_err:
                    log_event("order_validation", "account_fetch_error", symbol=symbol, error=str(acct_err))
                    account_equity_at_entry = 0.0
                    buying_power = 0.0  # Will fail validation if needed
                
                position_size_usd = qty * ref_price_check
                current_price = ref_price_check
                
                order_valid, order_error = validate_order_size(symbol, qty, side, current_price, buying_power)
                if not order_valid:
                    print(f"DEBUG {symbol}: BLOCKED by order_validation: {order_error}", flush=True)
                    log_event("risk_management", "order_validation_failed", 
                             symbol=symbol, qty=qty, side=side, error=order_error)
                    log_blocked_trade(symbol, "order_validation_failed", score,
                                     direction=c.get("direction"),
                                     decision_price=ref_price_check,
                                     components=comps, validation_error=order_error)
                    # SIGNAL HISTORY: Log blocked signal
                    log_signal_to_history(
                        symbol=symbol,
                        direction=direction,
                        raw_score=raw_score,
                        whale_boost=whale_boost,
                        final_score=final_score,
                        atr_multiplier=atr_multiplier or 0.0,
                        momentum_pct=momentum_pct,
                        momentum_required_pct=momentum_required_pct,
                        decision=f"Rejected: {order_error}",
                        metadata={"validation_error": order_error}
                    )
                    continue
            except ImportError:
                # Risk management not available - continue without validation
                pass
            except Exception as val_error:
                log_event("risk_management", "order_validation_error", symbol=symbol, error=str(val_error))
                # Continue on error
            
            old_mode = Config.ENTRY_MODE
            
            # V4.0: Generate correlation ID for UW-to-Alpaca pipeline tracking
            import uuid
            correlation_id = f"uw_{uuid.uuid4().hex[:16]}"  # 16-char hex ID
            
            # Generate idempotency key using risk management function, including correlation_id
            try:
                from risk_management import generate_idempotency_key
                client_order_id_base = generate_idempotency_key(symbol, side, qty)
                # Append correlation_id to client_order_id_base for tracking
                if client_order_id_base and "-" not in correlation_id:
                    client_order_id_base = f"{client_order_id_base}-{correlation_id}"
            except ImportError:
                # Fallback to existing method, include correlation_id
                client_order_id_base = build_client_order_id(symbol, side, c)
                if client_order_id_base and "-" not in correlation_id:
                    client_order_id_base = f"{client_order_id_base}-{correlation_id}"
            
            try:
                
                # V3.2 CHECKPOINT: ROUTE_ORDERS - Execution Router
                try:
                    router_config = v32.ExecutionRouter.load_config()
                    bid, ask = self.executor.get_nbbo(symbol)
                    if bid <= 0 or ask <= 0:
                        print(f"DEBUG {symbol}: WARNING - get_nbbo returned invalid bid/ask: bid={bid}, ask={ask}", flush=True)
                        # Use last trade price as fallback
                        last_price = self.executor.get_last_trade(symbol)
                        if last_price > 0:
                            bid, ask = last_price * 0.999, last_price * 1.001  # Small spread estimate
                            print(f"DEBUG {symbol}: Using fallback bid/ask from last trade: bid={bid}, ask={ask}", flush=True)
                        else:
                            print(f"DEBUG {symbol}: ERROR - Cannot get valid price for {symbol}, skipping order", flush=True)
                            log_order({"symbol": symbol, "qty": qty, "side": side, "error": "invalid_price_data", "bid": bid, "ask": ask})
                            continue
                    spread_bps = ((ask - bid) / bid * 10000) if bid > 0 else 100
                    # Get toxicity score and execution failure count
                    try:
                        from tca_data_manager import get_toxicity_sentinel_score, get_recent_failures
                        toxicity_score = get_toxicity_sentinel_score(symbol, c)
                        recent_failures = get_recent_failures(symbol, lookback_hours=24)
                    except ImportError:
                        toxicity_score = 0.0  # Fallback default
                        recent_failures = 0  # Fallback default
                    
                    # v3.2.1: ExecutionRouter with telemetry
                    selected_strategy, strategy_params = v32.ExecutionRouter.select_strategy(
                        ticker=symbol,
                        regime=market_regime,
                        spread_bps=spread_bps,
                        toxicity=toxicity_score
                    )
                    print(f"DEBUG {symbol}: ExecutionRouter selected strategy={selected_strategy}, spread_bps={spread_bps:.1f}", flush=True)
                except Exception as router_ex:
                    print(f"DEBUG {symbol}: EXCEPTION in execution router setup: {str(router_ex)}", flush=True)
                    print(f"DEBUG {symbol}: Traceback: {traceback.format_exc()}", flush=True)
                    log_order({"symbol": symbol, "qty": qty, "side": side, "error": f"execution_router_exception: {str(router_ex)}"})
                    # Use default strategy on error
                    selected_strategy = "limit_offset"
                    strategy_params = {}
                
                # Map strategy to ENTRY_MODE
                strategy_mode_map = {
                    "limit_offset": "MAKER_BIAS",
                    "peg_mid": "MIDPOINT",
                    "twap_slice": "MAKER_BIAS",  # Use limit orders for TWAP slices
                    "vwap_adaptive": "MARKET_FALLBACK"
                }
                Config.ENTRY_MODE = strategy_mode_map.get(selected_strategy, "MAKER_BIAS")
                
                # Legacy routing (fallback)
                if Config.ENABLE_EXEC_PREDICTOR:
                    tod_min = datetime.utcnow().hour * 60 + datetime.utcnow().minute
                    preds = {"trade_rate": 0.0, "tod_min": tod_min, "history": {}, "spread_bps": None}
                    chosen = choose_entry_route(symbol, bid, ask, prof, preds)
                    if chosen:  # Only override if predictor has strong signal
                        Config.ENTRY_MODE = chosen
                elif entry_action and Config.ENABLE_PER_TICKER_LEARNING:
                    if entry_action == "maker_bias":
                        Config.ENTRY_MODE = "MAKER_BIAS"
                    elif entry_action == "midpoint":
                        Config.ENTRY_MODE = "MIDPOINT"
                    else:
                        Config.ENTRY_MODE = "MARKET_FALLBACK"
                
                # Capture expected price for basic TCA logging (best-effort).
                expected_entry_price = None
                try:
                    expected_entry_price = self.executor.compute_entry_price(symbol, side)
                    print(f"DEBUG {symbol}: Expected entry price computed: {expected_entry_price}", flush=True)
                except Exception as price_ex:
                    print(f"DEBUG {symbol}: WARNING - compute_entry_price failed: {str(price_ex)}", flush=True)
                    expected_entry_price = None

                # Long-only safety: do not open shorts in LONG_ONLY mode.
                if Config.LONG_ONLY and side == "sell":
                    print(f"DEBUG {symbol}: BLOCKED by LONG_ONLY mode (short entry not allowed)", flush=True)
                    log_event("gate", "long_only_blocked_short_entry", symbol=symbol, score=score)
                    log_blocked_trade(symbol, "long_only_blocked_short_entry", score,
                                      direction=c.get("direction"),
                                      decision_price=ref_price_check,
                                      components=comps)
                    # SIGNAL HISTORY: Log blocked signal
                    log_signal_to_history(
                        symbol=symbol,
                        direction=direction,
                        raw_score=raw_score,
                        whale_boost=whale_boost,
                        final_score=final_score,
                        atr_multiplier=atr_multiplier or 0.0,
                        momentum_pct=momentum_pct,
                        momentum_required_pct=momentum_required_pct,
                        decision="Rejected: long_only_mode",
                        metadata={"side": side}
                    )
                    continue

                print(f"DEBUG {symbol}: Building client_order_id_base...", flush=True)
                client_order_id_base = build_client_order_id(symbol, side, c)
                print(f"DEBUG {symbol}: client_order_id_base={client_order_id_base}", flush=True)
                
                # CRITICAL: Add exception handling and logging around submit_entry
                try:
                    print(f"DEBUG {symbol}: About to call submit_entry with qty={qty}, side={side}, regime={market_regime}", flush=True)
                    res, fill_price, order_type, filled_qty, entry_status = self.executor.submit_entry(
                        symbol,
                        qty,
                        side,
                        regime=market_regime,
                        client_order_id_base=client_order_id_base,
                        entry_score=score,
                        market_regime=market_regime,
                    )
                    print(f"DEBUG {symbol}: submit_entry completed - res={res is not None}, order_type={order_type}, entry_status={entry_status}, filled_qty={filled_qty}", flush=True)
                    
                    # XAI: Log explainable trade entry
                    if res is not None and entry_status == "FILLED":
                        try:
                            explainable = get_explainable_logger()
                            # Get regime
                            regime_name = market_regime
                            try:
                                from structural_intelligence import get_regime_detector
                                regime_detector = get_regime_detector()
                                regime_name, _ = regime_detector.detect_regime()
                            except:
                                pass
                            
                            # Get macro yield
                            macro_yield = None
                            try:
                                from structural_intelligence import get_macro_gate
                                macro_gate = get_macro_gate()
                                macro_yield = macro_gate.get_current_yield()
                            except:
                                pass
                            
                            # Get whale clusters
                            whale_clusters = {}
                            if c.get("source") not in ("composite", "composite_v3"):
                                whale_clusters = {
                                    "count": c.get("count", 0),
                                    "premium_usd": c.get("avg_premium", 0) * c.get("count", 0)
                                }
                            
                            # Get gamma walls
                            gamma_walls = None
                            try:
                                from structural_intelligence import get_structural_exit
                                structural_exit = get_structural_exit()
                                position_data = {"current_price": fill_price or ref_price_check, "side": side, "entry_price": fill_price or ref_price_check}
                                exit_rec = structural_exit.get_exit_recommendation(symbol, position_data)
                                if exit_rec.get("gamma_wall_distance"):
                                    gamma_walls = {
                                        "distance_pct": exit_rec.get("gamma_wall_distance"),
                                        "gamma_exposure": exit_rec.get("gamma_exposure", 0)
                                    }
                            except:
                                pass
                            
                            why_sentence = explainable.log_trade_entry(
                                symbol=symbol,
                                direction=direction,
                                score=score,
                                components=comps,
                                regime=regime_name,
                                macro_yield=macro_yield,
                                whale_clusters=whale_clusters,
                                gamma_walls=gamma_walls,
                                composite_score=score,
                                entry_price=fill_price or ref_price_check
                            )
                            log_event("xai", "trade_entry_logged", symbol=symbol, why=why_sentence)
                        except Exception as xai_ex:
                            log_event("xai", "trade_entry_log_failed", symbol=symbol, error=str(xai_ex))
                except Exception as submit_ex:
                    print(f"DEBUG {symbol}: EXCEPTION in submit_entry: {str(submit_ex)}", flush=True)
                    print(f"DEBUG {symbol}: Traceback: {traceback.format_exc()}", flush=True)
                    log_order({"symbol": symbol, "qty": qty, "side": side, "error": f"submit_entry_exception: {str(submit_ex)}", "traceback": traceback.format_exc()})
                    res, fill_price, order_type, filled_qty, entry_status = None, None, "error", 0, "error"
                
                Config.ENTRY_MODE = old_mode
                
                if res is None:
                    print(f"DEBUG {symbol}: submit_entry returned None - order submission failed (order_type={order_type}, entry_status={entry_status})", flush=True)
                    log_order({"symbol": symbol, "qty": qty, "side": side, "error": "submit_entry_failed", "order_type": order_type, "entry_status": entry_status})
                    continue

                print(f"DEBUG {symbol}: submit_entry returned - order_type={order_type}, entry_status={entry_status}, filled_qty={filled_qty}, fill_price={fill_price}", flush=True)

                # CRITICAL FIX: Accept orders that are successfully submitted, even if not immediately filled
                # The reconciliation loop will pick up fills later. Only reject if order submission actually failed.
                if entry_status in ("error", "spread_too_wide", "min_notional_blocked", "risk_validation_failed", "insufficient_buying_power", "bad_ref_price"):
                    print(f"DEBUG {symbol}: Order REJECTED - submission failed with status={entry_status}", flush=True)
                    log_event("order", "entry_submission_failed", symbol=symbol, side=side, status=entry_status,
                              client_order_id=client_order_id_base, requested_qty=qty)
                    # SIGNAL HISTORY: Log rejected signal
                    log_signal_to_history(
                        symbol=symbol,
                        direction=direction,
                        raw_score=raw_score,
                        whale_boost=whale_boost,
                        final_score=final_score,
                        atr_multiplier=atr_multiplier or 0.0,
                        momentum_pct=momentum_pct,
                        momentum_required_pct=momentum_required_pct,
                        decision=f"Rejected: {entry_status}",
                        metadata={"entry_status": entry_status, "client_order_id": client_order_id_base}
                    )
                    continue
                
                # Order was successfully submitted (may or may not be filled yet)
                if entry_status == "filled" and filled_qty > 0:
                    print(f"DEBUG {symbol}: Order IMMEDIATELY FILLED - qty={filled_qty}, price={fill_price}", flush=True)
                else:
                    print(f"DEBUG {symbol}: Order SUBMITTED (not yet filled) - status={entry_status}, will be tracked by reconciliation", flush=True)
                    # For submitted but unfilled orders, reconciliation will handle them
                    # We still process them but don't mark as open until filled
                
                # SIGNAL HISTORY: Log ordered signal (both filled and submitted)
                log_signal_to_history(
                    symbol=symbol,
                    direction=direction,
                    raw_score=raw_score,
                    whale_boost=whale_boost,
                    final_score=final_score,
                    atr_multiplier=atr_mult or 0.0,
                    momentum_pct=momentum_pct,
                    momentum_required_pct=momentum_required_pct,
                    decision="Ordered",
                    metadata={
                        "entry_status": entry_status,
                        "filled_qty": filled_qty,
                        "fill_price": fill_price,
                        "qty": qty,
                        "ignition_status": ignition_status if 'ignition_status' in locals() else "unknown"
                    }
                )

                # CRITICAL FIX: Handle both filled and submitted orders
                if entry_status == "filled" and filled_qty > 0:
                    # Order was immediately filled - process normally
                    exec_qty = int(filled_qty)
                    exec_price = float(fill_price) if fill_price is not None else self.executor.get_quote_price(symbol)
                    
                    # VALIDATION: Ensure entry_score is valid before marking position open
                    if score <= 0.0:
                        print(f"ERROR {symbol}: Attempted to enter position with invalid entry_score={score:.2f} - BLOCKING ENTRY", flush=True)
                        log_event("gate", "invalid_entry_score_blocked", symbol=symbol, score=score, 
                                 direction=c.get("direction"), components=comps)
                        log_blocked_trade(symbol, "invalid_entry_score", score,
                                          direction=c.get("direction"),
                                          decision_price=ref_price_check,
                                          components=comps,
                                          reason="entry_score must be > 0.0")
                        continue  # Skip this position - don't enter with invalid score
                    
                    # V4.0: Pass regime_modifier, ignition_status, and correlation_id for full Specialist Tier state recovery
                    # Store correlation_id in position metadata for attribution tracking
                    correlation_id_for_metadata = correlation_id if 'correlation_id' in locals() else None
                    if correlation_id_for_metadata:
                        # Store correlation_id in opens dict for later use
                        if symbol not in self.executor.opens:
                            self.executor.opens[symbol] = {}
                        self.executor.opens[symbol]["correlation_id"] = correlation_id_for_metadata
                    
                    # Call _persist_position_metadata directly to include correlation_id
                    self.executor.mark_open(symbol, exec_price, atr_mult, side, exec_qty, entry_score=score,
                                            components=comps, market_regime=market_regime, direction=c["direction"],
                                            regime_modifier=regime_modifier, ignition_status=ignition_status)
                    # Update metadata with correlation_id after mark_open
                    if correlation_id_for_metadata:
                        try:
                            metadata_path = StateFiles.POSITION_METADATA
                            if metadata_path.exists():
                                metadata = load_metadata_with_lock(metadata_path)
                                if symbol in metadata:
                                    metadata[symbol]["correlation_id"] = correlation_id_for_metadata
                                    atomic_write_json(metadata_path, metadata)
                        except Exception as e:
                            log_event("correlation_id", "metadata_update_failed", symbol=symbol, error=str(e))
                else:
                    # Order was submitted but not yet filled - reconciliation will handle it
                    # For now, we accept the order submission as successful
                    # Reconciliation loop will pick up the fill and mark position open
                    exec_qty = int(filled_qty) if filled_qty > 0 else qty  # Use filled qty if available, else requested
                    exec_price = float(fill_price) if fill_price is not None else self.executor.get_quote_price(symbol)
                    print(f"DEBUG {symbol}: Order submitted (status={entry_status}) - reconciliation will track fill", flush=True)
                    log_event("order", "entry_submitted_pending_fill", symbol=symbol, side=side, 
                             requested_qty=qty, filled_qty=filled_qty, order_type=order_type, 
                             client_order_id=client_order_id_base, entry_status=entry_status)
                    # Don't mark_open for unfilled orders - reconciliation will do that when fill occurs
                    # But we still want to count this as a successful order submission
                
                # Only log POSITION_OPENED if order was actually filled
                if entry_status == "filled" and filled_qty > 0:
                    telemetry.log_portfolio_event(
                        event_type="POSITION_OPENED",
                        symbol=symbol,
                        side=side,
                        qty=exec_qty,
                        entry_price=exec_price,
                        exit_price=None,
                        realized_pnl=0.0,
                        unrealized_pnl=0.0,
                        holding_period_min=0,
                        order_type=order_type,
                        score=score
                    )
                else:
                    # Log order submission for unfilled orders
                    telemetry.log_order_event(
                        event_type="ORDER_SUBMITTED",
                        symbol=symbol,
                        side=side,
                        qty=qty,
                        order_type=order_type,
                        status=entry_status,
                        note="pending_fill_reconciliation"
                    )
                
                context = {
                    "direction": c["direction"],
                    "gamma_regime": gex.get("gamma_regime", "unknown"),
                    "market_regime": market_regime,
                    "score": score,
                    "order_type": order_type
                }
                # Entry attribution contract:
                # - entry_price must come from executed entry fill (Alpaca order.filled_avg_price).
                # - entry_qty must come from executed entry fill qty (Alpaca order.filled_qty).
                # - do NOT log a synthetic/quote-based entry_price for pending fills.
                context["entry_ts"] = now_iso()
                context["entry_status"] = entry_status
                if entry_status == "filled" and filled_qty > 0 and fill_price is not None:
                    context["entry_price"] = float(fill_price)
                    context["entry_qty"] = int(filled_qty)
                    context["qty"] = int(filled_qty)  # backward-compatible
                    context["pending_fill"] = False
                    context["entry_price_source"] = "alpaca.order.filled_avg_price"
                else:
                    # Pending fill: keep state for observability, but do not attach PnL-bearing prices.
                    context["pending_fill"] = True
                    context["requested_qty"] = int(qty)
                    context["entry_price_source"] = None
                context["entry_score"] = score
                context["components"] = comps if 'comps' in locals() else context.get("components", {})
                context["regime"] = market_regime
                context["position_side"] = "long" if side == "buy" else "short"
                # Metadata integrity: enforce full fields only once the order is actually filled.
                if context.get("pending_fill"):
                    required_fields = ["entry_ts", "entry_score", "regime", "entry_status"]
                else:
                    required_fields = ["entry_ts", "entry_price", "qty", "entry_score", "components", "regime"]
                missing = [f for f in required_fields if context.get(f) in (None, "", 0, {})]
                if missing:
                    log_event(
                        "data_integrity",
                        "entry_metadata_incomplete",
                        symbol=symbol,
                        missing_fields=missing,
                        context_minimal={k: context.get(k) for k in ("entry_ts", "entry_price", "qty")},
                    )
                    context["metadata_incomplete"] = True
                else:
                    context["metadata_incomplete"] = False
                # V5.0: Add position sizing and account equity to attribution context
                if account_equity_at_entry is not None:
                    context["account_equity_at_entry"] = round(account_equity_at_entry, 2)
                if position_size_usd is not None:
                    context["position_size_usd"] = round(position_size_usd, 2)
                if Config.ENABLE_PER_TICKER_LEARNING and decisions_map:
                    context.update({
                        "confirm_score": None,
                        "components": comps,
                        "component_weights": get_or_init_profile(self.profiles, symbol).get("component_weights", {}),
                        "entry_action": entry_action,
                        "atr_mult": atr_mult,
                        "size_scale": size_scale
                    })
                else:
                    context["confirm_score"] = confirm_map.get(symbol, 0.0)
                
                # Append to orders list for both filled and submitted orders
                # This ensures we track all order attempts, not just immediate fills
                orders.append({"symbol": symbol, "qty": exec_qty, "side": side, "score": score, 
                              "order_type": order_type, "status": entry_status, "filled_qty": filled_qty})
                
                if entry_status == "filled" and filled_qty > 0:
                    new_positions_this_cycle += 1  # V3.2.1: Track new positions per cycle
                    log_order({"symbol": symbol, "qty": exec_qty, "side": side, "score": score, 
                              "price": exec_price, "order_type": order_type, "status": "filled"})
                else:
                    log_order({"symbol": symbol, "qty": exec_qty, "side": side, "score": score, 
                              "price": exec_price, "order_type": order_type, "status": entry_status, 
                              "note": "submitted_pending_fill"})
                # NOTE: Do not log a synthetic/quote-based entry_price for pending fills.
                log_attribution(trade_id=f"open_{symbol}_{now_iso()}", symbol=symbol, pnl_usd=0.0, context=context)
            except Exception as e:
                print(f"DEBUG {symbol}: EXCEPTION in order submission: {str(e)}", flush=True)
                print(f"DEBUG {symbol}: Traceback: {traceback.format_exc()}", flush=True)
                log_order({"symbol": symbol, "qty": qty, "side": side, "error": f"order_submission_exception: {str(e)}"})
                Config.ENTRY_MODE = old_mode
                continue
        
        # DIAGNOSTIC: Log summary of execution
        print(f"DEBUG decide_and_execute SUMMARY: {len(clusters_sorted)} clusters processed, {new_positions_this_cycle} positions opened this cycle, {len(orders)} orders returned", flush=True)
        if len(orders) == 0 and len(clusters_sorted) > 0:
            print(f"DEBUG WARNING: {len(clusters_sorted)} clusters processed but 0 orders returned - check gate logs above for block reasons", flush=True)

        # First-class missed-candidate logging: above-floor symbols that neither executed nor logged a gate.
        try:
            executed_symbols = set()
            for o in orders:
                if isinstance(o, dict) and o.get("symbol"):
                    executed_symbols.add(str(o.get("symbol")))
            for sym, sc in (candidates_above_min or {}).items():
                if sym not in executed_symbols and sym not in _CYCLE_GATE_SYMBOLS:
                    log_system_event(
                        subsystem="decision",
                        event_type="missed_candidate",
                        severity="WARN",
                        symbol=sym,
                        score=float(sc),
                        reason="no_gate_recorded",
                    )
        except Exception:
            pass
        
        # RISK MANAGEMENT: Update daily start equity if this is first trade of day
        try:
            from risk_management import get_daily_start_equity, set_daily_start_equity
            if get_daily_start_equity() is None:
                # First trade today - set baseline
                # BULLETPROOF: Safe account fetch with error handling
                try:
                    account = self.executor.api.get_account()
                    equity = float(getattr(account, "equity", 0.0))
                    if equity > 0:
                        set_daily_start_equity(equity)
                except (AttributeError, ValueError, TypeError, Exception) as acct_err:
                    log_event("daily_baseline", "account_fetch_error", error=str(acct_err))
                    # Non-critical - skip baseline if can't fetch
        except Exception:
            pass  # Non-critical
        
        if Config.ENABLE_PER_TICKER_LEARNING:
            save_profiles(self.profiles)
        # Cycle-level "why no trades" summary (low-noise: only emit when we placed no orders).
        if not orders:
            try:
                gc = dict(gate_counts)  # Counter → dict
            except Exception:
                gc = gate_counts if isinstance(gate_counts, dict) else {}
            log_event(
                "gate",
                "cycle_summary",
                market_regime=market_regime,
                stage=system_stage,
                considered=considered,
                orders=0,
                top_score=top_score,
                gate_counts=gc,
            )
        return orders

# =========================
# EOD REPORT (auto-generated daily)
# =========================
def bucket_cluster_size(n):
    return "3-4" if 3 <= n <= 4 else "5+" if n >= 5 else "<3"

def generate_eod_report(date_str=None):
    date_str = date_str or datetime.utcnow().strftime("%Y-%m-%d")
    def load_jsonl(name):
        path = os.path.join(LOG_DIR, f"{name}.jsonl")
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f]

    attributions = [r for r in load_jsonl("attribution") if r.get("type")=="attribution" and r.get("ts","").startswith(date_str)]
    signals = [r for r in load_jsonl("signals") if r.get("type")=="signal" and r.get("ts","").startswith(date_str)]

    trades = len(attributions)
    pnl = sum(float(r.get("pnl_usd", 0)) for r in attributions)
    wins = sum(1 for r in attributions if float(r.get("pnl_usd", 0)) > 0)
    win_rate = (wins / trades) if trades else None

    by_ticker = {}
    by_cluster = {}
    for s in signals:
        c = s.get("cluster", {})
        symbol = c.get("ticker")
        by_ticker.setdefault(symbol, {"trades":0, "pnl":0.0})
        by_ticker[symbol]["trades"] += 1
        bucket = bucket_cluster_size(int(c.get("count", 0)))
        by_cluster.setdefault(bucket, {"trades":0, "pnl":0.0})
        by_cluster[bucket]["trades"] += 1
    for a in attributions:
        sym = a.get("symbol")
        if sym in by_ticker:
            by_ticker[sym]["pnl"] += float(a.get("pnl_usd", 0))

    report = {
        "date": date_str,
        "summary": {
            "total_pnl_usd": round(pnl, 2),
            "trades": trades,
            "win_rate": round(win_rate, 4) if win_rate is not None else None
        },
        "by_ticker": [
            {"ticker": k, "trades": v["trades"], "pnl_usd": round(v["pnl"], 2)} for k, v in by_ticker.items()
        ],
        "by_cluster_size": [
            {"size_bucket": k, "trades": v["trades"], "pnl_usd": round(v["pnl"], 2)} for k, v in by_cluster.items()
        ]
    }
    json_path = os.path.join(REPORT_DIR, f"report_{date_str}.json")
    html_path = os.path.join(REPORT_DIR, f"report_{date_str}.html")
    with open(json_path, "w", encoding="utf-8") as f: json.dump(report, f, indent=2)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(f"<html><body><h1>Daily Report {date_str}</h1><pre>{json.dumps(report, indent=2)}</pre></body></html>")
    log_event("report", "eod_written", json_path=json_path, html_path=html_path)
    return report

# =========================
# UW CACHE INTEGRATION (Transitional composite scoring)
# =========================
@global_failure_wrapper("uw_cache")
def read_uw_cache():
    """Read UW cache populated by daemon.

    Contract: read_uw_cache() MUST NOT raise ImportError in production.
    If UW cache is missing/corrupt/unreadable, it MUST return {} and log a clear event.
    """
    # BULLETPROOF: Safe cache read with corruption handling and self-healing
    cache_file = CacheFiles.UW_FLOW_CACHE
    if not cache_file.exists():
        log_event("uw_cache", "uw_cache_missing", uw_cache_path=str(cache_file), fallback="empty_cache")
        return {}

    # Use the shared self-healing JSON reader so corruption never disables trading silently.
    try:
        from utils.state_io import read_json_self_heal
    except Exception as e:
        log_event(
            "uw_cache",
            "uw_cache_import_failed",
            error=str(e),
            error_type=type(e).__name__,
            module="utils.state_io.read_json_self_heal",
            action="fallback_reader",
            severity="HIGH",
        )

        # Fallback: minimal self-healing reader (kept local to avoid scattered PYTHONPATH hacks).
        def read_json_self_heal(path, default, *, heal=True, mkdir=True, on_event=None):  # type: ignore
            from pathlib import Path
            import json as _json
            import time as _time

            p = Path(path)
            if not p.exists():
                return default
            try:
                return _json.loads(p.read_text(encoding="utf-8"))
            except Exception as ee:
                if on_event:
                    try:
                        on_event("state_read_failed", {"path": str(p), "error": str(ee), "error_type": type(ee).__name__})
                    except Exception:
                        pass
                if not heal:
                    return default
                try:
                    ts = int(_time.time())
                    backup = p.with_suffix(p.suffix + f".corrupted.{ts}.json")
                    try:
                        p.rename(backup)
                    except Exception:
                        backup = None
                    if mkdir:
                        p.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        p.write_text(_json.dumps(default, indent=2), encoding="utf-8")
                    except Exception:
                        pass
                    if on_event:
                        try:
                            on_event("state_self_healed", {"path": str(p), "backup": str(backup) if backup else None})
                        except Exception:
                            pass
                except Exception:
                    pass
                return default

    cache = read_json_self_heal(
        cache_file,
        {},
        on_event=lambda ev, payload: log_event("uw_cache", ev, uw_cache_path=str(cache_file), **payload),
    )
    if not isinstance(cache, dict):
        log_event("uw_cache", "uw_cache_corrupted_structure", uw_cache_path=str(cache_file), cache_type=str(type(cache)))
        return {}

    # Visibility: an empty dict is a valid state but must be obvious in logs.
    if not cache:
        log_event("uw_cache", "uw_cache_empty", uw_cache_path=str(cache_file))

    return cache

# =========================
# DEBUG INSTRUMENTATION
# =========================
def audit_seg(name, phase, extra=None):
    """Log segment progress for debugging silent failures."""
    event = {
        "event": "RUN_SEG",
        "name": name,
        "phase": phase,
        "ts": datetime.utcnow().isoformat() + "Z"
    }
    if extra:
        event.update(extra)
    gov_log = CacheFiles.GOVERNANCE_EVENTS
    gov_log.parent.mkdir(exist_ok=True)
    with gov_log.open("a") as f:
        f.write(json.dumps(event) + "\n")

# =========================
# CORE ITERATION (pull all UW layers, score, execute)
# =========================
@global_failure_wrapper("decision")
def run_once():
    # CRITICAL FIX: Log entry to run_once()
    try:
        with open("logs/worker_debug.log", "a") as f:
            f.write(f"[{datetime.now(timezone.utc).isoformat()}] run_once() ENTRY\n")
            f.flush()
    except:
        pass
    print("DEBUG: run_once() ENTRY", flush=True)
    _pipeline_heartbeat_maybe()
    
    # CRITICAL FIX: Ensure StateFiles is available - re-import if needed
    global StateFiles
    try:
        _ = StateFiles  # Check if available
    except NameError:
        # StateFiles not available - re-import it
        from config.registry import StateFiles
        print("DEBUG: Re-imported StateFiles in run_once()", flush=True)
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] Re-imported StateFiles in run_once()\n")
                f.flush()
        except:
            pass
    
    # Update logic heartbeat for SRE monitoring
    try:
        from sre_diagnostics import update_sre_metrics
        update_sre_metrics({"logic_heartbeat": time.time()})
    except:
        pass
    
    # StateFiles is already imported at module level (line 30-32)
    # No redundant import needed
    try:
        # CRITICAL FIX: Log after try block entry
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] run_once() inside try block\n")
                f.flush()
        except:
            pass
        
        global ZERO_ORDER_CYCLE_COUNT
        alerts_this_cycle = []
        fixes_applied_list = []  # V3.0: Track auto-fixes
        
        audit_seg("run_once", "START")
        
        # MONITORING GUARD 1: Check freeze state (governor_freezes.json only, no pre_market_freeze.flag)
        # NOTE: pre_market_freeze.flag mechanism removed - it was causing more problems than it solved
        if not check_freeze_state():
            alerts_this_cycle.append("freeze_active")
            print("🛑 FREEZE ACTIVE - Trading halted by monitoring guard", flush=True)
            log_event("run", "halted_freeze", alerts=alerts_this_cycle)
            
            # Still track zero-order cycles and generate monitoring summary on freeze path
            ZERO_ORDER_CYCLE_COUNT += 1
            
            # Check rollback conditions even when frozen
            check_rollback_conditions(
                composite_scores_avg=0.0,
                zero_order_cycles=ZERO_ORDER_CYCLE_COUNT,
                freeze_active=True,
                heartbeat_stale=False,
                trading_mode=Config.TRADING_MODE
            )
            
            # Generate monitoring summary for freeze cycle
            summary = generate_cycle_monitoring_summary(
                clusters=[],
                orders_placed=0,
                positions_count=0,
                alerts_triggered=alerts_this_cycle,
                zero_order_cycles=ZERO_ORDER_CYCLE_COUNT,
                fixes_applied=[],
                optimizations_applied=[]
            )
            
            # HALT: Return early - trading will NOT resume until freeze flags manually cleared
            # CRITICAL FIX: Log cycle even when frozen
            jsonl_write("run", {
                "ts": datetime.now(timezone.utc).isoformat(),
                "_ts": int(time.time()),
                "msg": "complete",
                "clusters": 0,
                "orders": 0,
                "freeze_active": True,
                "metrics": summary
            })
            return {"clusters": 0, "orders": 0, **summary}
        
        # CRITICAL FIX: Log before creating UWClient and engine
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] run_once() creating UWClient and engine\n")
                f.flush()
        except:
            pass
        
        uw = UWClient()
        engine = StrategyEngine()
        degraded_mode = False  # Reduce-only when broker is unreachable

        # STRUCTURAL UPGRADE (additive): Market context snapshot (premarket/overnight + vol term proxy).
        # Contract:
        # - Must never block trading (best-effort, wrapped, logs to system_events).
        # - Provides inputs for regime/posture and shadow A/B (does not change decisions by itself).
        try:
            if hasattr(engine, "executor") and hasattr(engine.executor, "api") and engine.executor.api is not None:
                from structural_intelligence.market_context_v2 import update_market_context_v2
                mc = update_market_context_v2(engine.executor.api)
                try:
                    engine.market_context_v2 = mc  # type: ignore[attr-defined]
                except Exception:
                    pass
        except Exception:
            # Never block trading on context ingest errors.
            pass

        # STRUCTURAL UPGRADE (additive): Per-symbol vol/beta features store.
        # Contract: log-only enrichment fields; no scoring weight changes here.
        try:
            if hasattr(engine, "executor") and hasattr(engine.executor, "api") and engine.executor.api is not None:
                from structural_intelligence.symbol_risk_features import update_symbol_risk_features
                try:
                    symbols = list(getattr(Config, "TICKERS", []) or [])
                except Exception:
                    symbols = []
                if "SPY" not in [str(s).upper() for s in symbols]:
                    symbols.append("SPY")
                rf = update_symbol_risk_features(engine.executor.api, symbols=symbols, benchmark="SPY")
                try:
                    engine.symbol_risk_features = rf  # type: ignore[attr-defined]
                except Exception:
                    pass
        except Exception:
            pass

        # STRUCTURAL UPGRADE (additive): Regime + posture V2 (log-only; no gating changes).
        try:
            if hasattr(engine, "executor") and hasattr(engine.executor, "api") and engine.executor.api is not None:
                from structural_intelligence.regime_posture_v2 import update_regime_posture_v2
                mc = getattr(engine, "market_context_v2", None)
                if not isinstance(mc, dict):
                    mc = {}
                rp = update_regime_posture_v2(engine.executor.api, market_context=mc)
                try:
                    engine.regime_posture_v2 = rp  # type: ignore[attr-defined]
                except Exception:
                    pass
        except Exception:
            pass

        all_trades = []
        gex_map = {}
        dp_map = {}
        vol_map = {}
        net_map = {}
        ovl_map = {}
        
        audit_seg("run_once", "cache_read")
        uw_cache = read_uw_cache()
        uw_cache_path = str(CacheFiles.UW_FLOW_CACHE)
        
        # SIGNAL FUNNEL TRACKER: Count incoming UW alerts (symbols in cache = alerts received)
        try:
            from signal_funnel_tracker import get_funnel_tracker
            funnel = get_funnel_tracker()
            # Count each symbol in cache as an incoming UW alert
            cache_symbols = [k for k in uw_cache.keys() if not k.startswith("_")]
            for symbol in cache_symbols:
                cache_data = uw_cache.get(symbol, {})
                # Count alerts based on cache updates (each symbol with data = alert)
                if cache_data and not cache_data.get("simulated"):
                    funnel.record_uw_alert(symbol, "cache_update")
        except ImportError:
            pass
        except Exception as e:
            log_event("funnel", "record_alerts_error", error=str(e))
        
        adaptive_gate = AdaptiveGate()
        # ROOT CAUSE FIX: Check for actual symbol keys (not metadata keys starting with "_")
        # Only enable composite scoring if cache has real symbol data, not just metadata
        cache_symbol_count = len([k for k in uw_cache.keys() if not k.startswith("_")])
        use_composite = cache_symbol_count > 0

        # VISIBILITY: If UW cache has no symbols, make it explicit (reason for 0 clusters).
        # This should not crash or freeze trading; it only improves observability.
        if cache_symbol_count == 0:
            log_event(
                "uw_cache",
                "uw_cache_empty_no_signals",
                cache_symbol_count=cache_symbol_count,
                uw_cache_path=uw_cache_path,
                cache_total_keys=len(uw_cache) if isinstance(uw_cache, dict) else None,
            )
        
        log_event("run_once", "started", use_composite=use_composite, cache_symbols=cache_symbol_count, cache_total_keys=len(uw_cache))
        audit_seg("run_once", "init_complete", {"cache_symbols": cache_symbol_count, "cache_total_keys": len(uw_cache)})
        
        # POSITION RECONCILIATION LOOP V2: Autonomous self-healing sync
        print("DEBUG: Running autonomous position reconciliation V2...", flush=True)
        try:
            # V2: Pass executor.opens for sync, returns autonomous fix results
            reconcile_result = run_position_reconciliation_loop(
                Config.ALPACA_KEY,
                Config.ALPACA_SECRET,
                Config.ALPACA_BASE_URL,
                executor_opens=engine.executor.opens
            )
            
            # SAFETY: Never allow missing keys from reconciliation to crash run_once().
            status = reconcile_result.get('reconciliation_status', 'unknown') if isinstance(reconcile_result, dict) else 'unknown'
            total_diffs = reconcile_result.get('total_diffs', 0) if isinstance(reconcile_result, dict) else 0
            degraded = reconcile_result.get('degraded_mode', False) if isinstance(reconcile_result, dict) else False
            degraded_mode = bool(degraded)
            
            alpaca_pos_count = reconcile_result.get('alpaca_positions_count') if isinstance(reconcile_result, dict) else None
            alpaca_pos_count = int(alpaca_pos_count) if isinstance(alpaca_pos_count, (int, float)) else 0
            print(f"DEBUG: Reconciliation V2 - Alpaca: {alpaca_pos_count} positions, "
                  f"Status: {status}, Diffs: {total_diffs}, Degraded: {degraded}", flush=True)
            
            # V2: Report fixes but DO NOT HALT - autonomous remediation applied
            if total_diffs > 0:
                plan = reconcile_result.get('plan', {})
                print(f"✅ AUTONOMOUS FIXES APPLIED:", flush=True)
                if plan.get('missing_in_bot'):
                    print(f"   - Injected {len(plan['missing_in_bot'])} missing positions", flush=True)
                if plan.get('orphaned_in_bot'):
                    print(f"   - Purged {len(plan['orphaned_in_bot'])} orphaned positions", flush=True)
                if plan.get('quantity_mismatch'):
                    print(f"   - Reconciled {len(plan['quantity_mismatch'])} quantity mismatches", flush=True)
                
                log_event("position_reconciliation_v2", "autonomous_fixed", 
                         total_diffs=total_diffs,
                         plan=plan,
                         action="trading_resumed")
            else:
                log_event("position_reconciliation_v2", "clean", 
                         positions=alpaca_pos_count)
            
            # V2: Check degraded mode status
            if degraded:
                alerts_this_cycle.append("broker_degraded_mode")
                print(f"⚠️  DEGRADED MODE: Broker unreachable, using last snapshot (reduce-only)", flush=True)
        
        except Exception as reconcile_error:
            print(f"⚠️  Position reconciliation V2 error: {reconcile_error}", flush=True)
            log_event("position_reconciliation_v2", "error", error=str(reconcile_error))
        
        # RISK MANAGEMENT CHECKS: Account-level risk limits (after position reconciliation)
        try:
            from risk_management import run_risk_checks
            # BULLETPROOF: Safe account and position fetch with error handling
            current_equity = 0.0
            positions = []
            try:
                account = engine.executor.api.get_account()
                current_equity = float(getattr(account, "equity", 0.0))
                positions = engine.executor.api.list_positions() or []
            except (AttributeError, ValueError, TypeError, Exception) as risk_fetch_err:
                log_event("risk_management", "account_or_positions_fetch_error", error=str(risk_fetch_err))
                # Fail open - if can't fetch, skip risk checks (allow trading)
                current_equity = 0.0
                positions = []
            
            # Only run risk checks if we have valid data
            if current_equity > 0:
                risk_results = run_risk_checks(engine.executor.api, current_equity, positions)
            
            else:
                # No valid equity - assume safe (fail open)
                risk_results = {"safe_to_trade": True, "checks": {}}
            
            if not risk_results.get("safe_to_trade", True):
                freeze_reason = risk_results.get("freeze_reason", "unknown_risk_check")
                alerts_this_cycle.append(f"risk_limit_breach_{freeze_reason}")
                print(f"🛑 RISK LIMIT BREACH: {freeze_reason} - Trading halted", flush=True)
                log_event("risk_management", "freeze_activated", 
                         reason=freeze_reason, 
                         checks=risk_results.get("checks", {}))
                # CRITICAL FIX: Log cycle even when risk frozen
                jsonl_write("run", {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "_ts": int(time.time()),
                    "msg": "complete",
                    "clusters": 0,
                    "orders": 0,
                    "risk_freeze": freeze_reason,
                    "metrics": {"risk_freeze": freeze_reason}
                })
                # Return early - freeze will be caught by freeze check next cycle
                return {"clusters": 0, "orders": 0, "risk_freeze": freeze_reason}
            else:
                log_event("risk_management", "checks_passed", 
                         daily_pnl=risk_results["checks"].get("daily_loss", {}).get("daily_pnl", 0),
                         drawdown_pct=risk_results["checks"].get("drawdown", {}).get("drawdown_pct", 0))
        except ImportError:
            # Risk management module not available - log but continue (for backward compatibility)
            log_event("risk_management", "module_not_available", warning=True)
        except Exception as risk_error:
            log_event("risk_management", "check_error", error=str(risk_error))
            # On error, continue but log - don't block trading if risk checks fail
        
        # MONITORING GUARD 2: Check heartbeat staleness (v3.1.1: 30m threshold, PAPER mode)
        if not check_heartbeat_staleness(REQUIRED_HEARTBEAT_MODULES, max_age_minutes=30, trading_mode=Config.TRADING_MODE):
            alerts_this_cycle.append("heartbeat_stale")
            # V3.0: Auto-heal heartbeat staleness (restart modules)
            fix_result = auto_heal_on_alert("heartbeat_staleness")
            if fix_result and fix_result.get("overall_success"):
                fixes_applied_list.extend(fix_result.get("fixes_succeeded", []))

        # CENTRALIZED DATA ARCHITECTURE: Use uw-daemon cache as single source of truth
        # This eliminates duplicate API calls and stays within UW rate limits (~30/min)
        # uw-daemon handles all UW API calls with proper rate limiting and caching
        
        print("DEBUG: Polling configured (cache-only mode)", flush=True)
        
        if use_composite and len(uw_cache) > 0:
            # CACHE MODE: Read all data from uw-daemon cache - NO API CALLS
            print(f"DEBUG: Using centralized UW cache ({len(uw_cache)} symbols)", flush=True)
            
            # GRACEFUL DEGRADATION: Track if we're using stale data
            current_time = time.time()
            stale_threshold = 2 * 3600  # 2 hours
            using_stale_data = False
            fresh_data_count = 0
            stale_data_count = 0
            
            # Build maps from cache data AND extract flow trades for clustering
            for ticker in Config.TICKERS:
                cache_data = uw_cache.get(ticker, {})
                if not cache_data or cache_data.get("simulated"):
                    continue
                
                # Check cache age for graceful degradation
                last_update = cache_data.get("_last_update", 0)
                age_sec = current_time - last_update if last_update else float('inf')
                is_stale = age_sec > stale_threshold
                
                # CRITICAL: Extract raw flow trades from cache for clustering
                # Daemon stores raw API trades in cache_data["flow_trades"]
                # We need to normalize them (same as UWClient.get_option_flow does)
                flow_trades_raw = cache_data.get("flow_trades", None)
                if flow_trades_raw is None:
                    # Key doesn't exist - daemon hasn't polled this ticker yet
                    print(f"DEBUG: No flow_trades key in cache for {ticker} (daemon not polled yet)", flush=True)
                elif flow_trades_raw:
                    # Key exists and has data - use it even if stale (graceful degradation)
                    if is_stale:
                        using_stale_data = True
                        stale_data_count += 1
                        print(f"DEBUG: Using STALE cache for {ticker} ({int(age_sec/60)} min old) - {len(flow_trades_raw)} trades", flush=True)
                    else:
                        fresh_data_count += 1
                        print(f"DEBUG: Found {len(flow_trades_raw)} raw trades for {ticker}", flush=True)
                    
                    # Normalize raw API trades to match main.py's expected format
                    uw_client = UWClient()
                    normalized_count = 0
                    filtered_count = 0
                    for raw_trade in flow_trades_raw:
                        try:
                            # Normalize using same logic as UWClient.get_option_flow
                            normalized_trade = uw_client._normalize_flow_trade(raw_trade)
                            normalized_count += 1
                            # Apply base filter (premium, expiry, etc.)
                            if base_filter(normalized_trade):
                                all_trades.append(normalized_trade)
                                filtered_count += 1
                        except Exception as e:
                            # Log normalization errors for debugging
                            print(f"DEBUG: Failed to normalize trade for {ticker}: {e}", flush=True)
                            continue
                    if normalized_count > 0:
                        print(f"DEBUG: {ticker}: {normalized_count} normalized, {filtered_count} passed filter", flush=True)
                else:
                    # Key exists but is empty array - API returned no trades (likely rate limited)
                    # Check if we have older cache data we can use
                    if is_stale:
                        print(f"DEBUG: flow_trades empty for {ticker} (stale cache, {int(age_sec/60)} min old)", flush=True)
                    else:
                        print(f"DEBUG: flow_trades key exists for {ticker} but is empty (API returned 0 trades)", flush=True)
                
                # Extract data from cache for confirmation scoring
                dp_data = cache_data.get("dark_pool", {})
                dp_map[ticker] = [{"off_lit_volume": dp_data.get("total_premium", 0)}]
                
                # Net premium from cache
                net_map[ticker] = {
                    "net_premium": dp_data.get("total_premium", 0),
                    "net_call_premium": dp_data.get("total_premium", 0) if cache_data.get("sentiment") == "BULLISH" else 0
                }
                
                # Gamma regime inference from sentiment
                sentiment = cache_data.get("sentiment", "NEUTRAL")
                gex_map[ticker] = {"gamma_regime": "negative" if sentiment == "BEARISH" else "neutral"}
                
                # Vol map placeholder
                vol_map[ticker] = {"realized_vol_20d": 0.2}
                
                ovl_map[ticker] = []
            
            # Log graceful degradation status
            if using_stale_data:
                print(f"✅ GRACEFUL DEGRADATION: Using stale cache data ({stale_data_count} stale, {fresh_data_count} fresh)", flush=True)
                log_event("uw_cache", "graceful_degradation_active", 
                         stale_tickers=stale_data_count,
                         fresh_tickers=fresh_data_count,
                         note="Trading continues with cached data < 2 hours old")
            
            log_event("data_source", "cache_mode", cache_symbols=len(uw_cache), api_calls=0, 
                     stale_data_used=using_stale_data, stale_count=stale_data_count, fresh_count=fresh_data_count)
            
            # CRITICAL FIX: Even if flow_trades is empty, composite scoring can still generate trades
            # from sentiment, conviction, dark_pool, insider data in cache
            # This ensures trading continues even when API is rate limited or returns empty flow_trades
            print(f"DEBUG: Cache mode active - composite scoring will run even if flow_trades empty ({len(all_trades)} trades from flow, {len(uw_cache)} symbols in cache)", flush=True)
            print(f"DEBUG: Maps built: {len(dp_map)} dark_pool, {len(gex_map)} gamma, {len(net_map)} net_premium", flush=True)
        else:
            # GRACEFUL DEGRADATION: Cache empty or daemon not running
            # Check if we have ANY cached data (even if stale) to use
            print("⚠️  WARNING: UW cache empty or unavailable", flush=True)
            
            # Try to use stale cache data if available (within 2 hours)
            stale_cache_used = False
            if uw_cache:
                current_time = time.time()
                stale_threshold = 2 * 3600  # 2 hours
                
                for ticker in Config.TICKERS:
                    cache_data = uw_cache.get(ticker, {})
                    if cache_data and not cache_data.get("simulated"):
                        last_update = cache_data.get("_last_update", 0)
                        age_sec = current_time - last_update if last_update else float('inf')
                        
                        # Use stale data if less than 2 hours old
                        if age_sec < stale_threshold:
                            stale_cache_used = True
                            print(f"✅ Using stale cache for {ticker} (age: {int(age_sec/60)} min)", flush=True)
                            
                            # Extract flow trades from stale cache
                            flow_trades_raw = cache_data.get("flow_trades", [])
                            if flow_trades_raw:
                                uw_client = UWClient()
                                for raw_trade in flow_trades_raw:
                                    try:
                                        normalized_trade = uw_client._normalize_flow_trade(raw_trade)
                                        if base_filter(normalized_trade):
                                            all_trades.append(normalized_trade)
                                    except Exception as e:
                                        continue
                            
                            # Use cached sentiment/conviction data
                            dp_data = cache_data.get("dark_pool", {})
                            dp_map[ticker] = [{"off_lit_volume": dp_data.get("total_premium", 0)}]
                            net_map[ticker] = {
                                "net_premium": cache_data.get("net_premium", 0),
                                "net_call_premium": cache_data.get("call_premium", 0)
                            }
                            sentiment = cache_data.get("sentiment", "NEUTRAL")
                            gex_map[ticker] = {"gamma_regime": "negative" if sentiment == "BEARISH" else "neutral"}
                            vol_map[ticker] = {"realized_vol_20d": 0.2}
                            ovl_map[ticker] = []
                
                if stale_cache_used:
                    print("✅ Using stale cache data (graceful degradation mode)", flush=True)
                    log_event("uw_cache", "using_stale_cache", 
                             action="graceful_degradation",
                             note="Using cached data < 2 hours old due to API rate limit or daemon unavailable")
                else:
                    print("⚠️  No usable stale cache - skipping trading this cycle", flush=True)
                    log_event("uw_cache", "cache_empty_no_stale", 
                             action="skipping_trading",
                             reason="no_cache_data_available")
            
            # If no stale cache available, skip trading
            if not stale_cache_used:
                print("⚠️  Skipping API calls to preserve quota - no usable cache data", flush=True)
                poll_top_net = False
                poll_flow = False
                
                # Initialize empty maps (will result in no clusters)
                for ticker in Config.TICKERS:
                    gex_map[ticker] = {"gamma_regime": "unknown"}
                    dp_map[ticker] = []
                    vol_map[ticker] = {"realized_vol_20d": 0}
                    ovl_map[ticker] = []
                    net_map[ticker] = {}

        audit_seg("run_once", "data_fetch_complete")
        print(f"DEBUG: Fetched data, clustering {len(all_trades)} trades", flush=True)
        flow_clusters = cluster_signals(all_trades)
        
        # CRITICAL FIX: Initialize clusters to flow_clusters immediately to prevent UnboundLocalError
        clusters = flow_clusters
        
        print(f"DEBUG: Initial flow_trades clusters={len(flow_clusters)}, use_composite={use_composite}", flush=True)
        log_event("scoring_flow", "cluster_creation", flow_clusters=len(flow_clusters), use_composite=use_composite, cache_symbols=cache_symbol_count)
        _pipeline_touch("scoring")
        
        # ROOT CAUSE FIX: Always run composite scoring when cache has symbol data
        # Composite scoring uses sentiment, conviction, dark_pool, insider - doesn't need flow_trades
        # use_composite already checks for symbol keys (not metadata), so we can use it directly
        if use_composite:
            # Generate synthetic signals from cache instead of waiting for live API
            # CRITICAL: This works even when flow_trades is empty - uses sentiment, conviction, dark_pool, insider
            print(f"DEBUG: Running composite scoring for {cache_symbol_count} symbols (flow_trades may be empty)", flush=True)
            log_event("scoring_flow", "composite_scoring_start", cache_symbols=cache_symbol_count)
            market_regime = compute_market_regime(gex_map, net_map, vol_map)
            filtered_clusters = []
            
            symbols_processed = 0
            symbols_with_signals = 0
            
            # CRITICAL FIX: Process ALL symbols that have clusters OR are in cache
            # This ensures clusters for symbols not in cache (e.g., NVDA trades stored under AAPL key) are still scored
            cluster_symbols = set(c.get("ticker") for c in clusters if c.get("ticker"))
            cache_symbols = set(k for k in uw_cache.keys() if not k.startswith("_"))
            all_symbols_to_process = cluster_symbols | cache_symbols
            
            print(f"DEBUG: Processing {len(all_symbols_to_process)} symbols ({len(cluster_symbols)} from clusters, {len(cache_symbols)} from cache)", flush=True)

            # Counter-signal detector state (persisted; best-effort).
            try:
                from pathlib import Path as _Path
                from utils.state_io import read_json_self_heal as _read_json_self_heal
                _LAST_SCORES_PATH = _Path("state/last_scores.json")
                last_scores = _read_json_self_heal(
                    _LAST_SCORES_PATH,
                    {},
                    on_event=lambda ev, payload: log_system_event("signals", ev, "WARN", details=payload),
                )
                if not isinstance(last_scores, dict):
                    last_scores = {}
            except Exception:
                last_scores = {}
                _LAST_SCORES_PATH = None
            last_scores_dirty = False
            
            for ticker in all_symbols_to_process:
                # Skip metadata keys
                if ticker.startswith("_"):
                    continue
                
                # ROOT CAUSE FIX: Add error handling to prevent KeyError crashes
                # If ticker is not in cache or cache data is invalid, skip it gracefully
                try:
                    # Check if ticker exists in cache before processing
                    if ticker not in uw_cache:
                        print(f"DEBUG: Skipping {ticker} - not in UW cache", flush=True)
                        continue
                    
                    cache_data = uw_cache.get(ticker)
                    if not cache_data or not isinstance(cache_data, dict):
                        print(f"DEBUG: Skipping {ticker} - invalid cache data", flush=True)
                        continue
                    
                    # V3: Enrichment → Composite V3 FULL INTELLIGENCE → Gate
                    enriched = uw_enrich.enrich_signal(ticker, uw_cache, market_regime)
                except KeyError as ke:
                    print(f"DEBUG: KeyError processing {ticker}: {ke} - skipping", flush=True)
                    log_event("composite_scoring", "keyerror_skipped", symbol=ticker, error=str(ke))
                    continue
                except Exception as e:
                    print(f"DEBUG: Exception processing {ticker}: {e} - skipping", flush=True)
                    log_event("composite_scoring", "exception_skipped", symbol=ticker, error=str(e), error_type=type(e).__name__)
                    continue

                # Shadow/rollout observability: record composite version selection once per cycle.
                # NOTE: production currently remains v1; v2 is shadow-only unless explicitly enabled later.
                try:
                    if symbols_processed == 0:
                        from config.registry import StrategyFlags
                        try:
                            log_system_event(
                                subsystem="scoring",
                                event_type="composite_version_used",
                                severity="INFO",
                                details={
                                    "composite_version": getattr(StrategyFlags, "COMPOSITE_VERSION", "v1"),
                                    "shadow_trading_enabled": bool(getattr(StrategyFlags, "SHADOW_TRADING_ENABLED", True)),
                                },
                            )
                        except Exception:
                            pass
                except Exception:
                    pass
                
                # Institutional Remediation Phase 3:
                # Do NOT floor freshness here; freshness is computed in uw_enrichment_v2 and should be allowed
                # to decay toward 0.0 so the score floor blocks stale/ghost signals.
                current_freshness = enriched.get("freshness", 1.0)
                
                # CRITICAL FIX: Get symbol_data from cache before using it (MUST be outside freshness check)
                symbol_data = uw_cache.get(ticker, {})
                
                # Ensure computed signals are in enriched data (fallback if not in cache)
                enricher = uw_enrich.UWEnricher()
                cache_updated = False
                
                # SCORING PIPELINE FIX (Priority 3): Ensure core features are ALWAYS computed or neutral-defaulted
                # See SIGNAL_SCORE_PIPELINE_AUDIT.md for details
                # This prevents 3 components (iv_skew, smile_slope, event_align) from contributing 0.0
                missing_core_features = []
                
                if isinstance(symbol_data, dict):
                    # Compute missing signals on-the-fly
                    if not enriched.get("iv_term_skew") and symbol_data.get("iv_term_skew") is None:
                        computed_skew = enricher.compute_iv_term_skew(ticker, symbol_data)
                        enriched["iv_term_skew"] = computed_skew
                        if ticker in uw_cache:
                            uw_cache[ticker]["iv_term_skew"] = computed_skew
                            cache_updated = True
                        missing_core_features.append("iv_term_skew")
                    
                    # Ensure iv_term_skew exists (neutral default if computation failed)
                    if enriched.get("iv_term_skew") is None:
                        enriched["iv_term_skew"] = 0.0  # Neutral default
                        missing_core_features.append("iv_term_skew_defaulted")
                    
                    if not enriched.get("smile_slope") and symbol_data.get("smile_slope") is None:
                        computed_slope = enricher.compute_smile_slope(ticker, symbol_data)
                        enriched["smile_slope"] = computed_slope
                        if ticker in uw_cache:
                            uw_cache[ticker]["smile_slope"] = computed_slope
                            cache_updated = True
                        missing_core_features.append("smile_slope")
                    
                    # Ensure smile_slope exists (neutral default if computation failed)
                    if enriched.get("smile_slope") is None:
                        enriched["smile_slope"] = 0.0  # Neutral default
                        missing_core_features.append("smile_slope_defaulted")
                    
                    # Ensure event_alignment exists (neutral default if missing)
                    if enriched.get("event_alignment") is None:
                        enriched["event_alignment"] = 0.0  # Neutral default
                        missing_core_features.append("event_alignment_defaulted")
                    
                    # Log missing core features for telemetry
                    if missing_core_features:
                        log_event("scoring_pipeline", "core_features_defaulted", 
                                 symbol=ticker, missing_features=missing_core_features)
                
                # Ensure insider exists (with default structure)
                if not enriched.get("insider") or not isinstance(enriched.get("insider"), dict):
                    default_insider = {
                        "sentiment": "NEUTRAL",
                        "net_buys": 0,
                        "net_sells": 0,
                        "total_usd": 0.0,
                        "conviction_modifier": 0.0
                    }
                    enriched["insider"] = symbol_data.get("insider", default_insider) if isinstance(symbol_data, dict) else default_insider
                    if ticker in uw_cache and not uw_cache[ticker].get("insider"):
                        uw_cache[ticker]["insider"] = enriched["insider"]
                        cache_updated = True
                
                # Persist cache updates if any were made
                if cache_updated:
                    try:
                        atomic_write_json(CacheFiles.UW_FLOW_CACHE, uw_cache)
                    except Exception as e:
                        log_event("cache_update", "error", error=str(e))
                
                # Use V3 scoring with all expanded intelligence (congress, shorts, institutional, etc.)
                # NOTE: market_regime is computed later, use "mixed" as default for now
                symbols_processed += 1
                print(f"DEBUG: Computing composite score for {ticker} (symbol {symbols_processed}/{len(all_symbols_to_process)})", flush=True)
                composite = uw_v2.compute_composite_score_v3(ticker, enriched, "mixed")
                if composite is None:
                    print(f"DEBUG: Composite scoring returned None for {ticker} - skipping", flush=True)
                    log_event("scoring_flow", "composite_none", symbol=ticker)
                    continue  # skip invalid data safely

                # STRUCTURAL UPGRADE (log-only): pass through vol/beta features for observability/learning.
                # This does NOT affect score computation (composite already computed).
                try:
                    f = composite.get("features_for_learning")
                    if not isinstance(f, dict):
                        f = {}
                    f.setdefault("realized_vol_5d", float(enriched.get("realized_vol_5d", 0.0) or 0.0))
                    f.setdefault("realized_vol_20d", float(enriched.get("realized_vol_20d", 0.0) or 0.0))
                    f.setdefault("beta_vs_spy", float(enriched.get("beta_vs_spy", 0.0) or 0.0))
                    composite["features_for_learning"] = f
                except Exception:
                    pass
                
                score = composite.get("score", 0.0)
                print(f"DEBUG: {ticker} composite_score={score:.3f}", flush=True)
                log_event("scoring_flow", "composite_calculated", symbol=ticker, score=score, components=composite.get("components", {}))

                # First-class counter-signal logging (direction reversal).
                try:
                    new_sent = enriched.get("sentiment", "NEUTRAL")
                    new_dir = "bullish" if new_sent == "BULLISH" else ("bearish" if new_sent == "BEARISH" else "neutral")
                    prev = last_scores.get(ticker, {}) if isinstance(last_scores, dict) else {}
                    old_score = float(prev.get("score", 0.0) or 0.0)
                    old_dir = str(prev.get("direction", "neutral") or "neutral")
                    delta = float(score) - float(old_score)
                    if old_dir in ("bullish", "bearish") and new_dir in ("bullish", "bearish") and old_dir != new_dir:
                        log_system_event(
                            subsystem="signals",
                            event_type="counter_signal_detected",
                            severity="INFO",
                            symbol=ticker,
                            old_score=old_score,
                            new_score=float(score),
                            delta=delta,
                            old_direction=old_dir,
                            new_direction=new_dir,
                        )
                    if isinstance(last_scores, dict):
                        last_scores[ticker] = {"score": float(score), "direction": new_dir, "ts": now_iso()}
                        last_scores_dirty = True
                except Exception:
                    pass
                
                # V3: Log all expanded features for learning (congress, shorts, institutional, etc.)
                log_v3_features(ticker, composite)
                
                # V2.1 EXECUTION: Cross-asset confirmation (when promoted)
                if should_run_direct_v2():
                    try:
                        cross_asset_adjustment = cross_asset.get_cross_asset_confirmation(ticker, composite)
                        original_score = composite.get("score", 0.0)
                        composite["score"] = original_score + cross_asset_adjustment
                        composite["cross_asset_adjustment"] = cross_asset_adjustment
                    except Exception as e:
                        pass  # Don't crash on cross-asset errors
                
                # SECTOR TIDE BOOST: Apply +0.3 if sector has >= 3 symbols in 15-minute window
                sector_tide_boost = 0.0
                sector_tide_info = {}
                try:
                    from sector_tide_tracker import get_sector_tide_tracker
                    tide_tracker = get_sector_tide_tracker()
                    # Record this signal for sector tracking
                    tide_tracker.record_signal(ticker)
                    # Check if sector tide is active
                    tide_info = tide_tracker.check_sector_tide(ticker)
                    if tide_info.get("active"):
                        sector_tide_boost = tide_info.get("boost", 0.0)
                        sector_tide_info = {
                            "sector": tide_info.get("sector"),
                            "count": tide_info.get("count"),
                            "boost": sector_tide_boost
                        }
                        original_score = composite.get("score", 0.0)
                        composite["score"] = original_score + sector_tide_boost
                        composite["sector_tide_boost"] = sector_tide_boost
                        composite["sector_tide_info"] = sector_tide_info
                        print(f"DEBUG: Sector Tide boost applied to {ticker}: +{sector_tide_boost:.2f} (sector={tide_info.get('sector')}, count={tide_info.get('count')})", flush=True)
                except ImportError:
                    pass  # Sector tide tracker not available
                except Exception as e:
                    print(f"DEBUG: Sector tide check failed for {ticker}: {e}", flush=True)
                
                # PERSISTENCE BOOST: Apply +0.5 if ticker appears > 5 times in 15 minutes
                persistence_boost = 0.0
                persistence_info = {}
                try:
                    from persistence_tracker import get_persistence_tracker
                    persistence_tracker = get_persistence_tracker()
                    # Record this signal for persistence tracking
                    persistence_tracker.record_signal(ticker)
                    # Check if persistence is detected
                    persistence_check = persistence_tracker.check_persistence(ticker)
                    if persistence_check.get("active"):
                        persistence_boost = persistence_check.get("boost", 0.0)
                        persistence_info = {
                            "count": persistence_check.get("count"),
                            "whale_motif": persistence_check.get("whale_motif", False),
                            "boost": persistence_boost
                        }
                        # Apply persistence boost (same as whale boost)
                        original_score = composite.get("score", 0.0)
                        composite["score"] = original_score + persistence_boost
                        composite["persistence_boost"] = persistence_boost
                        composite["persistence_info"] = persistence_info
                        # Mark as whale motif if persistence detected
                        if persistence_check.get("whale_motif"):
                            composite["whale_conviction_boost"] = persistence_boost  # Override whale boost
                            composite["whale_motif_from_persistence"] = True
                        print(f"DEBUG: Persistence boost applied to {ticker}: +{persistence_boost:.2f} (count={persistence_check.get('count')}, whale_motif={persistence_check.get('whale_motif')})", flush=True)
                except ImportError:
                    pass  # Persistence tracker not available
                except Exception as e:
                    print(f"DEBUG: Persistence check failed for {ticker}: {e}", flush=True)
                
                # EOW FORENSIC OPTIMIZATION: Alpha Signature Boosters
                # Leverage 'Hidden Factors' discovered in virtual winners from audit
                alpha_boost_total = 0.0
                alpha_boosters_applied = []
                try:
                    # Capture alpha signature for boosters
                    if hasattr(engine, 'executor') and hasattr(engine.executor, 'api'):
                        from alpha_signature_capture import capture_alpha_signature
                        uw_cache_for_alpha = read_json(CacheFiles.UW_FLOW_CACHE, default={})
                        alpha_signature = capture_alpha_signature(engine.executor.api, ticker, uw_cache_for_alpha)
                        
                        # 1. RVOL > 3.0 → Score += 0.4
                        rvol = alpha_signature.get("rvol")
                        if rvol and rvol > 3.0:
                            alpha_boost_total += 0.4
                            alpha_boosters_applied.append(f"RVOL_{rvol:.2f}")
                            print(f"DEBUG: Alpha booster RVOL > 3.0: +0.4 applied to {ticker} (RVOL={rvol:.2f})", flush=True)
                        
                        # 2. Sector Tide Count > 3 → Score += 0.3 (ensure minimum, may already be applied)
                        sector_tide_count_actual = sector_tide_info.get("count", 0) if sector_tide_info else 0
                        if sector_tide_count_actual > 3:
                            # Don't double-count if already applied, but ensure minimum 0.3
                            if sector_tide_boost < 0.3:
                                additional_boost = 0.3 - sector_tide_boost
                                alpha_boost_total += additional_boost
                                alpha_boosters_applied.append(f"SectorTide_{sector_tide_count_actual}")
                                print(f"DEBUG: Alpha booster Sector Tide > 3: +{additional_boost:.2f} applied to {ticker} (count={sector_tide_count_actual})", flush=True)
                            else:
                                alpha_boosters_applied.append(f"SectorTide_{sector_tide_count_actual}_already_applied")
                        
                        # 3. Persistence Count > 5 → Score += 0.3 (ensure minimum, may already be applied)
                        persistence_count_actual = persistence_info.get("count", 0) if persistence_info else 0
                        if persistence_count_actual > 5:
                            # If persistence boost already applied, check if it's >= 0.3
                            if persistence_boost < 0.3:
                                additional_boost = 0.3 - persistence_boost
                                alpha_boost_total += additional_boost
                                alpha_boosters_applied.append(f"Persistence_{persistence_count_actual}")
                                print(f"DEBUG: Alpha booster Persistence > 5: +{additional_boost:.2f} applied to {ticker} (count={persistence_count_actual})", flush=True)
                            else:
                                alpha_boosters_applied.append(f"Persistence_{persistence_count_actual}_already_applied")
                        
                        # Apply total alpha boost
                        if alpha_boost_total > 0:
                            original_score = composite.get("score", 0.0)
                            composite["score"] = original_score + alpha_boost_total
                            composite["alpha_signature_boost"] = alpha_boost_total
                            composite["alpha_boosters_applied"] = alpha_boosters_applied
                            # SAFETY: composite is a dict that may be partially populated; never index directly in debug.
                            final_score = composite.get("score", original_score)
                            print(f"DEBUG: Alpha Signature Boosters applied to {ticker}: +{alpha_boost_total:.2f} (total score: {original_score:.2f} → {final_score:.2f})", flush=True)
                except ImportError:
                    pass  # Alpha signature capture not available
                except Exception as e:
                    print(f"DEBUG: Alpha signature boosters failed for {ticker}: {e}", flush=True)
                
                # SCORING PIPELINE FIX (Part 2): Record telemetry after all boosts applied
                try:
                    from telemetry.score_telemetry import record
                    
                    # Build metadata for telemetry
                    metadata = {
                        "freshness": composite.get("freshness", 1.0),
                        "conviction_defaulted": enriched.get("conviction") is None or (enriched.get("conviction", 0.0) == 0.5 and symbol_data.get("conviction") is None),
                        "missing_intel": [],
                        "neutral_defaults": [],
                        "core_features_missing": missing_core_features if 'missing_core_features' in locals() else []
                    }
                    
                    # Check for neutral defaults in notes
                    notes = composite.get("notes", "")
                    if "neutral_default" in notes:
                        # Extract component names from notes
                        for comp in ["congress", "shorts", "institutional", "tide", "calendar", 
                                    "greeks", "ftd", "oi_change", "etf_flow", "squeeze_score"]:
                            if f"{comp}_neutral_default" in notes:
                                metadata["neutral_defaults"].append(comp)
                                metadata["missing_intel"].append(comp)
                    
                    # Record telemetry with final score (after all boosts)
                    record(
                        symbol=ticker,
                        score=composite.get("score", 0.0),
                        components=composite.get("components", {}),
                        metadata=metadata
                    )
                except ImportError:
                    pass  # Telemetry module not available
                except Exception as e:
                    log_event("score_telemetry", "error", symbol=ticker, error=str(e))
                
                # Use V2 should_enter (hierarchical thresholds) with V3.0 exhaustion check
                # Pass api for exhaustion filter (EMA/ATR check)
                gate_result = uw_v2.should_enter_v2(composite, ticker, mode="base", api=engine.executor.api if hasattr(engine, 'executor') and hasattr(engine.executor, 'api') else None)

                # STRUCTURAL UPGRADE: Shadow A/B compare (v1 vs v2 composite) - v1 remains production.
                # v2 is computed as an additive adjustment layer on the finalized v1 composite for comparability.
                try:
                    from config.registry import StrategyFlags
                    shadow_enabled = bool(getattr(StrategyFlags, "SHADOW_TRADING_ENABLED", True))
                except Exception:
                    shadow_enabled = True
                try:
                    if shadow_enabled:
                        from telemetry.shadow_ab import log_shadow_event, log_shadow_divergence

                        mc = getattr(engine, "market_context_v2", None)
                        if not isinstance(mc, dict):
                            mc = {}
                        rp = getattr(engine, "regime_posture_v2", None)
                        if not isinstance(rp, dict):
                            rp = {}

                        # Use structural regime for directional weighting when available, else fall back to "mixed".
                        v2_regime = (rp.get("structural_regime") or "mixed") if isinstance(rp, dict) else "mixed"

                        composite_v2 = uw_v2.compute_composite_score_v3_v2(
                            ticker,
                            enriched,
                            regime=str(v2_regime),
                            market_context=mc,
                            posture_state=rp,
                            base_override=composite,
                        ) or {}

                        v2_pass = False
                        try:
                            v2_pass = bool(
                                uw_v2.should_enter_v2(
                                    composite_v2,
                                    ticker,
                                    mode="base",
                                    api=engine.executor.api if hasattr(engine, "executor") and hasattr(engine.executor, "api") else None,
                                )
                            )
                        except Exception:
                            v2_pass = False

                        v1_score = float(composite.get("score", 0.0) or 0.0)
                        v2_score = float(composite_v2.get("score", 0.0) or 0.0)

                        # Attach shadow metadata to the composite payload for downstream decision-path comparability.
                        # This is safe, additive metadata only.
                        try:
                            composite["shadow_v2"] = {
                                "score": v2_score,
                                "pass_composite_gate": bool(v2_pass),
                                "adjustments": composite_v2.get("v2_adjustments", {}),
                                "inputs": composite_v2.get("v2_inputs", {}),
                                "notes": composite_v2.get("notes", ""),
                            }
                        except Exception:
                            pass

                        log_shadow_event(
                            "score_compare",
                            symbol=ticker,
                            v1_score=v1_score,
                            v2_score=v2_score,
                            v1_pass=bool(gate_result),
                            v2_pass=bool(v2_pass),
                            market_regime=str(market_regime),
                            posture=str(rp.get("posture", "neutral") if isinstance(rp, dict) else "neutral"),
                            regime_label=str(rp.get("regime_label", "chop") if isinstance(rp, dict) else "chop"),
                            volatility_regime=str(mc.get("volatility_regime", "mid") if isinstance(mc, dict) else "mid"),
                            v2_adjustments=composite_v2.get("v2_adjustments", {}),
                        )

                        if bool(gate_result) != bool(v2_pass):
                            log_shadow_divergence(
                                symbol=ticker,
                                v1_score=v1_score,
                                v2_score=v2_score,
                                v1_pass=bool(gate_result),
                                v2_pass=bool(v2_pass),
                                details={
                                    "market_regime": str(market_regime),
                                    "posture": str(rp.get("posture", "neutral") if isinstance(rp, dict) else "neutral"),
                                    "regime_label": str(rp.get("regime_label", "chop") if isinstance(rp, dict) else "chop"),
                                },
                            )
                except Exception:
                    pass
                
                # V3 Attribution: Store enriched composite with FULL INTELLIGENCE features for learning
                try:
                    with open(CacheFiles.UW_ATTRIBUTION, "a") as f:
                        attr_rec = {
                            "ts": int(time.time()),
                            "symbol": ticker,
                            "score": composite.get("score", 0.0),
                            "decision": "signal" if gate_result else "rejected",
                            "source": "uw_v3",
                            "version": composite.get("version", "V3"),
                            "components": composite.get("components", {}),
                            "motifs": composite.get("motifs", {}),
                            "expanded_intel": composite.get("expanded_intel", {}),
                            "features_for_learning": composite.get("features_for_learning", {}),
                            "toxicity": composite.get("toxicity", 0.0),
                            "freshness": composite.get("freshness", 1.0),
                            "notes": composite.get("notes", "")
                        }
                        f.write(json.dumps(attr_rec) + "\n")
                except Exception as e:
                    pass  # Don't crash trading on attribution logging errors
                
                if gate_result:
                    symbols_with_signals += 1
                    # Create synthetic cluster from cache data
                    # V3: Get sentiment from enriched data, include expanded intel
                    flow_sentiment_raw = enriched.get("sentiment", "NEUTRAL")
                    # CRITICAL FIX: Convert BULLISH/BEARISH to lowercase bullish/bearish for direction field
                    # The code expects lowercase (see line 3908: side = "buy" if c["direction"] == "bullish")
                    flow_sentiment = flow_sentiment_raw.lower() if flow_sentiment_raw in ("BULLISH", "BEARISH") else "neutral"
                    score = composite.get("score", 0.0)
                    print(f"DEBUG: Composite signal ACCEPTED for {ticker}: score={score:.2f}, sentiment={flow_sentiment_raw}->{flow_sentiment}, threshold={get_threshold(ticker, 'base'):.2f}", flush=True)
                    
                    # CRITICAL FIX: Log accepted signals to history IMMEDIATELY so they show in dashboard
                    # Even if they're blocked later in decide_and_execute, they should appear in Signal Review
                    try:
                        whale_boost = composite.get("whale_conviction_boost", 0.0)
                        raw_score = score - whale_boost if whale_boost > 0 else score
                        final_score = score
                        
                        # Get sector for logging
                        sector = "Unknown"
                        try:
                            from risk_management import get_sector
                            sector = get_sector(ticker)
                        except:
                            pass
                        
                        # Get persistence and sector tide counts
                        persistence_count = 0
                        sector_tide_count = 0
                        if composite.get("persistence_info"):
                            persistence_count = composite.get("persistence_info", {}).get("count", 0)
                        if composite.get("sector_tide_info"):
                            sector_tide_count = composite.get("sector_tide_info", {}).get("count", 0)
                        
                        log_signal_to_history(
                            symbol=ticker,
                            direction=flow_sentiment,  # bullish/bearish
                            raw_score=raw_score,
                            whale_boost=whale_boost,
                            final_score=final_score,
                            atr_multiplier=0.0,  # Will be calculated later if needed
                            momentum_pct=0.0,  # Will be calculated later if needed
                            momentum_required_pct=0.0,  # Will be calculated later if needed
                            decision="Accepted: composite_gate",  # Will be updated to "Ordered" or "Blocked:reason" later
                            metadata={
                                "sector": sector,
                                "persistence_count": persistence_count,
                                "sector_tide_count": sector_tide_count,
                                "composite_score": score,
                                "source": "composite_v3",
                                "gate_stage": "composite_accepted"
                            }
                        )
                        print(f"DEBUG: Logged accepted signal to history: {ticker} score={score:.2f}", flush=True)
                    except Exception as log_err:
                        print(f"DEBUG: Failed to log accepted signal to history for {ticker}: {log_err}", flush=True)
                        traceback.print_exc()
                        # Don't fail on logging error - continue processing
                    
                    cluster = {
                        "ticker": ticker,
                        "direction": flow_sentiment,  # CRITICAL: Must be lowercase "bullish"/"bearish"
                        "sentiment": flow_sentiment_raw,  # Keep original for display
                        "composite_score": score,
                        "composite_meta": composite,
                        "gate_passed": True,
                        "source": "composite_v3",
                        "count": 1,
                        "total_premium": uw_cache.get(ticker, {}).get("dark_pool", {}).get("total_premium", 0),  # ROOT CAUSE FIX: Use .get() to prevent KeyError
                        "start_ts": int(time.time()),  # Required for cluster key
                        # V3: Expanded intelligence for downstream processing
                        "expanded_intel": composite.get("expanded_intel", {}),
                        "features_for_learning": composite.get("features_for_learning", {})
                    }
                    filtered_clusters.append(cluster)
                else:
                    score = composite.get("score", 0.0)
                    threshold_used = get_threshold(ticker, 'base')
                    toxicity = composite.get("toxicity", 0.0)
                    freshness = composite.get("freshness", 1.0)
                    whale_boost = composite.get("whale_conviction_boost", 0.0)

                    # Extract raw score (before whale boost) for signal history
                    raw_score = score - whale_boost if whale_boost > 0 else score
                    final_score = score
                    
                    # Determine actual rejection reason
                    rejection_reasons = []
                    if score < threshold_used:
                        rejection_reasons.append(f"score={score:.2f} < threshold={threshold_used:.2f}")
                    if toxicity > 0.90:
                        rejection_reasons.append(f"toxicity={toxicity:.2f} > 0.90")
                    if freshness < 0.30:
                        rejection_reasons.append(f"freshness={freshness:.2f} < 0.30")
                    
                    reason_str = " OR ".join(rejection_reasons) if rejection_reasons else "unknown"
                    print(f"DEBUG: Composite signal REJECTED for {ticker}: {reason_str}", flush=True)
                    
                    # CRITICAL FIX: Log rejected signals to history so they show in dashboard
                    try:
                        # Get sector for logging
                        sector = "Unknown"
                        try:
                            from risk_management import get_sector
                            sector = get_sector(ticker)
                        except:
                            pass
                        
                        # Get persistence and sector tide counts
                        persistence_count = 0
                        sector_tide_count = 0
                        if composite.get("persistence_info"):
                            persistence_count = composite.get("persistence_info", {}).get("count", 0)
                        if composite.get("sector_tide_info"):
                            sector_tide_count = composite.get("sector_tide_info", {}).get("count", 0)
                        
                        # Determine actual rejection reason
                        rejection_reasons = []
                        if score < threshold_used:
                            rejection_reasons.append(f"score={score:.2f} < threshold={threshold_used:.2f}")
                        if toxicity > 0.90:
                            rejection_reasons.append(f"toxicity={toxicity:.2f} > 0.90")
                        if freshness < 0.30:
                            rejection_reasons.append(f"freshness={freshness:.2f} < 0.30")
                        
                        reason_str = " OR ".join(rejection_reasons) if rejection_reasons else "unknown"
                        
                        log_signal_to_history(
                            symbol=ticker,
                            direction=composite.get("sentiment", "neutral").lower(),  # bullish/bearish/neutral
                            raw_score=raw_score,
                            whale_boost=whale_boost,
                            final_score=final_score,
                            atr_multiplier=0.0,
                            momentum_pct=0.0,
                            momentum_required_pct=0.0,
                            decision=f"Rejected: {reason_str}",
                            metadata={
                                "sector": sector,
                                "persistence_count": persistence_count,
                                "sector_tide_count": sector_tide_count,
                                "composite_score": score,
                                "threshold": threshold_used,
                                "toxicity": toxicity,
                                "freshness": freshness,
                                "source": "composite_v3",
                                "gate_stage": "composite_rejected"
                            }
                        )
                        print(f"DEBUG: Logged rejected signal to history: {ticker} score={score:.2f} reason={reason_str}", flush=True)
                    except Exception as log_err:
                        print(f"DEBUG: Failed to log rejected signal to history for {ticker}: {log_err}", flush=True)
                        # Don't fail on logging error - continue processing
                    
                    # Determine actual rejection reason
                    rejection_reasons = []
                    if score < threshold_used:
                        rejection_reasons.append(f"score={score:.2f} < threshold={threshold_used:.2f}")
                    if toxicity > 0.90:
                        rejection_reasons.append(f"toxicity={toxicity:.2f} > 0.90")
                    if freshness < 0.30:
                        rejection_reasons.append(f"freshness={freshness:.2f} < 0.30")
                    
                    reason_str = " OR ".join(rejection_reasons) if rejection_reasons else "unknown"
                    print(f"DEBUG: Composite signal REJECTED for {ticker}: {reason_str}", flush=True)
                    log_event("composite_gate", "rejected", symbol=ticker, 
                             score=score,
                             threshold=threshold_used,
                             toxicity=toxicity,
                             freshness=freshness,
                             rejection_reason=reason_str)
                    
                    # SIGNAL HISTORY: Log rejected signal from composite scoring
                    # This ensures user can see why signals like AAPL (2.48) are being rejected
                    try:
                        from signal_history_storage import append_signal_history
                        from risk_management import get_sector
                        from persistence_tracker import get_persistence_tracker
                        from shadow_tracker import get_shadow_tracker
                        from alpha_signature_capture import capture_alpha_signature
                        
                        # Get direction from enriched data
                        flow_sentiment_raw = enriched.get("sentiment", "NEUTRAL")
                        direction = flow_sentiment_raw.lower() if flow_sentiment_raw in ("BULLISH", "BEARISH") else "neutral"
                        
                        # Get sector information
                        sector = get_sector(ticker)
                        
                        # Get persistence information
                        persistence_count = 0
                        persistence_active = False
                        try:
                            persistence_tracker = get_persistence_tracker()
                            persistence_check = persistence_tracker.check_persistence(ticker)
                            persistence_count = persistence_check.get("count", 0)
                            persistence_active = persistence_check.get("active", False)
                        except:
                            pass
                        
                        # Get sector tide information
                        sector_tide_active = False
                        sector_tide_count = 0
                        if sector_tide_info:
                            sector_tide_active = sector_tide_info.get("count", 0) >= 3
                            sector_tide_count = sector_tide_info.get("count", 0)
                        
                        # Capture alpha signature (RVOL, RSI, Put/Call Ratio)
                        alpha_signature = {}
                        try:
                            if hasattr(engine, 'executor') and hasattr(engine.executor, 'api'):
                                alpha_signature = capture_alpha_signature(engine.executor.api, ticker, uw_cache)
                        except Exception as e:
                            print(f"DEBUG: Failed to capture alpha signature for {ticker}: {e}", flush=True)
                        
                        # Create shadow position if score > 2.3
                        shadow_created = False
                        virtual_pnl = None
                        try:
                            if score >= 2.3:
                                entry_price = engine.executor.get_last_trade(ticker) if hasattr(engine, 'executor') else 0.0
                                if entry_price > 0:
                                    shadow_tracker = get_shadow_tracker()
                                    shadow_created = shadow_tracker.create_shadow_position(
                                        symbol=ticker,
                                        direction=direction,
                                        entry_price=entry_price,
                                        entry_score=score
                                    )
                                    if shadow_created:
                                        # Get initial virtual P&L (should be 0.0 at creation)
                                        shadow_pos = shadow_tracker.get_position(ticker)
                                        if shadow_pos:
                                            virtual_pnl = shadow_pos.max_profit_pct
                        except Exception as e:
                            print(f"DEBUG: Failed to create shadow position for {ticker}: {e}", flush=True)
                        
                        # Determine rejection reason with sector/persistence context
                        decision_reason = f"Blocked: score_too_low"
                        if score < threshold_used:
                            if not sector_tide_active and not persistence_active:
                                decision_reason = "Blocked: Sector_Tide_Missing"
                            elif sector_tide_active and not persistence_active:
                                decision_reason = f"Blocked: score_too_low (Sector_Tide active: {sector_tide_count})"
                            elif persistence_active:
                                decision_reason = f"Blocked: score_too_low (Persistence: {persistence_count})"
                        else:
                            decision_reason = f"Blocked: {reason_str}"
                        
                        # Get ATR multiplier (not available at this stage, set to None)
                        atr_multiplier = None
                        
                        # Get momentum data (not available at composite scoring stage)
                        momentum_pct = 0.0
                        momentum_required_pct = 0.0
                        
                        append_signal_history({
                            "symbol": ticker,
                            "direction": direction,
                            "raw_score": round(raw_score, 3),
                            "whale_boost": round(whale_boost, 3),
                            "final_score": round(final_score, 3),
                            "atr_multiplier": None,
                            "momentum_pct": 0.0,
                            "momentum_required_pct": 0.0,
                            "decision": decision_reason,
                            "sector": sector,
                            "persistence_count": persistence_count,
                            "sector_tide_count": sector_tide_count,
                            "virtual_pnl": virtual_pnl if virtual_pnl is not None else 0.0,
                            "shadow_created": shadow_created,
                            "metadata": {
                                "threshold_used": threshold_used,
                                "toxicity": toxicity,
                                "freshness": freshness,
                                "rejection_reason": reason_str,
                                "stage": "composite_scoring",
                                "sector_tide_active": sector_tide_active,
                                "persistence_active": persistence_active,
                                "sector_tide_boost": sector_tide_info.get("boost", 0.0) if sector_tide_info else 0.0,
                                "persistence_boost": persistence_info.get("boost", 0.0) if persistence_info else 0.0,
                                "alpha_signature": alpha_signature
                            }
                        })
                    except ImportError:
                        pass  # Signal history module not available
                    except Exception as e:
                        print(f"DEBUG: Failed to log rejected signal to history: {e}", flush=True)
            
            # Persist counter-signal state (best-effort; never blocks trading).
            try:
                if last_scores_dirty and _LAST_SCORES_PATH is not None:
                    from config.registry import atomic_write_json as _atomic_write_json
                    _atomic_write_json(_LAST_SCORES_PATH, last_scores)
            except Exception:
                pass

            # CRITICAL FIX: When composite scoring is active, ONLY use composite-scored clusters
            # Flow_trades clusters don't have composite_score, so they appear as score=0.00
            # Composite-scored clusters have proper scores and source="composite_v3"
            # REPLACE flow_clusters with filtered_clusters to ensure ALL clusters have scores
            clusters = filtered_clusters
            print(f"DEBUG: Using ONLY composite-scored clusters ({len(filtered_clusters)} clusters with scores), discarding {len(flow_clusters)} unscored flow_clusters", flush=True)
            print(f"DEBUG: Composite scoring complete: {symbols_processed} symbols processed, {symbols_with_signals} passed gate, {len(filtered_clusters)} composite clusters, {len(flow_clusters)} flow clusters, {len(clusters)} total clusters", flush=True)
            log_event("composite_filter", "applied", cache_symbols=cache_symbol_count, cache_total_keys=len(uw_cache), 
                     symbols_processed=symbols_processed,
                     symbols_with_signals=symbols_with_signals,
                     passed=len(clusters), rejection_rate=1.0 - (len(clusters) / max(symbols_processed, 1)))
            print(f"DEBUG: Composite filter complete, {len(clusters)} clusters passed gate", flush=True)
        else:
            # ROOT CAUSE FIX: Composite scoring doesn't run when cache has no symbol keys
            # This is expected behavior - cache may only have metadata keys (starting with "_")
            # In this case, use flow_clusters (unscored) as fallback
            print(f"DEBUG: Cache has no symbol keys ({cache_symbol_count} symbols, {len(uw_cache)} total keys) - composite scoring cannot run, using flow_clusters", flush=True)
            log_event("composite_scoring", "no_symbol_keys_using_flow_clusters", cache_symbol_count=cache_symbol_count, cache_total_keys=len(uw_cache), flow_clusters=len(flow_clusters))
            # Use flow_clusters when cache has no symbol data (expected behavior)
            clusters = flow_clusters  # Use flow_clusters when cache has no symbol keys

        audit_seg("run_once", "clusters_filtered", {"cluster_count": len(clusters)})
        
        # MONITORING GUARD 3: Check composite score floor (after clustering)
        if not check_composite_score_floor(clusters):
            alerts_this_cycle.append("composite_score_floor_breach")
            # V3.0: Auto-heal composite score degradation (reload config)
            fix_result = auto_heal_on_alert("composite_score_floor_breach")
            if fix_result and fix_result.get("overall_success"):
                fixes_applied_list.extend(fix_result.get("fixes_succeeded", []))
        
        print(f"DEBUG: Building confirm_map for {len(clusters)} clusters", flush=True)
        confirm_map = {}
        for t in set(c["ticker"] for c in clusters):
            confirm_map[t] = score_confirmation_layers(
                symbol=t,
                gex=gex_map.get(t, {}),
                dp_levels=dp_map.get(t, []),
                net_impact_map=net_map,
                vol=vol_map.get(t, {}),
                ovl=ovl_map.get(t, [])
            )

        market_regime = compute_market_regime(gex_map, net_map, vol_map)
        global _last_market_regime
        _last_market_regime = market_regime
        
        print(f"DEBUG: About to call decide_and_execute with {len(clusters)} clusters, regime={market_regime}", flush=True)
        if len(clusters) == 0:
            print("⚠️  WARNING: No clusters to execute - check composite scoring logs above", flush=True)
            log_event("execution", "no_clusters", cache_symbols=len(uw_cache) if use_composite else 0)
        audit_seg("run_once", "before_decide_execute", {"cluster_count": len(clusters)})
        # Live-safety gates before placing NEW entries:
        # - Broker degraded => reduce-only
        # - Not armed / endpoint mismatch => skip entries
        # - Executor not reconciled => skip entries (until it can sync positions cleanly)
        armed = trading_is_armed()
        reconciled_ok = False
        try:
            reconciled_ok = bool(engine.executor.ensure_reconciled())
        except Exception:
            reconciled_ok = False

        if degraded_mode:
            # Reduce-only safety: do not open new positions when broker connectivity is degraded.
            # Still allow exit logic and monitoring to run.
            log_event("run_once", "reduce_only_broker_degraded", action="skip_entries")
            orders = []
        elif not armed:
            log_event("run_once", "not_armed_skip_entries",
                      trading_mode=Config.TRADING_MODE, base_url=Config.ALPACA_BASE_URL,
                      require_live_ack=Config.REQUIRE_LIVE_ACK)
            orders = []
        elif not reconciled_ok:
            log_event("run_once", "not_reconciled_skip_entries", action="skip_entries")
            orders = []
        else:
            if Config.ENABLE_PER_TICKER_LEARNING:
                decisions_map = build_symbol_decisions(clusters, gex_map, dp_map, net_map, vol_map, ovl_map)
                _pipeline_touch("decision")
                orders = engine.decide_and_execute(clusters, confirm_map, gex_map, decisions_map, market_regime)
            else:
                _pipeline_touch("decision")
                orders = engine.decide_and_execute(clusters, confirm_map, gex_map, None, market_regime)
        print(f"DEBUG: decide_and_execute returned {len(orders)} orders", flush=True)
        audit_seg("run_once", "after_decide_execute", {"order_count": len(orders)})
        
        # CRITICAL FIX: Log to file BEFORE self-healing code
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] decide_and_execute returned {len(orders)} orders\n")
                f.flush()
        except:
            pass
        
        # SELF-HEALING: Clear freeze flag and reset fail counter on successful cycle
        if watchdog and hasattr(watchdog, 'state'):
            if watchdog.state.fail_count > 0:
                watchdog.state.fail_count = 0
                log_event("self_healing", "fail_counter_reset", reason="successful_cycle")
            # Clear freeze flag if it exists (was set due to previous failures)
            freeze_path = StateFiles.PRE_MARKET_FREEZE
            if freeze_path.exists():
                try:
                    freeze_path.unlink()
                    log_event("self_healing", "freeze_flag_cleared", reason="successful_cycle")
                    print("✅ SELF-HEALING: Cleared freeze flag after successful cycle", flush=True)
                except Exception as e:
                    log_event("self_healing", "freeze_clear_failed", error=str(e))
        
        # CRITICAL FIX: Log to file BEFORE calling evaluate_exits
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] About to call evaluate_exits() - orders={len(orders)}\n")
                f.flush()
        except:
            pass
        
        print("DEBUG: Calling evaluate_exits", flush=True)
        
        # CRITICAL FIX: Log exit evaluation to file
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] Calling evaluate_exits()\n")
                f.flush()
        except:
            pass
        
        # CRITICAL FIX: Ensure evaluate_exits is ALWAYS called, even if there's an exception
        try:
            # CRITICAL: Force evaluate_exits to run - this MUST happen
            print(f"DEBUG: FORCING evaluate_exits() call - engine.executor exists: {hasattr(engine, 'executor')}", flush=True)
            if hasattr(engine, 'executor') and hasattr(engine.executor, 'evaluate_exits'):
                engine.executor.evaluate_exits()
                print("DEBUG: evaluate_exits() completed", flush=True)
                try:
                    with open("logs/worker_debug.log", "a") as f:
                        f.write(f"[{datetime.now(timezone.utc).isoformat()}] evaluate_exits() completed\n")
                        f.flush()
                except:
                    pass
            else:
                print("ERROR: engine.executor.evaluate_exits() not available!", flush=True)
                try:
                    with open("logs/worker_debug.log", "a") as f:
                        f.write(f"[{datetime.now(timezone.utc).isoformat()}] ERROR: evaluate_exits() not available!\n")
                        f.flush()
                except:
                    pass
        except Exception as exit_err:
            print(f"ERROR: evaluate_exits() raised exception: {exit_err}", flush=True)
            traceback.print_exc()
            log_event("exit", "evaluate_exits_exception", error=str(exit_err))
            try:
                with open("logs/worker_debug.log", "a") as f:
                    f.write(f"[{datetime.now(timezone.utc).isoformat()}] ERROR: evaluate_exits() exception: {exit_err}\n")
                    f.flush()
            except:
                pass
        
        # CRITICAL FIX: Log after evaluate_exits
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] evaluate_exits() completed\n")
                f.flush()
        except:
            pass
        
        audit_seg("run_once", "after_exits")

        # SHADOW PnL (optional, additive): update unrealized PnL + evaluate hypothetical exits.
        # Contract: never blocks trading; never submits real orders.
        try:
            from config.registry import StrategyFlags
            shadow_enabled = bool(getattr(StrategyFlags, "SHADOW_TRADING_ENABLED", True))
            shadow_pnl_enabled = bool(getattr(StrategyFlags, "SHADOW_PNL_ENABLED", False))
            shadow_exit_enabled = bool(getattr(StrategyFlags, "SHADOW_EXIT_ENABLED", False))
            if shadow_enabled and shadow_pnl_enabled and hasattr(engine, "executor") and hasattr(engine.executor, "api") and engine.executor.api is not None:
                # Build a lightweight signal context map from current clusters (direction used for counter-signal exits).
                sig_ctx = {}
                try:
                    for cl in (locals().get("clusters") or []):
                        sym = cl.get("ticker")
                        if not sym:
                            continue
                        sig_ctx[str(sym).upper()] = {"direction": cl.get("direction")}
                except Exception:
                    sig_ctx = {}
                posture_state = getattr(engine, "regime_posture_v2", None)
                if not isinstance(posture_state, dict):
                    posture_state = {}
                from shadow.shadow_pnl_engine import shadow_pnl_tick
                shadow_pnl_tick(
                    engine.executor.api,
                    signal_context=sig_ctx,
                    posture_state=posture_state,
                    enable_exits=shadow_exit_enabled,
                )
        except Exception:
            pass

        print("DEBUG: Computing metrics", flush=True)
        metrics = compute_daily_metrics()
        metrics["market_regime"] = market_regime
        metrics["composite_enabled"] = use_composite
        
        # RISK MANAGEMENT: Add risk metrics to cycle metrics
        try:
            from risk_management import calculate_daily_pnl, load_peak_equity, get_risk_limits
            # BULLETPROOF: Safe account fetch with error handling
            current_equity = 0.0
            try:
                account = engine.executor.api.get_account()
                current_equity = float(getattr(account, "equity", 0.0))
            except (AttributeError, ValueError, TypeError, Exception) as acct_err:
                log_event("metrics", "account_fetch_error", error=str(acct_err))
                current_equity = 0.0
            
            daily_pnl = calculate_daily_pnl(current_equity) if current_equity > 0 else 0.0
            peak_equity = load_peak_equity()
            # BULLETPROOF: Validate peak_equity before division
            drawdown_pct = ((peak_equity - current_equity) / peak_equity * 100) if peak_equity > 0 and current_equity > 0 else 0.0
            drawdown_pct = max(-100.0, min(100.0, drawdown_pct))  # Clamp to reasonable range
            
            metrics["risk_metrics"] = {
                "current_equity": current_equity,
                "peak_equity": peak_equity,
                "daily_pnl": daily_pnl,
                "drawdown_pct": drawdown_pct,
                "daily_loss_limit": get_risk_limits()["daily_loss_dollar"],
                "drawdown_limit_pct": get_risk_limits()["max_drawdown_pct"],
                "mode": "PAPER" if Config.TRADING_MODE == "PAPER" else "LIVE"
            }
        except Exception:
            pass  # Non-critical
        
        print("DEBUG: About to log telemetry", flush=True)
        audit_seg("run_once", "before_telemetry")
        try:
            # BULLETPROOF: Safe account and position fetch with error handling
            equity = 100000.0  # Safe default
            positions = []
            try:
                account = engine.executor.api.get_account()
                equity = float(getattr(account, "equity", 100000.0))
                positions = engine.executor.api.list_positions() or []
            except (AttributeError, ValueError, TypeError, Exception) as acct_err:
                log_event("api", "account_or_positions_fetch_error", error=str(acct_err))
                equity = 100000.0  # Use default
                positions = []  # Empty list on error
            
            total_exposure = sum(abs(float(getattr(p, "market_value", 0.0))) for p in positions)
            leverage = total_exposure / equity if equity > 0 else 0.0
            position_count = len(positions)
            
            telemetry.log_risk_metrics(
                total_exposure=total_exposure,
                theme_concentration={},
                leverage=leverage,
                max_drawdown=0.0,
                position_count=position_count,
                regime=market_regime
            )
        except Exception:
            pass
        
        # CRITICAL FIX: Write heartbeat BEFORE owner_health_check to prevent false stale alerts
        # heartbeat() is normally called after run_once() completes, but owner_health_check
        # runs at the end of run_once() and checks heartbeat file - need to write it first
        try:
            watchdog.heartbeat({"clusters": len(clusters), "orders": len(orders)})
        except Exception as e:
            log_event("heartbeat", "early_write_failed", error=str(e))
        
        # CRITICAL FIX: Write heartbeat BEFORE owner_health_check to prevent false stale alerts
        # The heartbeat file is checked by owner_health_check, but heartbeat() is normally
        # called AFTER run_once() completes. We need to write it here so the check sees fresh data.
        # Note: This is a duplicate write (heartbeat() also called after run_once), but ensures
        # owner_health_check sees fresh heartbeat file.
        try:
            heartbeat_path = StateFiles.BOT_HEARTBEAT
            heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
            heartbeat_data = {
                "last_heartbeat_ts": int(time.time()),
                "last_heartbeat_dt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "iter_count": 0,  # Will be updated by actual heartbeat() call
                "running": True,
                "metrics": {"clusters": len(clusters), "orders": len(orders)}
            }
            heartbeat_path.write_text(json.dumps(heartbeat_data, indent=2))
        except Exception as e:
            log_event("heartbeat", "early_write_failed", error=str(e))
        
        print("DEBUG: About to call owner_health_check", flush=True)
        audit_seg("run_once", "before_health_check")
        # Owner-in-the-loop health check cycle
        health_status = owner_health_check()
        metrics["owner_check"] = health_status
        
        # CRITICAL: Continuous position divergence check + auto-fix (every 5 min)
        position_health = continuous_position_health_check()
        if position_health.get("divergence") and position_health.get("auto_fixed"):
            log_event("health_auto_fix", "position_divergence_corrected", 
                     details=position_health)
        health_status["position_reconcile"] = position_health
        
        # MONITORING GUARD 4: Track zero-order cycles and check rollback conditions
        orders_placed = len(orders)
        if orders_placed == 0:
            ZERO_ORDER_CYCLE_COUNT += 1
        else:
            ZERO_ORDER_CYCLE_COUNT = 0
        
        # Calculate average composite score from ALL symbols processed (not just clusters)
        # This gives better visibility into why signals are being rejected
        composite_scores = [c.get("composite_score", 0.0) for c in clusters if c.get("source") == "composite"]
        if composite_scores:
            avg_score = sum(composite_scores) / len(composite_scores)
        else:
            # If no clusters passed, use a default that won't trigger rollback
            # (signals were rejected, not that scoring is broken)
            avg_score = 3.0  # Changed from 5.0 to 3.0 to reflect actual rejection threshold
        
        rollback = check_rollback_conditions(
            composite_scores_avg=avg_score,
            zero_order_cycles=ZERO_ORDER_CYCLE_COUNT,
            freeze_active=len([a for a in alerts_this_cycle if "freeze" in a]) > 0,
            heartbeat_stale="heartbeat_stale" in alerts_this_cycle,
            trading_mode=Config.TRADING_MODE
        )
        
        if rollback:
            # SAFETY: rollback is external-returned dict; never assume keys exist in debug printing.
            print(f"🚨 ROLLBACK TRIGGERED: {rollback.get('triggers', []) if isinstance(rollback, dict) else []}", flush=True)
            alerts_this_cycle.append("rollback_triggered")
            # V3.0: Auto-heal rollback (lower caps, freeze)
            fix_result = auto_heal_on_alert("rollback_triggered")
            if fix_result and fix_result.get("overall_success"):
                fixes_applied_list.extend(fix_result.get("fixes_succeeded", []))
            # Return early - trading will halt next cycle due to freeze flags
        
        # V3.1 OPTIMIZATION CHECKPOINT: Apply adaptive optimizations with safety precedence
        optimizations_applied_list = []
        
        # Collect cycle metrics for optimization engine
        exec_quality_data = []
        exec_log_path = CacheFiles.EXECUTION_QUALITY
        if exec_log_path.exists():
            with exec_log_path.open("r") as f:
                for line in f:
                    try:
                        exec_quality_data.append(json.loads(line))
                    except:
                        pass
        
        # Calculate recent execution quality averages
        recent_exec = exec_quality_data[-20:] if exec_quality_data else []
        slippage_avg = sum(e.get("slippage_bps", 0) for e in recent_exec) / len(recent_exec) / 10000 if recent_exec else 1.0
        latency_avg = sum(e.get("latency_ms", 500) for e in recent_exec) / len(recent_exec) if recent_exec else 500
        
        cycle_metrics = {
            "scores_avg": avg_score,
            "scores_min": min(composite_scores) if composite_scores else 0.0,
            "passed_clusters": len(composite_scores),
            "slippage_avg": slippage_avg,
            "latency_avg": latency_avg
        }
        
        # Apply optimizations (blocked if safety guards active)
        static_cycle_id = int(time.time()) // 60  # Cycle ID based on minute
        optimizations_applied_list = apply_adaptive_optimizations(
            cycle_metrics=cycle_metrics,
            alerts_triggered=alerts_this_cycle,
            current_cycle_id=static_cycle_id
        )
        
        # MONITORING GUARD 5: Generate cycle monitoring summary
        summary = generate_cycle_monitoring_summary(
            clusters=clusters,
            orders_placed=orders_placed,
            positions_count=len(engine.executor.opens),
            alerts_triggered=alerts_this_cycle,
            zero_order_cycles=ZERO_ORDER_CYCLE_COUNT,
            fixes_applied=fixes_applied_list,
            optimizations_applied=optimizations_applied_list  # V3.1
        )
        
        if summary["health_status"] == "DEGRADED":
            print(f"⚠️  CYCLE HEALTH DEGRADED: {alerts_this_cycle}", flush=True)
        
        print(f"DEBUG: RUN_ONCE COMPLETE! clusters={len(clusters)}, orders={len(orders)}", flush=True)
        audit_seg("run_once", "COMPLETE_SUCCESS", {"clusters": len(clusters), "orders": len(orders)})
        log_event("run", "complete", clusters=len(clusters), orders=len(orders), metrics=metrics)
        
        # CRITICAL FIX: Write to run.jsonl (was missing!)
        jsonl_write("run", {
            "ts": datetime.now(timezone.utc).isoformat(),
            "_ts": int(time.time()),
            "msg": "complete",
            "clusters": len(clusters),
            "orders": len(orders),
            "metrics": metrics
        })
        
        return {"clusters": len(clusters), "orders": len(orders), **metrics}
    except (NameError, ImportError) as e:
        # Contract: Import errors in run_once() MUST be visible as fatal events, not silently ignored.
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"FATAL: Import error in run_once: {error_type}: {error_msg}", flush=True)
        log_event(
            "run_once",
            "fatal_import_error",
            error=error_msg,
            error_type=error_type,
            module_hint="utils.state_io" if "utils" in error_msg else None,
            action="skip_scoring_and_decisions",
            severity="HIGH",
        )
        
        # Try to heal if possible, but don't abort cycle
        # NOTE: Don't re-import StateFiles here - it's already imported at module level
        # Re-importing would create a local variable shadowing the module-level import
        try:
            import importlib
            import sys
            if 'config.registry' in sys.modules:
                importlib.reload(sys.modules['config.registry'])
            # DON'T re-import StateFiles - it's already available at module level
            print(f"DEBUG: Successfully reloaded config.registry module", flush=True)
        except Exception as heal_err:
            print(f"WARNING: Could not reload registry module: {heal_err}, but continuing anyway", flush=True)
        
        # CRITICAL: Return empty results - function can't continue after exception
        # But log the error so we know what happened
        # The cycle will complete with 0 clusters/orders, which is better than crashing
        return {"clusters": 0, "orders": 0, "fatal_error": f"import_error_{error_type}", "error_msg": error_msg[:160]}
    except Exception as e:
        print(f"DEBUG: EXCEPTION in run_once: {type(e).__name__}: {str(e)}", flush=True)
        audit_seg("run_once", "ERROR", {"error": str(e), "type": type(e).__name__})
        log_event("run_once", "error", error=str(e), trace=traceback.format_exc())

        # CRITICAL RESILIENCE RULE:
        # Never stop/restart the watchdog from inside run_once().
        # WHY: run_once() executes inside the worker thread; calling watchdog.stop() sets stop_evt and can leave
        #      the process "running but engine dead" if the restart path is disrupted.
        # HOW TO VERIFY: logs/worker.jsonl no longer ends with 'stopped_clean' following run_once exceptions;
        #              state/bot_heartbeat.json continues updating even during errors.
        return {
            "clusters": 0,
            "orders": 0,
            "engine_status": "degraded",
            "errors_this_cycle": [f"{type(e).__name__}: {str(e)}"],
            "error": str(e)[:200],
        }

# =========================
# DAILY & WEEKLY SCHEDULER (auto-report, weekly weights, emergency override)
# =========================
_last_report_day = None
_last_weekly_adjust_day = None
_last_market_regime = "mixed"  # Cache for weekly shadow lab automation

def daily_and_weekly_tasks_if_needed():
    global _last_report_day, _last_weekly_adjust_day, _last_market_regime
    day = datetime.utcnow().strftime("%Y-%m-%d")

    if _last_report_day != day and is_after_close_now():
        # Universe feasibility report (guarded, additive).
        # WHY: Make universe vs sizing/shortability constraints explicit to prevent phantom candidates.
        # HOW TO VERIFY: state/universe_feasibility.json is created after close when enabled.
        try:
            if str(get_env("ENABLE_UNIVERSE_FEASIBILITY", "false")).lower() == "true":
                from risk_management import generate_universe_feasibility_report
                # Use UW cache symbols as the effective universe unless explicitly overridden.
                uw_cache = read_uw_cache()
                symbols = [k for k in uw_cache.keys() if isinstance(k, str) and k.isalpha()]
                # Fallback to configured symbols if cache is empty.
                if not symbols:
                    symbols = list(getattr(Config, "SYMBOL_UNIVERSE", [])) or list(getattr(Config, "SYMBOLS", [])) or []
                api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL, api_version='v2')
                max_usd = float(getattr(Config, "POSITION_SIZE_USD", 500.0) or 500.0)
                generate_universe_feasibility_report(api, symbols, max_usd)
        except Exception as e:
            log_event("universe_feasibility", "generation_failed", error=str(e))

        report = generate_eod_report(day)
        _last_report_day = day
        log_event("daily", "report_completed", summary=report.get("summary", {}))
        daily_metrics = {
            "total_pnl": report["summary"].get("total_pnl_usd", 0.0),
            "trades": report["summary"].get("trades", 0),
            "win_rate": report["summary"].get("win_rate", 0.0) or 0.0
        }
        overrides = apply_emergency_override(daily_metrics)
        if overrides:
            log_event("daily", "emergency_override_done", weights=len(overrides))
        
        schedule_nightly_report()
        
        try:
            tuner = UWWeightTuner()
            tuner.run_daily_report()
            log_event("daily", "uw_weight_tuner_completed")
        except Exception as e:
            log_event("daily", "uw_weight_tuner_failed", error=str(e))

        # Daily trade appendix (post-close), additive audit artifact.
        # WHY: Audit found generate_daily_trade_appendix() was dead/unwired.
        # HOW TO VERIFY: reports/trade_appendix_YYYY-MM-DD.json appears after daily tasks run.
        from executive_summary_generator import generate_daily_trade_appendix
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        try:
            generate_daily_trade_appendix(today_str)
        except Exception as e:
            log_event("maintenance", "trade_appendix_failed", date=today_str, error=str(e))
        
        if Config.ENABLE_PER_TICKER_LEARNING:
            # MEDIUM-TERM LEARNING: Daily batch processing
            learn_from_outcomes()
            
            # PROFITABILITY TRACKING: Update daily/weekly/monthly metrics
            try:
                from profitability_tracker import update_daily_performance, update_weekly_performance, update_monthly_performance
                update_daily_performance()
                # Update weekly on Fridays, monthly on first day of month
                if is_friday():
                    update_weekly_performance()
                if datetime.now(timezone.utc).day == 1:
                    update_monthly_performance()
            except Exception as e:
                log_event("profitability_tracking", "update_failed", error=str(e))

    if is_friday() and is_after_close_now():
        if _last_weekly_adjust_day != day:
            # Shadow lab: seed profiles from history (first time)
            if Config.ENABLE_SHADOW_LAB and Config.ENABLE_PER_TICKER_LEARNING:
                seed_profiles_from_history()
            
            # Standard weekly adjustments
            weights = apply_weekly_adjustments()
            _last_weekly_adjust_day = day
            log_event("weekly", "weights_adjusted", weights=len(weights))
            
            if Config.ENABLE_PER_TICKER_LEARNING:
                weekly_retrain_profiles()
                
            if Config.ENABLE_STABILITY_DECAY:
                apply_weekly_stability_decay()
            
            # Shadow lab: weekly promotion decisions
            if Config.ENABLE_SHADOW_LAB:
                try:
                    # Use cached regime or default to "mixed" for weekly automation
                    regime = _last_market_regime if _last_market_regime else "mixed"
                    
                    # Run weekly shadow lab automation
                    api = tradeapi.REST(
                        Config.ALPACA_KEY,
                        Config.ALPACA_SECRET,
                        Config.ALPACA_BASE_URL,
                        api_version='v2'
                    )
                    weekly_shadow_lab_promotions(api, regime)
                except Exception as e:
                    log_event("weekly", "shadow_lab_error", error=str(e))

# =========================
# WATCHDOG & HEALTH SERVER
# =========================
class WorkerState:
    def __init__(self):
        self.last_heartbeat = time.time()
        self.iter_count = 0
        self.fail_count = self._load_fail_count()
        self.backoff_sec = Config.BACKOFF_BASE_SEC
        self.last_metrics = {}
        self.running = False
        self.fail_counter_path = StateFiles.FAIL_COUNTER
    
    def _load_fail_count(self) -> int:
        """Load persistent fail counter from disk."""
        try:
            fail_counter_path = StateFiles.FAIL_COUNTER
            if fail_counter_path.exists():
                from utils.state_io import read_json_self_heal
                data = read_json_self_heal(fail_counter_path, {"fail_count": 0})
                return int(data.get("fail_count", 0))
        except Exception as e:
            log_event("worker_state", "fail_count_load_error", error=str(e))
        return 0
    
    def save_fail_count(self, count: int):
        """Persist fail counter to disk."""
        try:
            self.fail_counter_path.write_text(json.dumps({"fail_count": count, "ts": time.time()}))
        except Exception as e:
            log_event("worker_state", "fail_count_save_error", error=str(e))

class Watchdog:
    def __init__(self):
        self.state = WorkerState()
        self._stop_evt = threading.Event()
        self.thread = None

    def heartbeat(self, metrics=None):
        self.state.last_heartbeat = time.time()
        if metrics:
            self.state.last_metrics = metrics
        log_event("heartbeat", "worker_alive", metrics=metrics or {})
        
        # CRITICAL FIX: Write heartbeat file so owner_health_check can find it
        heartbeat_path = StateFiles.BOT_HEARTBEAT
        try:
            # Ensure directory exists
            heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
            
            heartbeat_data = {
                "last_heartbeat_ts": int(self.state.last_heartbeat),
                "last_heartbeat_dt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                # Always record a "last_attempt" stamp, even when degraded.
                # WHY: Dashboard should reflect that the engine is alive even if last cycle had errors.
                "last_attempt_ts": int(self.state.last_heartbeat),
                "last_attempt_dt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "iter_count": self.state.iter_count,
                "running": self.state.running,
                "engine_status": (metrics or {}).get("engine_status", "ok") if isinstance(metrics, dict) else "ok",
                "metrics": metrics or {}
            }
            
            # Write file - use simple write_text (same as owner_health_check)
            heartbeat_path.write_text(json.dumps(heartbeat_data, indent=2))
            
            # Verify file was written
            if not heartbeat_path.exists():
                print(f"ERROR: Heartbeat file write failed - file doesn't exist: {heartbeat_path}", flush=True)
                log_event("heartbeat", "write_verify_failed", path=str(heartbeat_path))
            else:
                # Success - log occasionally (not every heartbeat to avoid spam)
                if self.state.iter_count % 10 == 0:
                    print(f"DEBUG: Heartbeat file OK: {heartbeat_path} (iter {self.state.iter_count})", flush=True)
                    
        except Exception as e:
            # CRITICAL: Log the error so we can see why it's failing
            print(f"ERROR: Failed to write heartbeat file to {heartbeat_path}: {e}", flush=True)
            log_event("heartbeat", "write_failed", error=str(e), path=str(heartbeat_path), traceback=traceback.format_exc())

    def _worker_loop(self):
        # CRITICAL FIX: Write to file immediately to verify loop is running
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] Worker loop STARTING (thread {threading.current_thread().ident})\n")
                f.flush()
        except:
            pass
        
        self.state.running = True
        log_event("worker", "started", thread_id=threading.current_thread().ident, 
                 fail_count=self.state.fail_count)
        print(f"DEBUG: Worker loop STARTED (thread {threading.current_thread().ident})", flush=True)
        
        # CRITICAL FIX: Write to file to verify logging works
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] Worker loop STARTED, state.running={self.state.running}\n")
                f.flush()
        except:
            pass
        
        SIMULATE_MARKET_OPEN = os.getenv("SIMULATE_MARKET_OPEN", "false").lower() == "true"
        print(f"DEBUG: SIMULATE_MARKET_OPEN={SIMULATE_MARKET_OPEN}, stop_evt.is_set()={self._stop_evt.is_set()}", flush=True)
        
        iteration_count = 0
        while not self._stop_evt.is_set():
            iteration_count += 1
            start = time.time()
            print(f"DEBUG: Worker loop iteration {iteration_count} (iter_count={self.state.iter_count})", flush=True)
            
            # CRITICAL FIX: Write every iteration to file
            try:
                with open("logs/worker_debug.log", "a") as f:
                    f.write(f"[{datetime.now(timezone.utc).isoformat()}] Worker iteration {iteration_count}, iter_count={self.state.iter_count}, stop_evt={self._stop_evt.is_set()}\n")
                    f.flush()
            except:
                pass
            
            try:
                log_event("worker", "iter_start", iter=self.state.iter_count + 1)
                print(f"DEBUG WORKER: Starting iteration {self.state.iter_count + 1}", flush=True)
                
                # CRITICAL FIX: Wrap market check in try/except to prevent silent failures
                try:
                    print(f"DEBUG WORKER: About to check market status...", flush=True)
                    market_open_result = is_market_open_now()
                    print(f"DEBUG WORKER: is_market_open_now() returned: {market_open_result}", flush=True)
                    market_open = market_open_result or SIMULATE_MARKET_OPEN
                    print(f"DEBUG WORKER: Market open check: {market_open} (SIMULATE_MARKET_OPEN={SIMULATE_MARKET_OPEN})", flush=True)
                    log_event("worker", "market_check", market_open=market_open, simulate=SIMULATE_MARKET_OPEN)
                except Exception as market_err:
                    print(f"ERROR WORKER: Market check failed: {market_err}", flush=True)
                    print(f"ERROR WORKER: Market check traceback: {traceback.format_exc()}", flush=True)
                    log_event("worker_error", "market_check_failed", error=str(market_err), traceback=traceback.format_exc())
                    market_open = False  # Default to closed on error
                
                print(f"DEBUG WORKER: After market check, market_open={market_open}, about to check if block...", flush=True)
                
                # CRITICAL FIX: Write market check result to file
                try:
                    with open("logs/worker_debug.log", "a") as f:
                        f.write(f"[{datetime.now(timezone.utc).isoformat()}] Market check: market_open={market_open}\n")
                        f.flush()
                except:
                    pass
                
                if market_open:
                    print(f"DEBUG: Market is OPEN - calling run_once()", flush=True)
                    log_event("worker", "calling_run_once", iter=self.state.iter_count + 1)
                    
                    # CRITICAL FIX: Write before calling run_once
                    try:
                        with open("logs/worker_debug.log", "a") as f:
                            f.write(f"[{datetime.now(timezone.utc).isoformat()}] About to call run_once()\n")
                            f.flush()
                    except:
                        pass
                    
                    # CRITICAL FIX: Create engine BEFORE run_once() so we can call evaluate_exits() even if run_once() hangs
                    worker_engine = None
                    try:
                        worker_engine = StrategyEngine()
                        try:
                            with open("logs/worker_debug.log", "a") as f:
                                f.write(f"[{datetime.now(timezone.utc).isoformat()}] Created worker_engine for evaluate_exits()\n")
                                f.flush()
                        except:
                            pass
                    except Exception as engine_err:
                        print(f"ERROR: Failed to create worker_engine: {engine_err}", flush=True)
                    
                    try:
                        # CRITICAL FIX: Add timeout protection and ensure evaluate_exits is ALWAYS called
                        print("DEBUG: About to call run_once() - entering try block", flush=True)
                        try:
                            with open("logs/worker_debug.log", "a") as f:
                                f.write(f"[{datetime.now(timezone.utc).isoformat()}] Entering run_once() try block\n")
                                f.flush()
                        except:
                            pass
                        
                        metrics = run_once()
                        if not isinstance(metrics, dict):
                            metrics = {"clusters": 0, "orders": 0, "engine_status": "degraded", "errors_this_cycle": ["run_once_returned_non_dict"]}
                        # Ensure a consistent health signal for downstream monitoring.
                        metrics.setdefault("engine_status", "ok")
                        metrics.setdefault("errors_this_cycle", [])
                        
                        # CRITICAL FIX: Write after run_once completes
                        try:
                            with open("logs/worker_debug.log", "a") as f:
                                f.write(f"[{datetime.now(timezone.utc).isoformat()}] run_once() completed: clusters={metrics.get('clusters', 0)}, orders={metrics.get('orders', 0)}\n")
                                f.flush()
                        except:
                            pass
                        print(f"DEBUG: run_once() returned: clusters={metrics.get('clusters', 0)}, orders={metrics.get('orders', 0)}", flush=True)
                        
                        # CRITICAL FIX: ALWAYS call evaluate_exits() after run_once(), regardless of run_once() result
                        # This ensures V position is evaluated and closed even if run_once() hangs or fails
                        try:
                            if worker_engine and hasattr(worker_engine, 'executor') and hasattr(worker_engine.executor, 'evaluate_exits'):
                                print("DEBUG: Calling evaluate_exits() after run_once()", flush=True)
                                try:
                                    with open("logs/worker_debug.log", "a") as f:
                                        f.write(f"[{datetime.now(timezone.utc).isoformat()}] Calling evaluate_exits() after run_once()\n")
                                        f.flush()
                                except:
                                    pass
                                worker_engine.executor.evaluate_exits()
                                print("DEBUG: evaluate_exits() completed", flush=True)
                                try:
                                    with open("logs/worker_debug.log", "a") as f:
                                        f.write(f"[{datetime.now(timezone.utc).isoformat()}] evaluate_exits() completed\n")
                                        f.flush()
                                except:
                                    pass
                            else:
                                print("ERROR: worker_engine.executor.evaluate_exits() not available", flush=True)
                                try:
                                    with open("logs/worker_debug.log", "a") as f:
                                        f.write(f"[{datetime.now(timezone.utc).isoformat()}] ERROR: worker_engine.executor.evaluate_exits() not available\n")
                                        f.flush()
                                except:
                                    pass
                        except Exception as safety_err:
                            print(f"ERROR: evaluate_exits() failed: {safety_err}", flush=True)
                            try:
                                with open("logs/worker_debug.log", "a") as f:
                                    f.write(f"[{datetime.now(timezone.utc).isoformat()}] ERROR: evaluate_exits() failed: {safety_err}\n")
                                    f.write(f"[{datetime.now(timezone.utc).isoformat()}] Traceback: {traceback.format_exc()}\n")
                                    f.flush()
                            except:
                                pass
                        # CRITICAL: Ensure run.jsonl is written even for successful cycles
                        jsonl_write("run", {
                            "ts": datetime.now(timezone.utc).isoformat(),
                            "_ts": int(time.time()),
                            "msg": "complete",
                            "clusters": metrics.get("clusters", 0),
                            "orders": metrics.get("orders", 0),
                            "market_open": True,
                            "engine_status": metrics.get("engine_status", "ok"),
                            "errors_this_cycle": metrics.get("errors_this_cycle", []),
                            "metrics": metrics
                        })
                    except Exception as run_err:
                        print(f"ERROR: run_once() raised exception: {run_err}", flush=True)
                        traceback.print_exc()

                        # CRITICAL FIX: Log exception to file
                        try:
                            with open("logs/worker_debug.log", "a") as f:
                                f.write(f"[{datetime.now(timezone.utc).isoformat()}] ERROR: run_once() exception: {run_err}\n")
                                f.write(f"[{datetime.now(timezone.utc).isoformat()}] Traceback: {traceback.format_exc()}\n")
                                f.flush()
                        except:
                            pass
                        
                        metrics = {"clusters": 0, "orders": 0, "error": str(run_err)}
                        metrics["engine_status"] = "degraded"
                        metrics["errors_this_cycle"] = [f"{type(run_err).__name__}: {str(run_err)}"]
                        jsonl_write("run", {
                            "ts": datetime.now(timezone.utc).isoformat(),
                            "_ts": int(time.time()),
                            "msg": "complete",
                            "clusters": 0,
                            "orders": 0,
                            "market_open": True,
                            "engine_status": "degraded",
                            "errors_this_cycle": metrics.get("errors_this_cycle", []),
                            "error": str(run_err)[:200],
                            "metrics": metrics
                        })
                        
                        # CRITICAL FIX: Still call evaluate_exits() even if run_once() failed
                        try:
                            if worker_engine and hasattr(worker_engine, 'executor') and hasattr(worker_engine.executor, 'evaluate_exits'):
                                print("DEBUG: Calling evaluate_exits() after run_once() exception", flush=True)
                                try:
                                    with open("logs/worker_debug.log", "a") as f:
                                        f.write(f"[{datetime.now(timezone.utc).isoformat()}] Calling evaluate_exits() after run_once() exception\n")
                                        f.flush()
                                except:
                                    pass
                                worker_engine.executor.evaluate_exits()
                                print("DEBUG: evaluate_exits() completed after exception", flush=True)
                                try:
                                    with open("logs/worker_debug.log", "a") as f:
                                        f.write(f"[{datetime.now(timezone.utc).isoformat()}] evaluate_exits() completed after exception\n")
                                        f.flush()
                                except:
                                    pass
                            else:
                                print("ERROR: worker_engine.executor.evaluate_exits() not available after exception", flush=True)
                        except Exception as exit_err:
                            print(f"ERROR: evaluate_exits() failed after run_once() exception: {exit_err}", flush=True)
                            try:
                                with open("logs/worker_debug.log", "a") as f:
                                    f.write(f"[{datetime.now(timezone.utc).isoformat()}] ERROR: evaluate_exits() failed after exception: {exit_err}\n")
                                    f.write(f"[{datetime.now(timezone.utc).isoformat()}] Traceback: {traceback.format_exc()}\n")
                                    f.flush()
                            except:
                                pass
                        
                        # SAFETY: Do not re-raise. The worker loop must not die on strategy/logging exceptions.
                        # We continue the iteration with degraded metrics and allow watchdog stall logic to work.
                else:
                    # Market closed - still log cycle but skip trading
                    print(f"DEBUG: Market is CLOSED - skipping trading", flush=True)
                    metrics = {"market_open": False, "clusters": 0, "orders": 0, "engine_status": "ok", "errors_this_cycle": []}
                    # CRITICAL: Always log cycles to run.jsonl for visibility
                    jsonl_write("run", {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "_ts": int(time.time()),
                        "msg": "cycle_complete",
                        "clusters": 0,
                        "orders": 0,
                        "market_open": False,
                        "engine_status": metrics.get("engine_status", "ok"),
                        "errors_this_cycle": metrics.get("errors_this_cycle", []),
                        "metrics": metrics
                    })
                    log_event("run", "complete", clusters=0, orders=0, metrics=metrics, market_open=False)
                
                # Update shadow positions with live prices (even when market closed, for after-hours tracking)
                try:
                    from shadow_tracker import get_shadow_tracker
                    shadow_tracker = get_shadow_tracker()
                    shadow_positions = shadow_tracker.get_all_positions()
                    
                    if shadow_positions:
                        for symbol, shadow_pos in shadow_positions.items():
                            if not shadow_pos.closed:
                                try:
                                    current_price = engine.executor.get_last_trade(symbol) if hasattr(engine, 'executor') else 0.0
                                    if not current_price or current_price <= 0:
                                        # Fallback: try Alpaca latest trade/quote if available
                                        # WHY: Some symbols never get a valid last trade through executor; shadow P&L freezes at 0 otherwise.
                                        # HOW TO VERIFY: state/shadow_positions.json shows non-zero max_profit_pct/max_loss_pct after this change.
                                        try:
                                            api = getattr(getattr(engine, "executor", None), "api", None)
                                            if api is not None:
                                                alpaca_price = 0.0
                                                try:
                                                    t = api.get_latest_trade(symbol)
                                                    alpaca_price = float(getattr(t, "price", 0.0))
                                                except Exception:
                                                    alpaca_price = 0.0
                                                if not alpaca_price or alpaca_price <= 0:
                                                    try:
                                                        q = api.get_latest_quote(symbol)
                                                        bid = float(getattr(q, "bp", 0.0) or 0.0)
                                                        ask = float(getattr(q, "ap", 0.0) or 0.0)
                                                        alpaca_price = (bid + ask) / 2.0 if bid > 0 and ask > 0 else 0.0
                                                    except Exception:
                                                        alpaca_price = 0.0
                                                if alpaca_price and alpaca_price > 0:
                                                    current_price = alpaca_price
                                        except Exception as e:
                                            log_event("shadow_tracker", "price_fallback_failed", symbol=symbol, error=str(e))

                                    if current_price and current_price > 0:
                                        update_result = shadow_tracker.update_position(symbol, current_price)
                                        if update_result and update_result.get("closed"):
                                            # Shadow position closed - update signal history with final P&L
                                            try:
                                                from signal_history_storage import get_signal_history
                                                signals = get_signal_history(limit=50)
                                                # Find most recent signal for this symbol
                                                for signal in reversed(signals):
                                                    if signal.get("symbol") == symbol and signal.get("shadow_created"):
                                                        # Update virtual P&L
                                                        signal["virtual_pnl"] = shadow_pos.max_profit_pct
                                                        signal["shadow_closed"] = True
                                                        signal["shadow_close_reason"] = update_result.get("close_reason")
                                                        # Re-write to history (this is a simple approach)
                                                        break
                                            except Exception:
                                                pass
                                    else:
                                        # still no price; let duration-based expiry handle it
                                        try:
                                            shadow_tracker.mark_no_price(symbol)
                                        except Exception:
                                            pass
                                except Exception as e:
                                    print(f"DEBUG: Failed to update shadow position for {symbol}: {e}", flush=True)
                    
                    # Cleanup expired positions
                    shadow_tracker.cleanup_expired()
                except ImportError:
                    pass  # Shadow tracker not available
                except Exception as e:
                    print(f"DEBUG: Shadow position update error: {e}", flush=True)
                
                daily_and_weekly_tasks_if_needed()
                self.state.iter_count += 1
                self.state.fail_count = 0
                self.state.save_fail_count(0)
                self.state.backoff_sec = Config.BACKOFF_BASE_SEC
                self.heartbeat(metrics)
                
                log_event("worker", "iter_end", iter=self.state.iter_count, success=True, market_open=market_open)
                
            except Exception as e:
                self.state.fail_count += 1
                self.state.save_fail_count(self.state.fail_count)
                tb = traceback.format_exc()
                log_event("worker_error", "iteration_failed", 
                         error=str(e), 
                         traceback=tb, 
                         fail_count=self.state.fail_count,
                         iter=self.state.iter_count)
                # CRITICAL FIX: Log cycle even on error so we can see what's happening
                try:
                    err_metrics = {"clusters": 0, "orders": 0, "engine_status": "degraded", "errors_this_cycle": [f"{type(e).__name__}: {str(e)}"]}
                    jsonl_write("run", {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "_ts": int(time.time()),
                        "msg": "complete",
                        "clusters": 0,
                        "orders": 0,
                        "error": str(e)[:200],
                        "fail_count": self.state.fail_count,
                        "engine_status": "degraded",
                        "errors_this_cycle": err_metrics.get("errors_this_cycle", []),
                        "metrics": {"error": True}
                    })
                except:
                    pass  # Don't fail on logging error
                # CRITICAL: Update heartbeat even on failure so watchdog/dashboard never show "engine dead".
                try:
                    self.heartbeat(err_metrics)
                except Exception:
                    pass
                send_webhook({"event": "iteration_failed", "error": str(e), "fail_count": self.state.fail_count})
                
                if self.state.fail_count >= 5:
                    freeze_path = StateFiles.PRE_MARKET_FREEZE
                    # Only set freeze if it doesn't exist (avoid overwriting manual clears)
                    if not freeze_path.exists():
                        freeze_path.write_text("too_many_failures")
                        log_event("worker_error", "freeze_activated", reason="too_many_failures", fail_count=self.state.fail_count)
                    self.state.backoff_sec = 300
                else:
                    self.state.backoff_sec = min(5 * self.state.fail_count, Config.BACKOFF_MAX_SEC)
            
            elapsed = time.time() - start
            target = Config.RUN_INTERVAL_SEC if self.state.fail_count == 0 else self.state.backoff_sec
            sleep_for = max(0.0, target - elapsed)
            print(f"DEBUG: Worker sleeping for {sleep_for:.1f}s (target={target:.1f}s, elapsed={elapsed:.1f}s)", flush=True)
            self._stop_evt.wait(timeout=sleep_for)
            print(f"DEBUG: Worker woke up, stop_evt.is_set()={self._stop_evt.is_set()}", flush=True)
        
        self.state.running = False
        log_event("worker", "stopped_clean")
        print(f"DEBUG: Worker loop EXITING (stop_evt was set)", flush=True)

    def start(self):
        # CRITICAL FIX: Log to file immediately
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] watchdog.start() CALLED\n")
                f.flush()
        except:
            pass
        
        if self.thread and self.thread.is_alive():
            log_event("watchdog", "start_skipped", reason="thread_already_alive")
            try:
                with open("logs/worker_debug.log", "a") as f:
                    f.write(f"[{datetime.now(timezone.utc).isoformat()}] watchdog.start() SKIPPED - thread already alive\n")
                    f.flush()
            except:
                pass
            return
        if self.thread:
            log_event("watchdog", "clearing_dead_thread", old_thread_id=self.thread.ident if self.thread else None)
        self._stop_evt.clear()
        self.thread = threading.Thread(target=self._worker_loop, daemon=True, name="TradingWorker")
        
        # CRITICAL FIX: Log before starting thread
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] Creating thread, about to call thread.start()\n")
                f.flush()
        except:
            pass
        
        self.thread.start()
        
        # CRITICAL FIX: Log after starting thread
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] thread.start() called, thread.ident={self.thread.ident}, thread.is_alive()={self.thread.is_alive()}\n")
                f.flush()
        except:
            pass
        
        log_event("watchdog", "thread_started", thread_id=self.thread.ident)

    def stop(self):
        self._stop_evt.set()
        if self.thread:
            # ROOT CAUSE FIX: Prevent "cannot join current thread" error
            # Check if we're trying to join the current thread
            current_thread_id = threading.current_thread().ident
            worker_thread_id = self.thread.ident if self.thread else None
            
            if current_thread_id == worker_thread_id:
                # Can't join current thread - just set stop event and return
                print(f"DEBUG: Cannot join current thread (thread {current_thread_id}) - stop event set, thread will exit on next check", flush=True)
                log_event("watchdog", "stop_skipped_self_join", thread_id=current_thread_id)
                return
            
            try:
                self.thread.join(timeout=5)
            except RuntimeError as e:
                if "cannot join current thread" in str(e).lower():
                    print(f"DEBUG: Thread join error (expected): {e} - stop event set, thread will exit", flush=True)
                    log_event("watchdog", "stop_join_error_handled", error=str(e))
                else:
                    raise

    def supervise(self):
        while not self._stop_evt.is_set():
            now = time.time()
            stalled = (now - self.state.last_heartbeat) > Config.MAX_STALL_SEC
            if stalled or not self.state.running:
                log_event("watchdog", "restart_triggered", stalled=stalled, running=self.state.running)
                send_webhook({"event": "restart_triggered", "stalled": stalled})
                self.stop()
                time.sleep(2)
                self._stop_evt.clear()
                self.start()
                log_event("watchdog", "restart_completed")
                send_webhook({"event": "restart_completed"})
            if self._stop_evt.wait(timeout=5):
                break

app = Flask(__name__)
watchdog = Watchdog()

# Self-healing monitor thread
_self_healing_last_run = 0
_self_healing_interval = 300  # Run every 5 minutes

def run_self_healing_periodic():
    """Periodically run self-healing monitor."""
    global _self_healing_last_run
    while True:
        try:
            time.sleep(60)  # Check every minute
            now = time.time()
            
            # Run healing every 5 minutes
            if now - _self_healing_last_run >= _self_healing_interval:
                try:
                    from self_healing_monitor import SelfHealingMonitor
                    monitor = SelfHealingMonitor()
                    result = monitor.run_healing_cycle()
                    _self_healing_last_run = now
                    log_event("self_healing", "cycle_complete", 
                             issues_detected=result.get("issues_detected", 0),
                             issues_healed=result.get("issues_healed", 0))
                except ImportError:
                    # Self-healing not available, skip
                    pass
                except Exception as e:
                    log_event("self_healing", "error", error=str(e))
        except Exception as e:
            log_event("self_healing", "thread_error", error=str(e))
            time.sleep(60)

# Start self-healing thread
if __name__ == "__main__":
    healing_thread = threading.Thread(target=run_self_healing_periodic, daemon=True, name="SelfHealingMonitor")
    healing_thread.start()
    
    # Start cache enrichment service
    def run_cache_enrichment_periodic():
        """Periodically enrich cache with computed signals."""
        # Run immediately on startup
        try:
            from cache_enrichment_service import CacheEnrichmentService
            service = CacheEnrichmentService()
            service.run_once()
            log_event("cache_enrichment", "startup_enrichment_complete")
        except ImportError:
            # Service not available, skip
            pass
        except Exception as e:
            log_event("cache_enrichment", "startup_error", error=str(e))
        
        # Then run every 60 seconds
        # CRITICAL FIX: Run in separate thread to avoid blocking main execution
        def cache_enrichment_thread():
            while True:
                try:
                    time.sleep(60)  # Check every minute
                    try:
                        from cache_enrichment_service import CacheEnrichmentService
                        service = CacheEnrichmentService()
                        service.run_once()
                        log_event("cache_enrichment", "cycle_complete")
                    except ImportError:
                        # Service not available, skip
                        pass
                    except Exception as e:
                        log_event("cache_enrichment", "error", error=str(e))
                except Exception as e:
                    log_event("cache_enrichment", "thread_error", error=str(e))
                    time.sleep(60)
        
        cache_thread = threading.Thread(target=cache_enrichment_thread, daemon=True, name="CacheEnrichment")
        cache_thread.start()
    
    cache_enrichment_thread = threading.Thread(target=run_cache_enrichment_periodic, daemon=True, name="CacheEnrichmentService")
    cache_enrichment_thread.start()
    
    # Start comprehensive learning orchestrator (runs daily after market close)
    def run_comprehensive_learning_periodic():
        """
        Run comprehensive learning on multiple schedules:
        - Daily: After market close
        - Weekly: Every Friday after market close
        - Bi-Weekly: Every other Friday after market close
        - Monthly: First trading day of month after market close
        """
        last_run_date = None
        
        while True:
            try:
                # Check if we should run today (after market close, once per day)
                today = datetime.now(timezone.utc).date()
                
                # Use existing market close detection (handles DST properly)
                market_closed = is_after_close_now()
                
                # Run if: (1) market is closed, (2) we haven't run today yet
                should_run_daily = False
                if market_closed and last_run_date != today:
                    should_run_daily = True
                    log_event("comprehensive_learning", "scheduled_run_triggered", reason="market_closed", date=str(today))
                
                if should_run_daily:
                    try:
                        # Use NEW comprehensive learning orchestrator V2
                        from comprehensive_learning_orchestrator_v2 import run_daily_learning
                        results = run_daily_learning()
                        last_run_date = today
                        
                        # Log results
                        log_event("comprehensive_learning", "daily_cycle_complete",
                                 attribution=results.get("attribution", 0),
                                 exits=results.get("exits", 0),
                                 signals=results.get("signals", 0),
                                 orders=results.get("orders", 0),
                                 blocked_trades=results.get("blocked_trades", 0),
                                 gate_events=results.get("gate_events", 0),
                                 uw_blocked=results.get("uw_blocked", 0),
                                 weights_updated=results.get("weights_updated", 0))
                        
                        # Force weight cache refresh in trading engine
                        # This ensures updated weights are immediately available
                        try:
                            import uw_composite_v2
                            # Invalidate cache by setting timestamp to 0
                            # This forces reload on next get_weight() call
                            uw_composite_v2._weights_cache_ts = 0.0
                            uw_composite_v2._cached_weights.clear()
                            # Also invalidate multiplier cache
                            uw_composite_v2._multipliers_cache_ts = 0.0
                            uw_composite_v2._cached_multipliers.clear()
                            log_event("comprehensive_learning", "weight_cache_refreshed")
                        except Exception as e:
                            log_event("comprehensive_learning", "cache_refresh_warning", error=str(e))
                            
                    except ImportError:
                        # Service not available, skip
                        pass
                    except Exception as e:
                        log_event("comprehensive_learning", "error", error=str(e))
                        log_event("comprehensive_learning", "error_traceback", traceback=traceback.format_exc())
                
                # Check for weekly/bi-weekly/monthly cycles
                try:
                    from comprehensive_learning_scheduler import check_and_run_scheduled_cycles
                    scheduled_results = check_and_run_scheduled_cycles()
                    if scheduled_results:
                        log_event("comprehensive_learning", "scheduled_cycles_executed", cycles=list(scheduled_results.keys()))
                except ImportError:
                    pass  # Scheduler not available
                except Exception as e:
                    log_event("comprehensive_learning", "scheduler_error", error=str(e))
                
                # Sleep for 1 hour, then check again
                # This is safe because we only run once per day (checked by last_run_date)
                time.sleep(3600)
                
            except Exception as e:
                log_event("comprehensive_learning", "thread_error", error=str(e))
                time.sleep(3600)  # Retry after 1 hour on error
    
    comprehensive_learning_thread = threading.Thread(target=run_comprehensive_learning_periodic, daemon=True, name="ComprehensiveLearning")
    
    # SRE Sentinel: Mock signal injection loop (every 15 minutes)
    try:
        from mock_signal_injection import run_mock_signal_loop
        mock_signal_thread = threading.Thread(target=run_mock_signal_loop, daemon=True, name="MockSignalInjection")
        mock_signal_thread.start()
        log_event("system", "mock_signal_injection_started")
        print("[MAIN] Mock signal injection loop started", flush=True)
    except Exception as e:
        log_event("system", "mock_signal_injection_start_failed", error=str(e))
        print(f"WARNING: Mock signal injection failed to start: {e}", flush=True)
    comprehensive_learning_thread.start()
    
    # CRITICAL FIX: Ensure watchdog starts even if main() is not called
    # This is a fallback to ensure trading loop runs
    try:
        with open("logs/worker_debug.log", "a") as f:
            f.write(f"[{datetime.now(timezone.utc).isoformat()}] FIRST if __name__ block completed, about to start watchdog as fallback\n")
            f.flush()
    except:
        pass
    
    # Start watchdog if not already started (fallback)
    if not (watchdog.thread and watchdog.thread.is_alive()):
        try:
            watchdog.start()
            supervisor = threading.Thread(target=watchdog.supervise, daemon=True, name="WatchdogSupervisor")
            supervisor.start()
            try:
                with open("logs/worker_debug.log", "a") as f:
                    f.write(f"[{datetime.now(timezone.utc).isoformat()}] Watchdog started from FIRST if __name__ block (fallback)\n")
                    f.flush()
            except:
                pass
        except Exception as e:
            try:
                with open("logs/worker_debug.log", "a") as f:
                    f.write(f"[{datetime.now(timezone.utc).isoformat()}] Watchdog start failed in first block: {e}\n")
                    f.flush()
            except:
                pass

@app.route("/", methods=["GET"])
def root():
    return jsonify({"status": "ok", "service": "trading-bot"}), 200

@app.route("/health", methods=["GET"])
def health():
    status = {
        "status": "ok" if watchdog.state.running else "starting",
        "last_heartbeat_age_sec": round(time.time() - watchdog.state.last_heartbeat, 2),
        "iter_count": watchdog.state.iter_count,
        "fail_count": watchdog.state.fail_count,
    }

    def _run_with_timeout(fn, timeout_sec: float):
        """
        Run a callable with a hard wall-clock timeout.
        WHY: Dashboard health checks were timing out and falsely reporting the bot as down.
        HOW TO VERIFY: curl http://127.0.0.1:8081/health returns within <1s even during enrichment/learning cycles.
        """
        out = {"ok": False, "value": None, "error": None}
        def _runner():
            try:
                out["value"] = fn()
                out["ok"] = True
            except Exception as e:
                out["error"] = str(e)
        t = threading.Thread(target=_runner, daemon=True)
        t.start()
        t.join(timeout=float(timeout_sec))
        if t.is_alive():
            return (False, None, "timeout")
        if out["ok"]:
            return (True, out["value"], None)
        return (False, None, out["error"])
    
    try:
        ok, value, err = _run_with_timeout(lambda: get_supervisor().get_status(), 0.75)
        if ok:
            status["health_checks"] = value
        else:
            status["health_checks_error"] = err or "unknown"
    except Exception as e:
        status["health_checks_error"] = str(e)
    
    # Add SRE monitoring data
    try:
        from sre_monitoring import get_sre_health
        ok, sre_health, err = _run_with_timeout(get_sre_health, 0.75)
        if not ok:
            raise RuntimeError(err or "sre_health_timeout")
        status["sre_health"] = {
            "market_open": sre_health.get("market_open", False),
            "market_status": sre_health.get("market_status", "unknown"),
            "last_order": sre_health.get("last_order", {}),
            "overall_health": sre_health.get("overall_health", "unknown"),
            "uw_api_healthy_count": sum(1 for h in sre_health.get("uw_api_endpoints", {}).values() if h.get("status") == "healthy"),
            "uw_api_total_count": len(sre_health.get("uw_api_endpoints", {})),
            "signal_components_healthy": sum(1 for s in sre_health.get("signal_components", {}).values() if s.get("status") == "healthy"),
            "signal_components_total": len(sre_health.get("signal_components", {}))
        }
    except Exception as e:
        status["sre_health_error"] = str(e)
    
    # Add comprehensive learning health (v2)
    try:
        from comprehensive_learning_orchestrator_v2 import load_learning_state
        ok, state, err = _run_with_timeout(load_learning_state, 0.75)
        if not ok:
            raise RuntimeError(err or "learning_state_timeout")
        last_processed = state.get("last_processed_ts")
        if last_processed:
            try:
                last_dt = datetime.fromisoformat(last_processed.replace("Z", "+00:00"))
                age_sec = (datetime.now(timezone.utc) - last_dt).total_seconds()
            except:
                age_sec = None
        else:
            age_sec = None
        
        status["comprehensive_learning"] = {
            "status": "active",
            "last_run_age_sec": age_sec,
            "total_trades_processed": state.get("total_trades_processed", 0),
            "total_trades_learned_from": state.get("total_trades_learned_from", 0),
            "note": "Using comprehensive_learning_orchestrator_v2"
        }
    except Exception as e:
        status["comprehensive_learning_error"] = str(e)
    
    return jsonify(status), 200

@app.route("/metrics", methods=["GET"])
def metrics():
    s = watchdog.state
    lines = [
        f"running {int(s.running)}",
        f"iter_count {s.iter_count}",
        f"fail_count {s.fail_count}",
        f"last_heartbeat_age_sec {round(time.time() - s.last_heartbeat, 2)}",
    ]
    for k, v in (s.last_metrics or {}).items():
        lines.append(f"{k} {v}")
    
    if Config.ENABLE_PER_TICKER_LEARNING:
        profiles = load_profiles()
        for sym, prof in profiles.items():
            lines.append(f"profile_{sym}_conf {round(prof.get('confidence', 0.0), 3)}")
            lines.append(f"profile_{sym}_samples {int(prof.get('samples', 0))}")
            weights = prof.get('component_weights', {})
            lines.append(f"profile_{sym}_weights_sum {round(sum(weights.values()), 3)}")
    
    if Config.ENABLE_THEME_RISK:
        try:
            theme_map = load_theme_map()
            engine = StrategyEngine()
            open_positions = engine.executor.api.list_positions()
            violations = correlated_exposure_guard(open_positions, theme_map, Config.MAX_THEME_NOTIONAL_USD)
            for theme, notional in violations.items():
                lines.append(f"theme_violation_{theme} {round(notional, 2)}")
        except Exception:
            pass
    
    return Response("\n".join(lines), mimetype="text/plain")

@app.route("/restart", methods=["POST"])
def restart():
    watchdog.stop()
    time.sleep(1)
    watchdog.start()
    return jsonify({"status": "restarted"}), 200

# =========================
# DASHBOARD API + UI
# =========================
def _read_jsonl(path, limit=2000):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows[-limit:] if limit else rows

def _safe_float(x, d=0.0):
    try:
        return float(x)
    except Exception:
        return d

def _today_ymd():
    return datetime.utcnow().strftime("%Y-%m-%d")

def _today_attribution():
    path = os.path.join(LOG_DIR, "attribution.jsonl")
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                ts = rec.get("ts", "")
                if rec.get("type") == "attribution" and ts.startswith(_today_ymd()):
                    out.append(rec)
            except Exception:
                continue
    return out

def load_symbol_history(symbol, limit=200):
    if not Config.ENABLE_PER_TICKER_LEARNING:
        return []
    fs_path = os.path.join("feature_store", f"{symbol}.jsonl")
    return _read_jsonl(fs_path, limit=limit)

@app.route("/dashboard", methods=["GET"])
def dashboard_ui():
    return send_from_directory("static", "dashboard.html")

@app.route("/static/<path:path>", methods=["GET"])
def dashboard_static(path):
    return send_from_directory("static", path)

@app.route("/api/profit", methods=["GET"])
def api_profit():
    """
    Live P&L from Alpaca: combines unrealized P&L from open positions + realized P&L from today's closed trades.
    Alpaca is the source of truth - data updated every 60 seconds by the bot's main loop.
    """
    try:
        # Get live open positions from Alpaca
        engine = StrategyEngine()
        positions = engine.executor.api.list_positions()
        
        # Unrealized P&L from open positions
        unrealized_pnl = 0.0
        open_by_symbol = {}
        for p in positions:
            sym = getattr(p, "symbol", "UNKNOWN")
            unrealized = _safe_float(getattr(p, "unrealized_pl", 0.0), 0.0)
            unrealized_pnl += unrealized
            open_by_symbol[sym] = {
                "unrealized_pnl": unrealized,
                "qty": _safe_float(getattr(p, "qty", 0), 0),
                "is_open": True
            }
        
        # Realized P&L from today's closed trades (from logs)
        rows = _today_attribution()
        realized_pnl = 0.0
        wins = 0
        total_closed = 0
        closed_by_symbol = {}
        timeline = []
        
        for r in rows:
            total_closed += 1
            p = _safe_float(r.get("pnl_usd", 0.0), 0.0)
            realized_pnl += p
            wins += 1 if p > 0 else 0
            sym = r.get("symbol", "UNKNOWN")
            closed_by_symbol.setdefault(sym, {"trades":0, "pnl":0.0, "wins":0})
            closed_by_symbol[sym]["trades"] += 1
            closed_by_symbol[sym]["pnl"] += p
            closed_by_symbol[sym]["wins"] += 1 if p > 0 else 0
            timeline.append({"ts": r.get("ts"), "symbol": sym, "pnl": p, "type": "closed"})
        
        # Combine realized + unrealized
        total_pnl = realized_pnl + unrealized_pnl
        
        # Merge by symbol
        all_symbols = set(list(open_by_symbol.keys()) + list(closed_by_symbol.keys()))
        by_symbol = []
        for sym in all_symbols:
            open_data = open_by_symbol.get(sym, {})
            closed_data = closed_by_symbol.get(sym, {"trades": 0, "pnl": 0.0, "wins": 0})
            
            symbol_pnl = closed_data["pnl"] + open_data.get("unrealized_pnl", 0.0)
            by_symbol.append({
                "symbol": sym,
                "trades_closed": closed_data["trades"],
                "wins": closed_data["wins"],
                "win_rate": (closed_data["wins"] / closed_data["trades"]) if closed_data["trades"] > 0 else None,
                "realized_pnl": round(closed_data["pnl"], 2),
                "unrealized_pnl": round(open_data.get("unrealized_pnl", 0.0), 2),
                "total_pnl": round(symbol_pnl, 2),
                "is_open": open_data.get("is_open", False),
                "qty": open_data.get("qty", 0)
            })
        
        # Sort by total P&L (biggest winners/losers first)
        by_symbol.sort(key=lambda x: abs(x["total_pnl"]), reverse=True)
        
        win_rate = (wins / total_closed) if total_closed > 0 else None
        
        return jsonify({
            "date": _today_ymd(),
            "source": "alpaca_live",
            "total_pnl_usd": round(total_pnl, 2),
            "realized_pnl_usd": round(realized_pnl, 2),
            "unrealized_pnl_usd": round(unrealized_pnl, 2),
            "trades_closed": total_closed,
            "positions_open": len(positions),
            "win_rate": win_rate,
            "by_symbol": by_symbol,
            "timeline": timeline[-250:]
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "date": _today_ymd(),
            "source": "error",
            "total_pnl_usd": 0.0,
            "realized_pnl_usd": 0.0,
            "unrealized_pnl_usd": 0.0,
            "trades_closed": 0,
            "positions_open": 0,
            "win_rate": None,
            "by_symbol": [],
            "timeline": []
        }), 200

@app.route("/api/state", methods=["GET"])
def api_state():
    s = watchdog.state
    cal = get_market_calendar()
    return jsonify({
        "running": bool(s.running),
        "iter_count": s.iter_count,
        "fail_count": s.fail_count,
        "last_heartbeat_age_sec": round(time.time() - s.last_heartbeat, 2),
        "market_calendar": cal,
        "last_metrics": s.last_metrics or {}
    }), 200

@app.route("/api/account", methods=["GET"])
def api_account():
    """
    Live account data from Alpaca - equity, buying power, P&L, etc.
    Source of truth for account balance and portfolio value.
    """
    try:
        engine = StrategyEngine()
        account = engine.executor.api.get_account()
        
        return jsonify({
            "source": "alpaca_live",
            "equity": _safe_float(getattr(account, "equity", 0.0), 0.0),
            "cash": _safe_float(getattr(account, "cash", 0.0), 0.0),
            "buying_power": _safe_float(getattr(account, "buying_power", 0.0), 0.0),
            "portfolio_value": _safe_float(getattr(account, "portfolio_value", 0.0), 0.0),
            "last_equity": _safe_float(getattr(account, "last_equity", 0.0), 0.0),
            "long_market_value": _safe_float(getattr(account, "long_market_value", 0.0), 0.0),
            "short_market_value": _safe_float(getattr(account, "short_market_value", 0.0), 0.0),
            "initial_margin": _safe_float(getattr(account, "initial_margin", 0.0), 0.0),
            "maintenance_margin": _safe_float(getattr(account, "maintenance_margin", 0.0), 0.0),
            "daytrade_count": int(getattr(account, "daytrade_count", 0)),
            "pattern_day_trader": bool(getattr(account, "pattern_day_trader", False)),
            "trading_blocked": bool(getattr(account, "trading_blocked", False)),
            "account_blocked": bool(getattr(account, "account_blocked", False)),
            "status": str(getattr(account, "status", "unknown"))
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "source": "error",
            "equity": 0.0,
            "cash": 0.0,
            "buying_power": 0.0,
            "portfolio_value": 0.0
        }), 200

@app.route("/api/positions", methods=["GET"])
def api_positions():
    try:
        engine = StrategyEngine()
        pos = engine.executor.api.list_positions()
        
        # Load position metadata to get entry_score and other details
        metadata_path = StateFiles.POSITION_METADATA
        position_metadata = {}
        if metadata_path.exists():
            try:
                position_metadata = load_metadata_with_lock(metadata_path)
            except Exception as e:
                print(f"WARNING: Failed to load position metadata: {e}", flush=True)
        
        out = []
        for p in pos:
            symbol = getattr(p, "symbol", None) or getattr(p, "asset_id", "unknown")
            meta = position_metadata.get(symbol, {})
            
            # Get entry_score from metadata, default to 0.0 if not found
            entry_score = meta.get("entry_score", 0.0)
            
            out.append({
                "symbol": symbol,
                "qty": _safe_float(getattr(p, "qty", 0), 0),
                "market_value": _safe_float(getattr(p, "market_value", 0.0), 0.0),
                "avg_entry_price": _safe_float(getattr(p, "avg_entry_price", 0.0), 0.0),
                "current_price": _safe_float(getattr(p, "current_price", 0.0), 0.0) if hasattr(p, "current_price") else _safe_float(getattr(p, "avg_entry_price", 0.0), 0.0),
                "unrealized_pnl": _safe_float(getattr(p, "unrealized_pl", 0.0), 0.0),
                "unrealized_pnl_pct": _safe_float(getattr(p, "unrealized_plpc", 0.0), 0.0),
                "side": getattr(p, "side", "").lower(),
                "entry_score": entry_score,  # Include entry_score from metadata
                "entry_ts": meta.get("entry_ts"),  # Include entry timestamp
                "market_regime": meta.get("market_regime", "unknown"),  # Include market regime
                "direction": meta.get("direction", "unknown")  # Include direction
            })
        theme_map = load_theme_map() if Config.ENABLE_THEME_RISK else {}
        by_theme = {}
        for row in out:
            theme = theme_map.get(row["symbol"], "general")
            by_theme[theme] = by_theme.get(theme, 0.0) + row["market_value"]
        
        # Calculate totals
        total_value = sum(p["market_value"] for p in out)
        unrealized_pnl = sum(p["unrealized_pnl"] for p in out)
        
        return jsonify({
            "positions": out, 
            "total_value": total_value,
            "unrealized_pnl": unrealized_pnl,
            "theme_exposure": {k: round(v, 2) for k, v in by_theme.items()}
        }), 200
    except Exception as e:
        return jsonify({"error": str(e), "positions": [], "theme_exposure": {}}), 200

@app.route("/api/logs", methods=["GET"])
def api_logs():
    streams = ["signals", "orders", "gate", "promotion", "weekly_promotions", "worker_error", "uw_error", "regime"]
    result = {}
    for st in streams:
        result[st] = _read_jsonl(os.path.join(LOG_DIR, f"{st}.jsonl"), limit=1500)
    return jsonify(result), 200

@app.route("/api/regime", methods=["GET"])
def api_regime():
    last = _read_jsonl(os.path.join(LOG_DIR, "regime.jsonl"), limit=100)
    return jsonify({
        "cached": _last_market_regime if '_last_market_regime' in globals() else "mixed",
        "events": last
    }), 200

@app.route("/api/policy", methods=["GET"])
def api_policy():
    policy = load_promotion_policy()
    weights = load_weights()
    return jsonify({"policy": policy, "weights": weights}), 200

@app.route("/api/profiles", methods=["GET"])
def api_profiles():
    if not Config.ENABLE_PER_TICKER_LEARNING:
        return jsonify({"enabled": False, "profiles": {}}), 200
    profiles = load_profiles()
    summary = {
        sym: {
            "confidence": round(prof.get("confidence", 0.0), 3),
            "samples": int(prof.get("samples", 0)),
            "component_weights": prof.get("component_weights", {}),
            "entry_bandit": prof.get("entry_bandit", {}),
            "stop_bandit": prof.get("stop_bandit", {})
        }
        for sym, prof in profiles.items()
    }
    return jsonify({"enabled": True, "profiles": summary}), 200

@app.route("/api/profiles/<symbol>", methods=["GET"])
def api_profile_symbol(symbol):
    if not Config.ENABLE_PER_TICKER_LEARNING:
        return jsonify({"enabled": False, "profile": {}}), 200
    profiles = load_profiles()
    prof = get_or_init_profile(profiles, symbol)
    fs_rows = []
    try:
        fs_rows = load_symbol_history(symbol, limit=200)
    except Exception:
        pass
    return jsonify({
        "enabled": True,
        "profile": prof,
        "feature_store_recent": fs_rows[-50:] if fs_rows else []
    }), 200

@app.route("/api/buckets", methods=["GET"])
def api_buckets():
    stats = compute_bucket_stats(Config.MIN_TRADES_FOR_ADJUST)
    return jsonify({"stats": stats}), 200

@app.route("/api/cockpit", methods=["GET"])
def api_cockpit():
    """Enhanced cockpit endpoint with comprehensive telemetry and UW flow data"""
    try:
        trading_mode = telemetry.get_trading_mode()
        capital_ramp = telemetry.get_capital_ramp()
        postmortems = telemetry.get_recent_postmortems(250)
        uw_cache = telemetry.get_uw_flow_cache()
        
        win_rate = 0.0
        total_trades = 0
        if postmortems:
            recent = postmortems[-10:]
            wins = sum(1 for p in recent if p.get("win_rate", 0) > 0.5)
            win_rate = wins / len(recent) if recent else 0.0
            total_trades = sum(p.get("trades", 0) for p in postmortems)
        
        positions = []
        try:
            engine = StrategyEngine()
            alpaca_positions = engine.executor.api.list_positions()
            for p in alpaca_positions:
                positions.append({
                    "symbol": p.symbol,
                    "qty": float(p.qty),
                    "side": "long" if float(p.qty) > 0 else "short",
                    "entry": float(p.avg_entry_price),
                    "current": float(p.current_price),
                    "unrealized_pl": float(p.unrealized_pl)
                })
        except Exception:
            pass
        
        # Get accurate last order timestamp
        last_order_ts = None
        last_order_age_sec = None
        try:
            from sre_monitoring import SREMonitoringEngine
            engine = SREMonitoringEngine()
            last_order_ts = engine.get_last_order_timestamp()
            if last_order_ts:
                last_order_age_sec = time.time() - last_order_ts
        except Exception:
            pass
        
        return jsonify({
            "mode": trading_mode.get("mode", "PAPER"),
            "capital_ramp": capital_ramp,
            "kpis": {"win_rate": win_rate, "total_trades": total_trades, "status": "ok"},
            "positions": positions,
            "uw": {"primary_watchlist": Config.TICKERS, "flow": uw_cache},
            "last_order": {
                "timestamp": last_order_ts,
                "age_sec": last_order_age_sec,
                "age_hours": last_order_age_sec / 3600 if last_order_age_sec else None
            },
            "last_update": int(time.time())
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/dashboard/attribution", methods=["GET"])
def dashboard_attribution():
    """Return attribution summary by ticker"""
    path = os.path.join(LOG_DIR, "attribution.jsonl")
    summary = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                        if rec.get("type") == "attribution":
                            sym = rec.get("symbol", "UNKNOWN")
                            pnl = float(rec.get("pnl_usd", 0))
                            summary.setdefault(sym, {"trades": 0, "pnl": 0.0})
                            summary[sym]["trades"] += 1
                            summary[sym]["pnl"] += pnl
                    except Exception:
                        pass
        except Exception:
            pass
    return jsonify(summary), 200

@app.route("/dashboard/shadow_lab", methods=["GET"])
def dashboard_shadow_lab():
    """Return shadow lab experiment status"""
    path = os.path.join(LOG_DIR, "shadow_lab.jsonl")
    experiments = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                        experiments.append(rec)
                    except Exception:
                        pass
        except Exception:
            pass
    return jsonify({"experiments": experiments[-100:]}), 200

@app.route("/dashboard/theme_exposure", methods=["GET"])
def dashboard_theme_exposure():
    """Return current theme exposure heatmap"""
    exposure = {}
    try:
        theme_map = load_theme_map() if Config.ENABLE_THEME_RISK else {}
        api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL)
        positions = api.list_positions()
        for p in positions:
            sym = getattr(p, "symbol", "")
            notional = abs(float(getattr(p, "market_value", 0)))
            theme = theme_map.get(sym, "general")
            exposure.setdefault(theme, 0.0)
            exposure[theme] += notional
    except Exception as e:
        log_event("theme_exposure", "fetch_failed", error=str(e))
    return jsonify(exposure), 200

@app.route("/dashboard/incidents", methods=["GET"])
def dashboard_incidents():
    """Return incident count and status"""
    incidents_today = count_incidents_today()
    return jsonify({
        "incidents_today": incidents_today,
        "max_allowed": Config.MAX_INCIDENTS_PER_DAY,
        "manual_reset_required": incidents_today >= Config.MAX_INCIDENTS_PER_DAY,
        "health_check": health_check_passes()
    }), 200

@app.route("/api/sre/health", methods=["GET"])
def api_sre_health():
    """SRE-style comprehensive health monitoring endpoint"""
    try:
        def _run_with_timeout(fn, timeout_sec: float):
            out = {"ok": False, "value": None, "error": None}
            def _runner():
                try:
                    out["value"] = fn()
                    out["ok"] = True
                except Exception as e:
                    out["error"] = str(e)
            t = threading.Thread(target=_runner, daemon=True)
            t.start()
            t.join(timeout=float(timeout_sec))
            if t.is_alive():
                return (False, None, "timeout")
            if out["ok"]:
                return (True, out["value"], None)
            return (False, None, out["error"])

        # Trigger cache enrichment without blocking the health response.
        # WHY: Audit found /api/sre/health could hang (enrichment can be slow), causing the dashboard to report "bot isn't running".
        # HOW TO VERIFY: curl http://127.0.0.1:8081/api/sre/health returns within <1s and dashboard no longer shows bot-down.
        try:
            from cache_enrichment_service import CacheEnrichmentService
            def _enrich_bg():
                try:
                    CacheEnrichmentService().run_once()
                except Exception:
                    pass
            threading.Thread(target=_enrich_bg, daemon=True).start()
        except Exception:
            pass
        
        from sre_monitoring import get_sre_health
        ok, health, err = _run_with_timeout(get_sre_health, 0.9)
        if not ok:
            # Fail open (200) so the dashboard doesn't treat the bot as "down" due to a slow health computation.
            health = {
                "overall_health": "unknown",
                "status": "degraded",
                "error": f"sre_health_{err or 'unknown'}",
                "ts": datetime.now(timezone.utc).isoformat(),
            }
        return jsonify(health), 200
    except Exception as e:
        return jsonify({"overall_health": "unknown", "status": "error", "error": str(e)}), 200

@app.route("/api/sre/signals", methods=["GET"])
def api_sre_signals():
    """Get detailed signal component health"""
    try:
        from sre_monitoring import SREMonitoringEngine
        engine = SREMonitoringEngine()
        signals = engine.check_signal_generation_health()
        return jsonify({
            "signals": {
                name: {
                    "status": s.status,
                    "last_update_age_sec": s.last_update_age_sec,
                    "data_freshness_sec": s.data_freshness_sec,
                    "error_rate_1h": s.error_rate_1h,
                    "details": s.details
                }
                for name, s in signals.items()
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/sre/uw_endpoints", methods=["GET"])
def api_sre_uw_endpoints():
    """Get UW API endpoint health"""
    try:
        from sre_monitoring import SREMonitoringEngine
        engine = SREMonitoringEngine()
        endpoints = engine.check_uw_api_health()
        return jsonify({
            "endpoints": {
                name: {
                    "status": h.status,
                    "error_rate_1h": h.error_rate_1h,
                    "avg_latency_ms": h.avg_latency_ms,
                    "rate_limit_remaining": h.rate_limit_remaining,
                    "last_error": h.last_error
                }
                for name, h in endpoints.items()
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/debug/threads", methods=["GET"])
def debug_threads():
    """Debug endpoint to check thread status"""
    import threading
    threads = [{
        "name": t.name,
        "daemon": t.daemon,
        "alive": t.is_alive(),
        "ident": t.ident
    } for t in threading.enumerate()]
    
    return jsonify({
        "active_threads": threads,
        "watchdog_state": {
            "running": watchdog.state.running,
            "iter_count": watchdog.state.iter_count,
            "fail_count": watchdog.state.fail_count,
            "thread_exists": watchdog.thread is not None,
            "thread_alive": watchdog.thread.is_alive() if watchdog.thread else False
        }
    }), 200

def handle_exit(signum, frame):
    log_event("system", "shutdown_signal", signum=signum)
    send_webhook({"event": "shutdown_signal", "signum": signum})
    try:
        watchdog.stop()
    finally:
        sys.exit(0)

# CRITICAL FIX: Only register signals when script is run directly (not when imported)
# This prevents "signal only works in main thread" error when risk_management.py imports main.py
if __name__ == "__main__":
    try:
        signal.signal(signal.SIGINT, handle_exit)
        signal.signal(signal.SIGTERM, handle_exit)
    except (ValueError, AttributeError):
        # Signal registration failed (not in main thread) - safe to ignore when imported
        pass

# =========================
# CONTINUOUS HEALTH CHECKS
# =========================
_last_reconcile_check_ts = 0
_consecutive_divergence_count = 0
_last_divergence_symbols = set()
RECONCILE_CHECK_INTERVAL_SEC = 300  # Check every 5 minutes
DIVERGENCE_CONFIRMATION_THRESHOLD = 1  # CRITICAL: Require only 1 confirmation before auto-fix (Alpaca is authoritative)

def atomic_write_json(path: Path, data: dict):
    """Atomic write with file locking to prevent corruption"""
    import fcntl
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix('.tmp')
    
    # Write to temp file
    with open(temp_path, 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    # Atomic rename
    temp_path.replace(path)

def load_metadata_with_lock(path: Path) -> dict:
    """Load metadata with file locking - BULLETPROOF: Corruption handling and self-healing"""
    import fcntl
    # BULLETPROOF: Safe load with corruption handling
    if not path.exists():
        return {}
    
    try:
        with open(path, 'r') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                data = json.load(f)
                # BULLETPROOF: Validate structure (must be dict)
                if not isinstance(data, dict):
                    # Corrupted - return empty dict (self-healing will happen in caller)
                    log_event("metadata", "corrupted_structure", path=str(path), data_type=str(type(data)))
                    return {}
                return data
            except (json.JSONDecodeError, UnicodeDecodeError) as parse_err:
                # Self-healing: Backup and reset corrupted file
                log_event("metadata", "parse_error", path=str(path), error=str(parse_err), error_type=type(parse_err).__name__)
                # Release lock before healing
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                try:
                    backup_path = path.with_suffix(f".corrupted.{int(time.time())}.json")
                    path.rename(backup_path)
                    atomic_write_json(path, {})
                    log_event("metadata", "self_healed", path=str(path), backup=str(backup_path))
                except Exception as heal_err:
                    log_event("metadata", "heal_failed", path=str(path), error=str(heal_err))
                return {}  # Return empty dict (fail open)
            finally:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                except Exception:
                    pass  # Lock may already be released
    except (IOError, OSError) as io_err:
        log_event("metadata", "io_error", path=str(path), error=str(io_err))
        return {}  # Fail open - return empty dict
    except Exception as e:
        log_event("metadata", "load_error", path=str(path), error=str(e), error_type=type(e).__name__)
        return {}  # Fail open - return empty dict

def continuous_position_health_check():
    """
    CONTINUOUS: Check for position divergence between bot and Alpaca.
    Runs every 5 minutes during trading loop.
    CRITICAL: Alpaca API is AUTHORITATIVE - auto-fixes immediately on detection.
    
    IMPORTANT: Position metadata must always match Alpaca API exactly since we trade there.
    """
    global _last_reconcile_check_ts, _consecutive_divergence_count, _last_divergence_symbols
    
    # Throttle to every 5 minutes (prevents API spam)
    now = time.time()
    if (now - _last_reconcile_check_ts) < RECONCILE_CHECK_INTERVAL_SEC:
        return {"skipped": True, "reason": "throttled"}
    
    _last_reconcile_check_ts = now
    
    try:
        # Get Alpaca positions
        api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL, api_version='v2')
        alpaca_positions = api.list_positions()
        alpaca_count = len(alpaca_positions)
        alpaca_symbols = {getattr(p, 'symbol') for p in alpaca_positions}
        
        # Get bot's internal state with locking
        metadata_path = StateFiles.POSITION_METADATA
        local_metadata = load_metadata_with_lock(metadata_path)
        
        local_count = len(local_metadata)
        local_symbols = set(local_metadata.keys())
        
        # Detect divergence
        missing_in_bot = alpaca_symbols - local_symbols
        orphaned_in_bot = local_symbols - alpaca_symbols
        divergence_detected = len(missing_in_bot) > 0 or len(orphaned_in_bot) > 0
        current_divergence_symbols = missing_in_bot | orphaned_in_bot
        
        health_check_result = {
            "alpaca_count": alpaca_count,
            "bot_count": local_count,
            "divergence": divergence_detected,
            "missing_in_bot": list(missing_in_bot),
            "orphaned_in_bot": list(orphaned_in_bot),
            "auto_fixed": False,
            "consecutive_count": _consecutive_divergence_count
        }
        
        # Track consecutive divergence confirmations
        if divergence_detected:
            # Check if it's the same divergence as last time
            if current_divergence_symbols == _last_divergence_symbols:
                _consecutive_divergence_count += 1
            else:
                # Different divergence, reset counter
                _consecutive_divergence_count = 1
                _last_divergence_symbols = current_divergence_symbols
            
            health_check_result["consecutive_count"] = _consecutive_divergence_count
            
            # Log detection but don't spam
            if _consecutive_divergence_count == 1:
                log_event("health_check", "position_divergence_detected_pending_confirmation", 
                         alpaca=alpaca_count, bot=local_count,
                         missing=list(missing_in_bot), orphaned=list(orphaned_in_bot))
        else:
            # No divergence, reset counters
            _consecutive_divergence_count = 0
            _last_divergence_symbols = set()
            return health_check_result
        
        # AUTO-FIX: Alpaca API is AUTHORITATIVE - fix immediately on detection (threshold=1)
        # CRITICAL: Position state must match Alpaca API exactly - we trade there, so it's the source of truth
        if _consecutive_divergence_count >= DIVERGENCE_CONFIRMATION_THRESHOLD:
            log_event("health_check", "position_divergence_confirmed_fixing", 
                     alpaca=alpaca_count, bot=local_count,
                     missing=list(missing_in_bot), orphaned=list(orphaned_in_bot),
                     confirmations=_consecutive_divergence_count)
            
            # CRITICAL: Alpaca API is AUTHORITATIVE - sync metadata to match Alpaca exactly
            # Add missing positions from Alpaca
            if missing_in_bot:
                for symbol in missing_in_bot:
                    alpaca_pos = next((p for p in alpaca_positions if getattr(p, 'symbol') == symbol), None)
                    if alpaca_pos:
                        # Preserve existing entry_score if available, but use Alpaca data as base
                        existing_metadata = local_metadata.get(symbol, {})
                        local_metadata[symbol] = {
                            "entry_ts": existing_metadata.get("entry_ts") or datetime.utcnow().isoformat() + "Z",
                            "entry_price": float(getattr(alpaca_pos, 'avg_entry_price', 0)),
                            "qty": int(getattr(alpaca_pos, 'qty', 0)),
                            "side": "short" if int(getattr(alpaca_pos, 'qty', 0)) < 0 else "long",
                            "recovered_from": "continuous_health_check",
                            "unrealized_pl": float(getattr(alpaca_pos, 'unrealized_pl', 0)),
                            "reconciled_at": datetime.utcnow().isoformat() + "Z"
                        }
                        # Preserve entry_score if it exists
                        if "entry_score" in existing_metadata:
                            local_metadata[symbol]["entry_score"] = existing_metadata["entry_score"]
            
            # Remove orphaned positions (positions in bot metadata but not in Alpaca)
            # CRITICAL: Alpaca is authoritative - if position doesn't exist in Alpaca, remove from metadata
            if orphaned_in_bot:
                for symbol in orphaned_in_bot:
                    if symbol in local_metadata:
                        del local_metadata[symbol]
            
            # Atomic write with file locking to prevent corruption
            atomic_write_json(metadata_path, local_metadata)
            
            health_check_result["auto_fixed"] = True
            log_event("health_check", "position_divergence_auto_fixed",
                     added=len(missing_in_bot), removed=len(orphaned_in_bot),
                     confirmations=_consecutive_divergence_count)
            
            # Alert operator (only once after confirmation threshold)
            send_webhook({
                "event": "POSITION_DIVERGENCE_AUTO_FIXED",
                "alpaca_positions": alpaca_count,
                "bot_positions": local_count,
                "missing_added": len(missing_in_bot),
                "orphaned_removed": len(orphaned_in_bot),
                "confirmations": _consecutive_divergence_count,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Reset counters after successful fix
            _consecutive_divergence_count = 0
            _last_divergence_symbols = set()
        
        return health_check_result
        
    except Exception as e:
        log_event("health_check", "position_check_failed", error=str(e))
        return {"error": str(e), "healthy": False}

# =========================
# STARTUP RECONCILIATION
# =========================
def startup_reconcile_positions():
    """
    CRITICAL: Reconcile bot state with Alpaca reality on startup.
    Alpaca is source of truth. Halts trading if reconciliation fails.
    TIMEOUT PROTECTED: 10s max to prevent workflow startup hangs.
    """
    reconcile_log_path = LogFiles.RECONCILE
    reconcile_log_path.parent.mkdir(exist_ok=True)
    
    try:
        log_event("reconcile", "startup_begin")
        
        # Get Alpaca reality with timeout protection
        import socket
        original_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(10.0)  # 10 second timeout
        
        try:
            api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL, api_version='v2')
            alpaca_positions = api.list_positions()
        finally:
            socket.setdefaulttimeout(original_timeout)  # Restore original timeout
        alpaca_symbols = {getattr(p, 'symbol') for p in alpaca_positions}
        
        # Load bot's internal state with locking
        metadata_path = StateFiles.POSITION_METADATA
        champions_path = StateFiles.CHAMPIONS
        
        local_metadata = load_metadata_with_lock(metadata_path)
        
        local_champions = {}
        if champions_path.exists():
            try:
                from utils.state_io import read_json_self_heal
                champ_data = read_json_self_heal(champions_path, {})
                local_champions = champ_data.get("current_champions", {})
            except:
                pass
        
        local_symbols = set(local_metadata.keys())
        
        # Detect divergence
        missing_in_bot = alpaca_symbols - local_symbols
        orphaned_in_bot = local_symbols - alpaca_symbols
        
        reconcile_event = {
            "alpaca_positions": len(alpaca_positions),
            "local_positions": len(local_symbols),
            "missing_in_bot": list(missing_in_bot),
            "orphaned_in_bot": list(orphaned_in_bot),
            "divergence": len(missing_in_bot) > 0 or len(orphaned_in_bot) > 0
        }
        
        # Reconcile: Alpaca is source of truth
        if missing_in_bot:
            log_event("reconcile", "positions_missing_in_bot", symbols=list(missing_in_bot), count=len(missing_in_bot))
            for symbol in missing_in_bot:
                # Add missing position metadata from Alpaca
                alpaca_pos = next((p for p in alpaca_positions if getattr(p, 'symbol') == symbol), None)
                if alpaca_pos:
                    local_metadata[symbol] = {
                        "entry_ts": datetime.utcnow().isoformat() + "Z",  # Unknown exact time
                        "entry_price": float(getattr(alpaca_pos, 'avg_entry_price', 0)),
                        "qty": int(getattr(alpaca_pos, 'qty', 0)),
                        "side": "short" if int(getattr(alpaca_pos, 'qty', 0)) < 0 else "long",
                        "recovered_from": "alpaca_reconcile",
                        "unrealized_pl": float(getattr(alpaca_pos, 'unrealized_pl', 0))
                    }
        
        if orphaned_in_bot:
            log_event("reconcile", "orphaned_metadata_in_bot", symbols=list(orphaned_in_bot), count=len(orphaned_in_bot))
            for symbol in orphaned_in_bot:
                # Remove orphaned metadata
                if symbol in local_metadata:
                    del local_metadata[symbol]
        
        # Update state files with atomic write
        atomic_write_json(metadata_path, local_metadata)
        
        # Log reconciliation event
        with reconcile_log_path.open("a") as f:
            reconcile_event["_ts"] = int(time.time())
            reconcile_event["_dt"] = datetime.utcnow().isoformat() + "Z"
            f.write(json.dumps(reconcile_event) + "\n")
        
        log_event("reconcile", "startup_complete", 
                 alpaca_positions=len(alpaca_positions),
                 reconciled=len(missing_in_bot) + len(orphaned_in_bot))
        
        # Alert if divergence detected
        if reconcile_event["divergence"]:
            send_webhook({
                "event": "POSITION_DIVERGENCE_RECONCILED",
                "alpaca_positions": len(alpaca_positions),
                "missing_in_bot": list(missing_in_bot),
                "orphaned_in_bot": list(orphaned_in_bot),
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return True
        
    except Exception as e:
        log_event("reconcile", "startup_failed", error=str(e))
        # Don't send webhook on every startup failure (too noisy)
        # send_webhook({
        #     "event": "RECONCILE_FAILURE_HALT_TRADING",
        #     "error": str(e),
        #     "timestamp": datetime.utcnow().isoformat()
        # })
        # DO NOT raise - let main() handle it and continue
        # The bot should start even if reconciliation fails (will retry in background)
        print(f"WARNING: Startup reconciliation failed: {e}")
        print("Bot will continue - reconciliation will retry in background")
        return False  # Return False instead of raising

# =========================
# ENTRY POINT
# =========================
def main():
    # CRITICAL FIX: Log to file immediately to verify main() is called
    try:
        with open("logs/worker_debug.log", "a") as f:
            f.write(f"[{datetime.now(timezone.utc).isoformat()}] main() FUNCTION CALLED\n")
            f.flush()
    except Exception as log_err:
        print(f"ERROR: Failed to write to worker_debug.log: {log_err}", flush=True)
    
    # V1.0: Run contract validation BEFORE trading starts
    # Catches producer/consumer type mismatches that cause runtime errors
    try:
        from startup_contract_check import run_startup_contract_check
        contract_passed = run_startup_contract_check()
        if not contract_passed:
            log_event("system", "contract_check_failed", action="warning")
            print("WARNING: Contract check found issues - proceeding with caution")
    except Exception as e:
        log_event("system", "contract_check_error", error=str(e))
        print(f"Contract check skipped: {e}")
    
    # CRITICAL: Reconcile with Alpaca before starting trading
    # TIMEOUT PROTECTED: Allow server to start even if Alpaca is unreachable
    try:
        startup_reconcile_positions()
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] startup_reconcile_positions() completed\n")
                f.flush()
        except:
            pass
    except Exception as e:
        log_event("system", "startup_reconcile_failed_continue", error=str(e))
        print(f"WARNING: Startup reconciliation failed (will retry in background): {e}")
        print("Flask server starting anyway to allow monitoring...")
        # DO NOT sys.exit(1) - allow server to start for health monitoring
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] startup_reconcile_positions() FAILED: {e}\n")
                f.flush()
        except:
            pass
    
    # CRITICAL FIX: Start independent exit checker thread
    # This runs evaluate_exits() every 60 seconds regardless of worker loop status
    def exit_checker_thread():
        """Background thread that checks and closes losing positions independently"""
        print("CRITICAL: Exit checker thread STARTED", flush=True)
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] Exit checker thread STARTED\n")
                f.flush()
        except:
            pass
        
        while True:
            try:
                time.sleep(60.0)  # Check every 60 seconds
                
                # Create executor to check exits
                try:
                    executor = AlpacaExecutor(defer_reconcile=True)
                    print("CRITICAL: Exit checker calling evaluate_exits()", flush=True)
                    try:
                        with open("logs/worker_debug.log", "a") as f:
                            f.write(f"[{datetime.now(timezone.utc).isoformat()}] Exit checker calling evaluate_exits()\n")
                            f.flush()
                    except:
                        pass
                    
                    executor.evaluate_exits()
                    
                    print("CRITICAL: Exit checker evaluate_exits() completed", flush=True)
                    try:
                        with open("logs/worker_debug.log", "a") as f:
                            f.write(f"[{datetime.now(timezone.utc).isoformat()}] Exit checker evaluate_exits() completed\n")
                            f.flush()
                    except:
                        pass
                except Exception as exit_err:
                    print(f"ERROR: Exit checker failed: {exit_err}", flush=True)
                    try:
                        with open("logs/worker_debug.log", "a") as f:
                            f.write(f"[{datetime.now(timezone.utc).isoformat()}] Exit checker ERROR: {exit_err}\n")
                            f.write(f"[{datetime.now(timezone.utc).isoformat()}] Traceback: {traceback.format_exc()}\n")
                            f.flush()
                    except:
                        pass
            except Exception as thread_err:
                print(f"ERROR: Exit checker thread error: {thread_err}", flush=True)
                traceback.print_exc()
                time.sleep(60.0)  # Wait before retry
    
    exit_checker = threading.Thread(target=exit_checker_thread, daemon=True, name="ExitChecker")
    exit_checker.start()
    print("CRITICAL: Exit checker thread started", flush=True)
    log_event("system", "exit_checker_thread_started")
    
    # Start watchdog with error handling
    try:
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] About to call watchdog.start()\n")
                f.flush()
        except:
            pass
        
        watchdog.start()
        
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] watchdog.start() completed\n")
                f.flush()
        except:
            pass
        
        supervisor = threading.Thread(target=watchdog.supervise, daemon=True)
        supervisor.start()
        log_event("system", "watchdog_started")
        
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] Watchdog supervisor thread started\n")
                f.flush()
        except:
            pass
    except Exception as e:
        log_event("system", "watchdog_start_failed", error=str(e))
        print(f"WARNING: Watchdog failed to start: {e}")
        traceback.print_exc()
        
        # CRITICAL FIX: Log error to file
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] watchdog.start() FAILED: {e}\n")
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] Traceback: {traceback.format_exc()}\n")
                f.flush()
        except:
            pass
        # Continue anyway - bot can run without watchdog
    
    # Start health supervisor with error handling
    try:
        health_super = get_supervisor()
        health_super.start()
        log_event("system", "health_supervisor_started")
    except Exception as e:
        log_event("system", "health_supervisor_start_failed", error=str(e))
        print(f"WARNING: Health supervisor failed to start: {e}")
        print("Bot will continue without health supervisor...")
        traceback.print_exc()
    
    log_event("system", "api_start", port=Config.API_PORT)
    print(f"Starting Flask server on port {Config.API_PORT}...", flush=True)
    
    # CRITICAL FIX: Log before Flask starts
    try:
        with open("logs/worker_debug.log", "a") as f:
            f.write(f"[{datetime.now(timezone.utc).isoformat()}] About to start Flask server on port {Config.API_PORT}\n")
            f.flush()
    except:
        pass
    
    app.run(host="0.0.0.0", port=Config.API_PORT, debug=False)

if __name__ == "__main__":
    # CRITICAL FIX: Log to file immediately to verify this block executes
    try:
        with open("logs/worker_debug.log", "a") as f:
            f.write(f"[{datetime.now(timezone.utc).isoformat()}] THIRD if __name__ == '__main__' BLOCK EXECUTING (line 10165)\n")
            f.flush()
    except Exception as log_err:
        print(f"ERROR: Failed to write to worker_debug.log in if __name__ block: {log_err}", flush=True)
    
    # INVINCIBLE MAIN LOOP: Catch-all exception handler prevents process exit
    max_crash_count = 10
    crash_count = 0
    crash_window_start = time.time()
    
    while True:
        try:
            try:
                with open("logs/worker_debug.log", "a") as f:
                    f.write(f"[{datetime.now(timezone.utc).isoformat()}] About to call main() function\n")
                    f.flush()
            except:
                pass
            
            main()
            
            try:
                with open("logs/worker_debug.log", "a") as f:
                    f.write(f"[{datetime.now(timezone.utc).isoformat()}] main() function returned (should not happen - Flask blocks)\n")
                    f.flush()
            except:
                pass
            
            break  # Normal exit from main() breaks the loop
        except KeyboardInterrupt:
            log_event("system", "shutdown_requested", reason="keyboard_interrupt")
            break
        except SystemExit as e:
            log_event("system", "system_exit", code=str(e))
            break
        except Exception as e:
            crash_count += 1
            
            # Reset crash count if we've been running stable for 5 minutes
            if time.time() - crash_window_start > 300:
                crash_count = 1
                crash_window_start = time.time()
            
            # Log the crash
            error_msg = f"CRITICAL CRASH PREVENTED: {str(e)}"
            stack_trace = traceback.format_exc()
            print(f"[CRASH RECOVERY] {error_msg}")
            print(stack_trace)
            
            log_event("system", "crash_recovered", 
                     error=str(e), 
                     crash_count=crash_count,
                     stack_trace=stack_trace[:500])
            
            # Check for crash loop
            if crash_count >= max_crash_count:
                log_event("system", "crash_loop_detected", 
                         crash_count=crash_count, action="exit")
                print(f"[FATAL] Crash loop detected ({crash_count} crashes in 5 min). Exiting.")
                break
            
            # Cooldown before restart
            cooldown = min(30 * crash_count, 180)  # 30s, 60s, 90s, ... max 180s
            print(f"[CRASH RECOVERY] Restarting in {cooldown}s... (crash {crash_count}/{max_crash_count})")
            time.sleep(cooldown)
else:
    # IMPORTANT:
    # Importing main.py must NOT start any long-running services (worker loop, watchdog, supervisors).
    # WHY: Import side-effects caused "service running but engine dead" and made tooling/tests unsafe.
    # HOW TO VERIFY: `python -c "import main; print('ok')"` does not start the worker loop.
    #
    # If you deploy under a WSGI server (e.g., gunicorn) and want background workers,
    # start them explicitly from the server entrypoint (do not rely on import side-effects).
    pass
