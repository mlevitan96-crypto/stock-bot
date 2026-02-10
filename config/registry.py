#!/usr/bin/env python3
"""
Centralized Configuration Registry
===================================
Single source of truth for all paths, thresholds, and constants.
ALL modules MUST import from here - no hardcoded paths allowed.

Usage:
    from config.registry import Paths, Thresholds, CacheFiles, get_env

Author: Trading Bot System
Last Updated: 2025-11-28
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, TypeVar, Union

T = TypeVar('T')


def get_env(key: str, default: T = None, cast: type = str) -> Union[T, str]:
    """Get environment variable with type casting and default."""
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return cast(val) if cast != str else val
    except (ValueError, TypeError):
        return default


def get_env_bool(key: str, default: bool = False) -> bool:
    """
    Read a boolean environment variable safely.
    Accepts: 1/0, true/false, yes/no, on/off (case-insensitive).
    """
    try:
        raw = os.getenv(key)
        if raw is None:
            return bool(default)
        s = str(raw).strip().lower()
        if s in ("1", "true", "yes", "y", "on"):
            return True
        if s in ("0", "false", "no", "n", "off"):
            return False
        return bool(default)
    except Exception:
        return bool(default)


class Directories:
    """All directory paths - create if not exist."""
    ROOT = Path(".")
    DATA = Path("data")
    STATE = Path("state")
    LOGS = Path("logs")
    CONFIG = Path("config")
    SIGNALS = Path("signals")
    HEARTBEATS = Path("state/heartbeats")
    
    @classmethod
    def ensure_all(cls):
        """Create all directories if they don't exist."""
        for attr in ['DATA', 'STATE', 'LOGS', 'CONFIG', 'HEARTBEATS']:
            getattr(cls, attr).mkdir(parents=True, exist_ok=True)


class CacheFiles:
    """All cache and data files - single source of truth."""
    
    UW_FLOW_CACHE = Directories.DATA / "uw_flow_cache.json"
    UW_FLOW_CACHE_LOG = Directories.DATA / "uw_flow_cache.log.jsonl"
    UW_EXPANDED_INTEL = Directories.DATA / "uw_expanded_intel.json"
    UW_RATE_LIMITER_STATE = Directories.DATA / "uw_rate_limiter_state.json"
    UW_API_QUOTA = Directories.DATA / "uw_api_quota.jsonl"
    COMPOSITE_CACHE = Directories.DATA / "composite_cache.json"
    OPERATOR_DASHBOARD = Directories.DATA / "operator_dashboard.json"
    HEALTH_STATUS = Directories.DATA / "health_status.json"
    SELF_HEAL_EVENTS = Directories.DATA / "self_heal_events.jsonl"
    SELF_HEAL_ESCALATIONS = Directories.DATA / "self_heal_escalations.json"
    ALERTS = Directories.DATA / "alerts.jsonl"
    LIVE_ORDERS = Directories.DATA / "live_orders.jsonl"
    
    UW_WEIGHTS = Directories.DATA / "uw_weights.json"
    DEBATE_SUMMARY = Directories.DATA / "debate_summary.json"
    KNOWLEDGE_GRAPH = Directories.DATA / "knowledge_graph.json"
    KG_REPORT = Directories.DATA / "knowledge_graph_report.json"
    GRAPH_REASONER_REPORT = Directories.DATA / "graph_reasoner_report.json"
    META_LEARNING_REPORT = Directories.DATA / "meta_learning_report.json"
    RESEARCH_BACKLOG = Directories.DATA / "research_backlog.json"
    BAYES_ALPHA_REPORT = Directories.DATA / "bayes_alpha_report.json"
    EXECUTION_ALPHA_REPORT = Directories.DATA / "execution_alpha_report.json"
    REGIME_SWITCHER_REPORT = Directories.DATA / "regime_switcher_report.json"
    STRATEGIC_PLANNER_REPORT = Directories.DATA / "strategic_planner_report.json"
    EVOLUTION_LAB_REPORT = Directories.DATA / "evolution_lab_report.json"
    
    GOVERNANCE_EVENTS = Directories.DATA / "governance_events.jsonl"
    COORDINATOR_DECISIONS = Directories.DATA / "coordinator_decisions.jsonl"
    UW_ATTRIBUTION = Directories.DATA / "uw_attribution.jsonl"
    HEALTH_CHECKS = Directories.DATA / "health_checks.jsonl"
    DAILY_POSTMORTEM = Directories.DATA / "daily_postmortem.jsonl"
    FEATURE_STORE = Directories.DATA / "feature_store.jsonl"
    PNL_ATTRIBUTION = Directories.DATA / "pnl_attribution.jsonl"
    EXECUTION_QUALITY = Directories.DATA / "execution_quality.jsonl"


class StateFiles:
    """All state files - single source of truth."""
    
    SIGNAL_WEIGHTS = Directories.STATE / "signal_weights.json"
    PORTFOLIO_GOVERNOR = Directories.STATE / "portfolio_governor.json"
    AUTONOMY_TUNING = Directories.STATE / "autonomy_tuning.json"
    TOXICITY_SIGNAL = Directories.STATE / "toxicity_signal.json"
    REGIME_DETECTOR = Directories.STATE / "regime_detector.json"
    ALPHA_WEIGHTS = Directories.STATE / "alpha_weights.json"
    ALPHA_SUITE = Directories.STATE / "alpha_suite.json"
    CORRELATION_MAP = Directories.STATE / "correlation_map.json"
    HYSTERESIS_STATE = Directories.STATE / "hysteresis_state.json"
    CONFLICT_OUTCOMES = Directories.STATE / "conflict_outcomes.json"
    EXEC_WEIGHT_NUDGES = Directories.STATE / "exec_weight_nudges.json"
    PLAYBOOKS = Directories.STATE / "playbooks.json"
    ADAPTIVE_GATE_STATE = Directories.STATE / "adaptive_gate_state.json"
    PRIMARY_ELECTION = Directories.STATE / "primary_election.json"
    OPPOSITION_PENALTY = Directories.STATE / "opposition_penalty.json"
    DRIFT_REPORT = Directories.STATE / "drift_report.json"
    
    BOT_HEARTBEAT = Directories.STATE / "bot_heartbeat.json"
    POSITION_METADATA = Directories.STATE / "position_metadata.json"
    DISPLACEMENT_COOLDOWNS = Directories.STATE / "displacement_cooldowns.json"
    INTERNAL_POSITIONS = Directories.STATE / "internal_positions.json"
    SMART_POLLER = Directories.STATE / "smart_poller.json"
    FAIL_COUNTER = Directories.STATE / "fail_counter.json"
    CHAMPIONS = Directories.STATE / "champions.json"
    PRE_MARKET_FREEZE = Directories.STATE / "pre_market_freeze.flag"
    # WHY: Universe feasibility report enables actionable constraints alignment.
    # HOW TO VERIFY: state/universe_feasibility.json exists and updates daily when enabled.
    UNIVERSE_FEASIBILITY = Directories.STATE / "universe_feasibility.json"

    # WHY: Droplet uses regime_detector_state.json; dashboard previously read regime_detector.json and defaulted to MIXED.
    # HOW TO VERIFY: Dashboard regime matches state/regime_detector_state.json (e.g., PANIC confidence=1.0).
    REGIME_DETECTOR_STATE = Directories.STATE / "regime_detector_state.json"

    # STRUCTURAL UPGRADE (2026-01-20): Market context + posture snapshots (additive).
    # WHY: Provide stable, cached market context inputs (premarket/overnight + vol term proxy) and posture outputs.
    # HOW TO VERIFY: state/market_context_v2.json and state/regime_posture_state.json update during trading cycles.
    MARKET_CONTEXT_V2 = Directories.STATE / "market_context_v2.json"
    REGIME_POSTURE_STATE = Directories.STATE / "regime_posture_state.json"
    SYMBOL_RISK_FEATURES = Directories.STATE / "symbol_risk_features.json"

    # Health subsystem: safe mode flag (decision integrity FAIL => no auto-resume; human must clear).
    HEALTH_SAFE_MODE = Directories.STATE / "health_safe_mode.flag"

    # Signal context: first time any signal fired per symbol/day (for entry_delay_seconds).
    FIRST_SIGNAL_TS = Directories.STATE / "first_signal_ts.json"

    # Wheel strategy: assigned shares and open CSP/CC tracking.
    WHEEL_STATE = Directories.STATE / "wheel_state.json"

    # Open-position signal propagation: last evaluated signal strength per symbol (dashboard + audit).
    SIGNAL_STRENGTH_CACHE = Directories.STATE / "signal_strength_cache.json"
    # Signal correlation analytics (read-only): top pairs and per-symbol concentration.
    SIGNAL_CORRELATION_CACHE = Directories.STATE / "signal_correlation_cache.json"


class LogFiles:
    """All log files - single source of truth."""
    
    # CRITICAL: Attribution log path - MUST be used by all components (main.py, friday_eow_audit.py, dashboard.py)
    ATTRIBUTION = Directories.LOGS / "attribution.jsonl"
    
    TRADING = Directories.LOGS / "trading.jsonl"
    ORDERS = Directories.LOGS / "orders.jsonl"
    POSITIONS = Directories.LOGS / "positions.jsonl"
    EXITS = Directories.LOGS / "exits.jsonl"
    TELEMETRY = Directories.LOGS / "telemetry.jsonl"
    COMPOSITE_ATTRIBUTION = Directories.LOGS / "composite_attribution.jsonl"
    ALERT_ERROR = Directories.LOGS / "alert_error.jsonl"
    
    WATCHDOG_EVENTS = Directories.LOGS / "watchdog_events.jsonl"
    AUTOEXIT_ACTIONS = Directories.LOGS / "autoexit_actions.jsonl"
    DEPLOYMENT_SUPERVISOR = Directories.LOGS / "deployment_supervisor.jsonl"
    
    UW_DAEMON = Directories.LOGS / "uw_daemon.jsonl"
    UW_ERRORS = Directories.LOGS / "uw_errors.jsonl"
    RECONCILE = Directories.LOGS / "reconcile.jsonl"
    # WHY: Central P&L reconciliation log for auditing day vs window vs attribution.
    # HOW TO VERIFY: logs/pnl_reconciliation.jsonl gets appended by dashboard /api/pnl/reconcile.
    PNL_RECONCILIATION = Directories.LOGS / "pnl_reconciliation.jsonl"

    # Permanent, unified system events stream (append-only).
    SYSTEM_EVENTS = Directories.LOGS / "system_events.jsonl"
    SHADOW = Directories.LOGS / "shadow.jsonl"
    # Phase-2: canonical run log (trade_intent, exit_intent, cycle summaries).
    RUN = Directories.LOGS / "run.jsonl"

    # Signal context capture: full signal state at every trade decision (enter/blocked/exit) for profitability learning.
    # HOW TO VERIFY: logs/signal_context.jsonl grows on each decision; no trading logic changed.
    SIGNAL_CONTEXT = Directories.LOGS / "signal_context.jsonl"

    # EOD canonical bundle (MEMORY_BANK 5.5): single source for trade/exit data; dashboard MUST use these paths.
    MASTER_TRADE_LOG = Directories.LOGS / "master_trade_log.jsonl"
    EXIT_ATTRIBUTION = Directories.LOGS / "exit_attribution.jsonl"


class ConfigFiles:
    """All configuration files."""
    
    THEME_RISK = Directories.CONFIG / "theme_risk.json"
    EXECUTION_ROUTER = Directories.CONFIG / "execution_router.json"
    STARTUP_SAFETY = Directories.CONFIG / "startup_safety_suite_v2.json"


class Thresholds:
    """All tunable thresholds - centralized defaults with env override."""
    
    MIN_EXEC_SCORE = get_env("MIN_EXEC_SCORE", 3.0, float)  # V3.0: Increased to 3.0 for predatory entry filter
    MAX_CONCURRENT_POSITIONS = get_env("MAX_CONCURRENT_POSITIONS", 16, int)  # Increased from 12 - was capacity constrained
    MAX_NEW_POSITIONS_PER_CYCLE = 6
    
    TRAILING_STOP_PCT = get_env("TRAILING_STOP_PCT", 0.015, float)
    PROFIT_SCALE_PCT = get_env("PROFIT_SCALE_PCT", 0.02, float)
    # TIME EXIT: Allow institutional signals time to develop
    # Updated 2025-12-11 per forensic audit: 90min was too aggressive ("scalp or die")
    # 240min (4h) allows morning entries to breathe until afternoon
    TIME_EXIT_MINUTES = get_env("TIME_EXIT_MINUTES", 240, int)
    TIME_EXIT_DAYS_STALE = get_env("TIME_EXIT_DAYS_STALE", 12, int)
    TIME_EXIT_STALE_PNL_THRESH_PCT = get_env("TIME_EXIT_STALE_PNL_THRESH_PCT", 0.03, float)
    
    # DISPLACEMENT: Reduced churn to prevent spread losses and commission drag
    # Updated 2025-12-11 per forensic audit: aggressive settings caused excessive turnover
    DISPLACEMENT_MIN_AGE_HOURS = get_env("DISPLACEMENT_MIN_AGE_HOURS", 4, int)  # Was 1h, now 4h
    DISPLACEMENT_MAX_PNL_PCT = get_env("DISPLACEMENT_MAX_PNL_PCT", 0.01, float)  # Was 0.5%, now 1%
    DISPLACEMENT_SCORE_ADVANTAGE = get_env("DISPLACEMENT_SCORE_ADVANTAGE", 2.0, float)  # Was 1.0, now 2.0
    DISPLACEMENT_COOLDOWN_HOURS = get_env("DISPLACEMENT_COOLDOWN_HOURS", 6, int)  # Was 4h, now 6h
    
    POSITION_SIZE_USD = get_env("POSITION_SIZE_USD", 500, float)
    MAX_THEME_NOTIONAL_USD = get_env("MAX_THEME_NOTIONAL_USD", 50000, float)
    
    HB_INTERVAL_SEC = get_env("HB_INTERVAL_SEC", 60, int)
    STALL_SEC = get_env("STALL_SEC", 300, int)
    AUTOEXIT_INTERVAL_SEC = get_env("AUTOEXIT_INTERVAL_SEC", 60, int)
    
    UW_POLL_INTERVAL_SEC = get_env("UW_POLL_INTERVAL_SEC", 120, int)
    UW_RATE_LIMIT_CALLS = get_env("UW_RATE_LIMIT_CALLS", 50, int)
    UW_RATE_LIMIT_PERIOD = get_env("UW_RATE_LIMIT_PERIOD", 60, int)


class StrategyFlags:
    """
    v2-only engine flags.

    NOTE:
    - Composite is v2-only (no version switching).
    """

    # Reserved for future gating toggles (keep empty for now).
    pass


# Composite v2 weights (active engine)
# -------------------------------------------------
# Contract:
# - v2 is the only composite engine in production (paper-only)
# - weights are explicit, documented, and safe-by-default
COMPOSITE_WEIGHTS_V2: Dict[str, Any] = {
    "version": "2026-01-20_wt1",

    # Volatility reward (annualized realized vol)
    "vol_center": 0.20,
    "vol_scale": 0.25,
    "vol_bonus_max": 0.70,
    # Penalty for low-vol names in high-vol regimes (applied only when vol_regime == "high")
    "low_vol_penalty_center": 0.15,
    "low_vol_penalty_max": -0.15,

    # Beta reward (vs SPY)
    "beta_center": 1.00,
    "beta_scale": 1.00,
    "beta_bonus_max": 0.45,

    # UW strength proxy (uses conviction + trade_count)
    "uw_center": 0.55,
    "uw_scale": 0.45,
    "uw_bonus_max": 0.25,

    # Premarket / futures proxy alignment (uses SPY/QQQ overnight direction from market_context_v2)
    "premarket_align_bonus": 0.15,
    "premarket_misalign_penalty": -0.15,

    # Regime/posture alignment
    "regime_align_bonus": 0.55,
    "regime_misalign_penalty": -0.35,
    "posture_conf_strong": 0.65,

    # Vol-regime multipliers
    "high_vol_multiplier": 1.15,
    "mid_vol_multiplier": 1.00,
    "low_vol_multiplier": 0.90,

    # Alignment dampening (avoid boosting misaligned directions)
    "misalign_dampen": 0.25,
    "neutral_dampen": 0.60,

    # Optional shaping (applied when V2_SHAPING_ENABLED==true)
    "shape_vol_gamma": 1.8,
    "shape_vol_bonus_max": 0.15,
    "shape_regime_align_bonus": 0.10,
    "shape_uw_weak_penalty_max": -0.10,
    "shape_uw_weak_threshold": 0.35,
    "shape_trade_count_strong": 15,

    # UW intelligence layer (v2-only, additive)
    "uw": {
        "version": "2026-01-20_uw_v1",
        # Versioning for downstream attribution/dashboard (additive metadata only)
        "sector_profile_version": "2026-01-20_sector_profiles_v1",
        "regime_profile_version": "2026-01-20_regime_v1",
        "pnl_tuning_version": "2026-01-20_pnl_tuning_v1",
        # Tuning hooks (weights; no auto-application)
        # NOTE: These are used by v2 scoring as multipliers for each UW-derived adjustment term.
        "flow_strength_weight": 1.0,
        "darkpool_bias_weight": 1.0,
        "sentiment_weight": 1.0,
        "earnings_proximity_weight": 1.0,
        "sector_alignment_weight": 1.0,
        "regime_alignment_weight": 1.0,
        # Inputs are expected from state/premarket_intel.json and/or state/postmarket_intel.json
        "flow_strength_bonus_max": 0.20,
        "darkpool_bias_bonus_max": 0.12,
        "sentiment_bonus_max": 0.10,
        "earnings_proximity_penalty_max": -0.12,  # closer earnings => more risk
        "sector_alignment_bonus_max": 0.12,
        "regime_alignment_bonus_max": 0.08,
        # normalization knobs
        "earnings_penalty_days": 3,  # within N days => penalize
    },
}


class APIConfig:
    """API configuration - centralized."""
    
    ALPACA_BASE_URL = get_env("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    ALPACA_DATA_URL = get_env("ALPACA_DATA_URL", "https://data.alpaca.markets")
    UW_BASE_URL = get_env("UW_BASE_URL", "https://api.unusualwhales.com")
    
    @classmethod
    def get_alpaca_headers(cls) -> dict:
        """Get Alpaca API headers."""
        return {
            "APCA-API-KEY-ID": os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY", ""),
            "APCA-API-SECRET-KEY": os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET", "")
        }
    
    @classmethod
    def get_uw_headers(cls) -> dict:
        """Get Unusual Whales API headers."""
        return {
            "Authorization": f"Bearer {os.getenv('UW_API_KEY', '')}",
            "Accept": "application/json"
        }


class DashboardAuthConfig:
    """
    Dashboard authentication config (HTTP Basic).

    Contract:
    - The dashboard MUST fail-closed if credentials are missing.
    - Credentials MUST come from environment variables (loaded from `/root/stock-bot/.env` on droplet).
    """

    DASHBOARD_USER = get_env("DASHBOARD_USER", None, str)
    DASHBOARD_PASS = get_env("DASHBOARD_PASS", None, str)

    @classmethod
    def validate_or_die(cls) -> None:
        """Fail-closed if required auth env vars are missing/empty."""
        missing = []
        for k in ("DASHBOARD_USER", "DASHBOARD_PASS"):
            v = os.getenv(k)
            if v is None or str(v).strip() == "":
                missing.append(k)

        if missing:
            print(
                "[DashboardAuth] CONTRACT VIOLATION: Missing required environment variables "
                f"{missing}. Refusing to start dashboard. "
                "Set these in `/root/stock-bot/.env` (droplet) and restart the dashboard.",
                flush=True,
            )
            raise SystemExit(1)


# UW intelligence layer (v2) limits (aggressive but safe)
# ------------------------------------------------------
# Contract:
# - These limits are enforced by `src/uw/uw_client.py`
# - Defaults can be overridden via env vars of the same names
UW_RATE_LIMIT_PER_MIN = get_env("UW_RATE_LIMIT_PER_MIN", 120, int)
UW_DAILY_LIMIT = get_env("UW_DAILY_LIMIT", 15000, int)
UW_SAFETY_BUFFER = get_env("UW_SAFETY_BUFFER", 0.95, float)


# Daily dynamic universe scoring config (v1 for the universe builder)
DAILY_UNIVERSE_SCORING_V1: Dict[str, Any] = {
    "version": "2026-01-20_universe_v1",
    "weights": {
        "volatility": 0.30,
        "premarket_activity": 0.20,
        "uw_flow": 0.20,
        "uw_darkpool": 0.10,
        "uw_sentiment": 0.10,
        "earnings_proximity": 0.10,
    },
}

# Daily dynamic universe scoring config (v2-only)
DAILY_UNIVERSE_SCORING_V2: Dict[str, Any] = {
    "version": "2026-01-20_universe_v2",
    "weights": {
        "volatility": 0.25,
        "premarket_activity": 0.20,
        "uw_flow": 0.20,
        "uw_darkpool": 0.10,
        "uw_sentiment": 0.10,
        "earnings_proximity": 0.10,
        "sector_alignment": 0.05,
        "regime_alignment": 0.05,
    },
}


class SignalComponents:
    """Signal component names - must match across all modules."""
    
    ALL_COMPONENTS = [
        "flow",
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
        "greeks_gamma",
        "ftd_pressure",
        "iv_rank",
        "oi_change",
        "etf_flow",
        "squeeze_score",
        "freshness_factor"
    ]
    
    @classmethod
    def validate_component(cls, name: str) -> bool:
        """Check if component name is valid."""
        return name in cls.ALL_COMPONENTS


def read_json(path: Path, default: Any = None) -> Any:
    """Safely read JSON file with default fallback."""
    import json
    try:
        if path.exists():
            raw_data = path.read_text()
            if not raw_data.strip():
                return default if default is not None else {}
            data = json.loads(raw_data)
            # BULLETPROOF: Validate structure (must be dict for metadata files)
            if isinstance(data, dict):
                return data
            else:
                # Return empty dict for non-dict data (fail open)
                return {}
    except (json.JSONDecodeError, IOError, UnicodeDecodeError) as e:
        # Log corruption but continue with default
        return default if default is not None else {}
    except Exception:
        pass
    return default if default is not None else {}


def atomic_write_json(path: Path, data: Any) -> None:
    """Atomically write JSON file (write to temp, then rename)."""
    import json
    # BULLETPROOF: Safe atomic write with error handling
    try:
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        # Write to temp file first
        tmp.write_text(json.dumps(data, indent=2))
        # Atomic rename
        tmp.replace(path)
    except (IOError, OSError, json.JSONEncodeError) as e:
        # Log error but don't crash - write failures are logged but non-fatal
        import logging
        logging.error(f"atomic_write_json failed for {path}: {e}")
        raise  # Re-raise so caller can handle


def append_jsonl(path: Path, record: dict) -> None:
    """Append record to JSONL file."""
    import json
    from datetime import datetime, timezone
    record["_ts"] = int(datetime.now(timezone.utc).timestamp())
    record["_dt"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with path.open("a") as f:
        f.write(json.dumps(record) + "\n")


Directories.ensure_all()
