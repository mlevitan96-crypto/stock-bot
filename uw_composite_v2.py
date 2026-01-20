#!/usr/bin/env python3
"""
UW Composite Scoring V3.1
Full Intelligence Pipeline with Adaptive Signal Weight Optimization

V3.1 Enhancements:
- Adaptive weight multipliers (0.25x-2.5x) learned from trade outcomes
- Directional conviction engine for unified long/short scoring
- Continuous weight tuning instead of binary signal activation
- Exit signal optimization with separate adaptive weights

V3 Features (retained):
- Congress/Politician trading signals
- Short interest & squeeze detection
- Institutional flow alignment
- Market tide sentiment
- Economic/FDA/Earnings calendar awareness
"""

import json
import time
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

MOTIF_STATE = Path("state/uw_motifs.json")
THRESHOLD_STATE = Path("state/uw_thresholds_hierarchical.json")
AUDIT_LOG = Path("data/audit_uw_upgrade.jsonl")
EXPANDED_INTEL_CACHE = Path("data/uw_expanded_intel.json")
GATE_DIAGNOSTIC_LOG = Path("logs/gate_diagnostic.jsonl")

# Permanent system events + global failure wrapper (non-blocking import).
try:
    from utils.system_events import global_failure_wrapper, log_system_event
except Exception:
    def global_failure_wrapper(_subsystem):  # type: ignore
        def _d(fn):
            return fn
        return _d
    def log_system_event(*args, **kwargs):  # type: ignore
        return None

_adaptive_optimizer = None

def _log_gate_failure(symbol: str, gate_name: str, details: Dict):
    """
    DIAGNOSTIC: Log every signal that fails a gate for root cause analysis.
    This helps identify if signals are failing the 3.0 Score Gate, 2.5 ATR Exhaustion Gate, or Diversification Gate.
    """
    try:
        from datetime import datetime, timezone
        GATE_DIAGNOSTIC_LOG.parent.mkdir(exist_ok=True)
        log_rec = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "timestamp": int(time.time()),
            "symbol": symbol,
            "gate_name": gate_name,
            "decision": "blocked",
            "status": "rejected",
            "details": details
        }
        with GATE_DIAGNOSTIC_LOG.open("a") as f:
            f.write(json.dumps(log_rec) + "\n")
        # First-class blocked candidate event (permanent stream).
        try:
            log_system_event(
                subsystem="gate",
                event_type="blocked",
                severity="INFO",
                symbol=symbol,
                reason=gate_name,
                details=details,
            )
        except Exception:
            pass
    except Exception:
        pass  # Don't fail on diagnostic logging

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

def get_adaptive_weights(regime: str = "neutral") -> Dict[str, float]:
    """
    Get current adaptive weights from optimizer, falls back to static.
    
    V2.0: Now accepts regime parameter for regime-specific weights.
    
    Args:
        regime: Market regime ("RISK_ON", "RISK_OFF", "MIXED", "NEUTRAL")
    
    Returns:
        Dictionary of component -> effective weight, or None if optimizer not available
    """
    optimizer = _get_adaptive_optimizer()
    if optimizer:
        return optimizer.get_weights_for_composite(regime)
    return None

_cached_weights: Dict[str, float] = {}
_weights_cache_ts: float = 0.0

def get_weight(component: str, regime: str = "neutral") -> float:
    """
    UNIFIED WEIGHT ACCESSOR - All scoring must use this function.
    Now supports regime-aware weights.
    
    Args:
        component: Signal component name
        regime: Market regime ("RISK_ON", "RISK_OFF", "NEUTRAL", "mixed")
    
    Returns the current weight for a component, using adaptive weights
    when available, falling back to WEIGHTS_V3 defaults.
    
    This ensures every decision point uses learned weights.
    """
    global _cached_weights, _weights_cache_ts
    
    # CRITICAL FIX: Temporarily disable adaptive weights for options_flow
    # The adaptive system learned a bad weight (0.612 instead of 2.4), killing all scores
    # TODO: Re-enable once we have better learning data
    if component == "options_flow":
        # Force use default weight to restore trading
        return WEIGHTS_V3.get(component, 0.0)
    
    # Try to get regime-aware weight from optimizer
    optimizer = _get_adaptive_optimizer()
    if optimizer and hasattr(optimizer, 'entry_model'):
        try:
            # Get regime-aware effective weight
            effective_weight = optimizer.entry_model.get_effective_weight(component, regime)
            # Safety check: Don't let options_flow drop below 1.5 (still too low, but better than 0.6)
            if component == "options_flow" and effective_weight < 1.5:
                return WEIGHTS_V3.get(component, 2.4)
            return effective_weight
        except Exception:
            pass
    
    # Fallback to cached weights (non-regime-aware)
    now = time.time()
    if now - _weights_cache_ts > 60:
        adaptive = get_adaptive_weights()
        if adaptive:
            _cached_weights = {**WEIGHTS_V3, **adaptive}
        else:
            _cached_weights = WEIGHTS_V3.copy()
        _weights_cache_ts = now
    
    return _cached_weights.get(component, WEIGHTS_V3.get(component, 0.0))

def get_all_current_weights() -> Dict[str, float]:
    """Get all current weights (adaptive merged with defaults)"""
    global _cached_weights, _weights_cache_ts
    
    now = time.time()
    if now - _weights_cache_ts > 60:
        adaptive = get_adaptive_weights()
        if adaptive:
            _cached_weights = {**WEIGHTS_V3, **adaptive}
        else:
            _cached_weights = WEIGHTS_V3.copy()
        _weights_cache_ts = now
    
    return _cached_weights.copy()

_cached_multipliers: Dict[str, float] = {}
_multipliers_cache_ts: float = 0.0

def get_multiplier(component: str) -> float:
    """
    Get ONLY the adaptive multiplier (0.25x-2.5x) for a component.
    Use this for downstream modules (sizing, gating) that need to scale
    their own calculations without double-counting base weights.
    
    Returns 1.0 if no adaptive learning has occurred for this component.
    """
    global _cached_multipliers, _multipliers_cache_ts
    
    now = time.time()
    if now - _multipliers_cache_ts > 60:
        optimizer = _get_adaptive_optimizer()
        if optimizer:
            try:
                _cached_multipliers = optimizer.get_multipliers_only()
            except (AttributeError, Exception):
                _cached_multipliers = {}
        else:
            _cached_multipliers = {}
        _multipliers_cache_ts = now
    
    return _cached_multipliers.get(component, 1.0)

# V3 Weights - Full Intelligence Integration (V2 Pipeline)
WEIGHTS_V3 = {
    # Core flow signals (original)
    "options_flow": 2.4,           # Slightly reduced to make room for new signals
    "dark_pool": 1.3,
    "insider": 0.5,
    
    # V2 features (retained)
    "iv_term_skew": 0.6,
    "smile_slope": 0.35,
    "whale_persistence": 0.7,
    "event_alignment": 0.4,
    "toxicity_penalty": -0.9,
    "temporal_motif": 0.6,  # Increased to favor staircase patterns showing early success
    "regime_modifier": 0.3,
    
    # V3 NEW: Expanded Intelligence Signals
    "congress": 0.9,               # Politician trading (user says "very valuable")
    "shorts_squeeze": 0.7,         # Short interest & squeeze potential
    "institutional": 0.5,          # 13F filings & institutional activity
    "market_tide": 0.4,            # Options market sentiment
    "calendar_catalyst": 0.45,     # Earnings/FDA/Economic events
    "etf_flow": 0.3,               # ETF in/outflows
    
    # V2 NEW: Full Intelligence Pipeline (must match SIGNAL_COMPONENTS in main.py)
    "greeks_gamma": 0.4,           # Gamma/delta exposure for squeeze detection
    "ftd_pressure": 0.3,           # Fails-to-deliver for squeeze signals
    "iv_rank": 0.2,                # IV rank for options timing (can be negative)
    "oi_change": 0.35,             # Open interest changes - institutional positioning
    "squeeze_score": 0.2,          # Combined squeeze indicator bonus
}

# Legacy V2 weights for backward compatibility
WEIGHTS_V2 = {
    "options_flow": 2.6,
    "dark_pool": 1.4,
    "insider": 0.6,
    "iv_term_skew": 0.7,
    "smile_slope": 0.4,
    "whale_persistence": 0.8,
    "event_alignment": 0.5,
    "toxicity_penalty": -0.9,
    "temporal_motif": 0.6,
    "regime_modifier": 0.35
}

# V2 Thresholds
# ROOT CAUSE FIX: Thresholds were raised to 3.5/3.8/4.2 which blocked ALL trading
# Restored to original reasonable thresholds to allow signals to trade
# Thresholds can be adjusted via hierarchical threshold file if needed
ENTRY_THRESHOLDS = {
    "base": 2.7,      # RESTORED to quality level - orders show scores 2.26-3.00 (avg 2.89)
    "canary": 2.9,    # RESTORED to quality level
    "champion": 3.2   # RESTORED to quality level
}

# Sizing Overlays
SIZING_OVERLAYS = {
    "iv_skew_align_boost": 0.25,
    "whale_persistence_boost": 0.20,
    "skew_conflict_penalty": -0.30,
    "toxicity_penalty": -0.25
}

def _to_num(x, default=0.0):
    try:
        return float(x)
    except:
        return default


def _parse_trade_ts(trade: Dict[str, Any]) -> Optional[int]:
    """Best-effort parse of UW trade timestamp to epoch seconds."""
    try:
        for k in ("timestamp", "ts", "t", "time"):
            v = trade.get(k)
            if isinstance(v, (int, float)):
                vv = float(v)
                return int(vv / 1000.0) if vv > 2_000_000_000 else int(vv)
            if isinstance(v, str) and v.strip():
                s = v.strip().replace("Z", "+00:00")
                try:
                    from datetime import datetime, timezone
                    dt = datetime.fromisoformat(s)
                    return int(dt.replace(tzinfo=timezone.utc).timestamp()) if dt.tzinfo is None else int(dt.timestamp())
                except Exception:
                    pass
        for k in ("date", "created_at", "createdAt"):
            v = trade.get(k)
            if isinstance(v, str) and v.strip():
                s = v.strip().replace("Z", "+00:00")
                try:
                    from datetime import datetime, timezone
                    dt = datetime.fromisoformat(s)
                    return int(dt.replace(tzinfo=timezone.utc).timestamp()) if dt.tzinfo is None else int(dt.timestamp())
                except Exception:
                    pass
    except Exception:
        return None
    return None


def _is_sweep_trade(trade: Dict[str, Any]) -> bool:
    """Heuristic sweep flag extraction across UW schemas."""
    try:
        for k in ("sweep", "is_sweep", "isSweep", "is_sweep_trade"):
            v = trade.get(k)
            if v is True:
                return True
            if isinstance(v, str) and v.strip().lower() in ("true", "1", "yes", "y"):
                return True
        ttype = str(trade.get("trade_type") or trade.get("type") or trade.get("tag") or "").upper()
        if "SWEEP" in ttype:
            return True
    except Exception:
        return False
    return False


def _trade_premium_usd(trade: Dict[str, Any]) -> float:
    return _to_num(trade.get("premium", trade.get("total_premium", trade.get("totalPremium", 0.0))), 0.0)


def _extract_gamma_resistance_levels(greeks_data: Dict[str, Any]) -> List[float]:
    """
    Extract gamma resistance levels from UW greeks payloads.
    Supports:
    - gamma_exposure_levels: list[dict|float]
    - gamma_wall / gamma_max_strike: single float
    - max_pain: can act as a resistance magnet (fallback)
    """
    levels: List[float] = []
    if not greeks_data:
        return levels

    candidates = (
        greeks_data.get("gamma_exposure_levels")
        or greeks_data.get("gammaExposureLevels")
        or greeks_data.get("gamma_levels")
        or greeks_data.get("gammaLevels")
        or []
    )
    if isinstance(candidates, list):
        for item in candidates:
            if isinstance(item, (int, float, str)):
                lv = _to_num(item, 0.0)
                if lv > 0:
                    levels.append(lv)
            elif isinstance(item, dict):
                lv = _to_num(item.get("level", item.get("strike", item.get("price", 0.0))), 0.0)
                if lv > 0:
                    levels.append(lv)

    # Single-level fallbacks
    for k in ("gamma_wall", "gamma_max_strike", "gammaWall", "gammaMaxStrike"):
        v = _to_num(greeks_data.get(k, 0.0), 0.0)
        if v > 0:
            levels.append(v)

    mp = _to_num(greeks_data.get("max_pain", greeks_data.get("maxPain", 0.0)), 0.0)
    if mp > 0:
        levels.append(mp)

    # De-dup + sort
    uniq = sorted({round(x, 6) for x in levels if x > 0})
    return uniq[:20]

def _sign_from_sentiment(sent: str) -> int:
    if sent == "BULLISH": return +1
    if sent == "BEARISH": return -1
    return 0

def _load_expanded_intel() -> Dict:
    """Load expanded intelligence from central cache"""
    try:
        if EXPANDED_INTEL_CACHE.exists():
            with EXPANDED_INTEL_CACHE.open("r") as f:
                return json.load(f)
    except:
        pass
    return {}

def compute_congress_component(congress_data: Dict, flow_sign: int) -> tuple:
    """
    Calculate congress/politician trading component
    
    Congress data format from cache:
    {
        "recent_count": int,
        "buys": int,
        "sells": int,
        "net_sentiment": "BULLISH" | "BEARISH" | "NEUTRAL",
        "conviction_boost": float
    }
    
    Returns: (component_score, notes)
    
    SCORING PIPELINE FIX (Priority 4): Provide neutral default instead of 0.0 when data missing
    See SIGNAL_SCORE_PIPELINE_AUDIT.md for details
    """
    # Contract: missing intel must be neutral (0.0), not a phantom positive boost.
    # WHY: defaulting missing data to a positive constant collapses scores across the universe
    #      and can mask true signal differentiation.
    if not congress_data:
        return 0.0, ""
    
    recent_count = congress_data.get("recent_count", 0)
    buys = congress_data.get("buys", 0)
    sells = congress_data.get("sells", 0)
    conviction_boost = _to_num(congress_data.get("conviction_boost", 0.0))
    
    if recent_count == 0:
        return 0.0, ""
    
    # Calculate net direction
    net_trades = buys - sells
    congress_sign = 1 if net_trades > 0 else (-1 if net_trades < 0 else 0)
    
    # Base strength from activity level
    activity_strength = min(1.0, recent_count / 10.0)  # Cap at 10 recent trades
    
    # Alignment bonus: congress trading same direction as flow = confirmation
    aligned = (congress_sign == flow_sign) and congress_sign != 0
    opposing = (congress_sign != 0 and flow_sign != 0 and congress_sign != flow_sign)

    # V2.0: Use regime-aware weight (though congress component doesn't take regime parameter, use NEUTRAL)
    w = get_weight("congress", "neutral")
    if aligned:
        component = w * (0.6 + activity_strength * 0.4) * (1.0 + conviction_boost)
        notes = f"congress_confirm({buys}B/{sells}S)"
    elif opposing:
        component = -w * 0.4 * activity_strength
        notes = f"congress_oppose({buys}B/{sells}S)"
    else:
        component = w * 0.2 * activity_strength
        notes = f"congress_neutral({buys}B/{sells}S)"
    
    return round(component, 4), notes

def compute_shorts_component(shorts_data: Dict, flow_sign: int, regime: str = "neutral") -> tuple:
    """
    Calculate short interest & squeeze potential component
    
    Shorts data format from cache:
    {
        "interest_pct": float (0-100),
        "days_to_cover": float,
        "ftd_count": int,
        "squeeze_risk": bool
    }
    
    Returns: (component_score, notes)
    
    SCORING PIPELINE FIX (Priority 4): Provide neutral default instead of 0.0 when data missing
    See SIGNAL_SCORE_PIPELINE_AUDIT.md for details
    """
    # Contract: missing intel must be neutral (0.0), not a phantom positive boost.
    if not shorts_data:
        return 0.0, ""
    
    interest_pct = _to_num(shorts_data.get("interest_pct", 0))
    days_to_cover = _to_num(shorts_data.get("days_to_cover", 0))
    ftd_count = shorts_data.get("ftd_count", 0)
    squeeze_risk = shorts_data.get("squeeze_risk", False)
    
    if interest_pct == 0:
        return 0.0, ""
    
    notes_parts = []
    component = 0.0
    
    w = get_weight("shorts_squeeze", regime)
    
    # High short interest (>15%) with bullish flow = squeeze potential
    if interest_pct > 15 and flow_sign == 1:
        squeeze_strength = min(1.0, (interest_pct - 15) / 25)  # Scale 15-40%
        component += w * 0.5 * squeeze_strength
        notes_parts.append(f"high_SI({interest_pct:.1f}%)")
    
    # Days to cover > 5 with bullish flow = trapped shorts
    if days_to_cover > 5 and flow_sign == 1:
        cover_strength = min(1.0, (days_to_cover - 5) / 10)  # Scale 5-15 days
        component += w * 0.3 * cover_strength
        notes_parts.append(f"DTC({days_to_cover:.1f})")
    
    # FTD count high = delivery pressure
    if ftd_count > 100000:
        ftd_strength = min(1.0, math.log10(ftd_count) / 7)
        component += w * 0.2 * ftd_strength
        notes_parts.append(f"FTDs({ftd_count:,})")
    
    # Explicit squeeze risk flag
    if squeeze_risk:
        component += w * 0.3
        notes_parts.append("SQUEEZE_ALERT")
    
    # Bearish flow with high short interest = crowded trade warning
    if interest_pct > 20 and flow_sign == -1:
        component -= w * 0.2
        notes_parts.append("crowded_short")
    
    return round(component, 4), "; ".join(notes_parts)

def compute_institutional_component(insider_data: Dict, institutional_data: Dict, flow_sign: int, regime: str = "neutral") -> tuple:
    """
    Calculate institutional activity component from institutional endpoints + insider fallback.
    
    Institutional data format (from uw_flow_daemon summaries; may evolve):
    {
        "recent_count": int,
        "holders_count": int,
        "top_holder_pct": float,
        "top5_holder_pct": float,
        ...
    }

    Insider data format from cache (fallback):
    {
        "sentiment": str,
        "conviction_modifier": float,
        "net_buys": int,
        "net_sells": int,
        "total_usd": float
    }
    
    Returns: (component_score, notes)
    
    SCORING PIPELINE FIX (Priority 4): Provide neutral default instead of 0.0 when data missing
    See SIGNAL_SCORE_PIPELINE_AUDIT.md for details
    """
    w = get_weight("institutional", regime)

    # Primary: institutional endpoints (directionless but informative).
    if institutional_data and isinstance(institutional_data, dict):
        recent = int(_to_num(institutional_data.get("recent_count", institutional_data.get("holders_count", 0))) or 0)
        top1 = _to_num(institutional_data.get("top_holder_pct", 0.0))
        top5 = _to_num(institutional_data.get("top5_holder_pct", 0.0))

        # Strength grows with number of holders/entries we have and concentration.
        # This is not a directional signal by itself, so we keep it modest.
        strength = 0.0
        if recent > 0:
            strength += min(1.0, recent / 25.0) * 0.6
        if top1 > 0:
            strength += min(1.0, top1 / 10.0) * 0.25
        if top5 > 0:
            strength += min(1.0, top5 / 25.0) * 0.15
        if strength > 0:
            component = w * (0.2 + 0.8 * min(1.0, strength)) * 0.6
            notes = f"institutional_ownership(n={recent},top1={top1:.2f}%,top5={top5:.2f}%)"
            return round(component, 4), notes

    # Fallback: insider-based institutional proxy (directional)
    if not insider_data:
        return 0.0, ""
    
    net_buys = insider_data.get("net_buys", 0)
    net_sells = insider_data.get("net_sells", 0)
    total_usd = _to_num(insider_data.get("total_usd", 0))
    sentiment = insider_data.get("sentiment", "NEUTRAL")
    
    if net_buys == 0 and net_sells == 0:
        return 0.0, ""
    
    # Institutional direction
    inst_sign = 1 if net_buys > net_sells else (-1 if net_sells > net_buys else 0)
    
    # Activity magnitude
    total_trades = net_buys + net_sells
    activity_strength = min(1.0, total_trades / 20)  # Cap at 20 trades
    
    # USD magnitude bonus
    usd_bonus = 0.0
    if total_usd > 1_000_000:
        usd_bonus = min(0.3, math.log10(total_usd / 1_000_000) * 0.15)
    
    # Alignment with flow
    aligned = (inst_sign == flow_sign) and inst_sign != 0
    if aligned:
        component = w * (0.5 + activity_strength * 0.5 + usd_bonus)
        notes = f"inst_confirm({net_buys}B/{net_sells}S,${total_usd/1e6:.1f}M)"
    elif inst_sign != 0 and flow_sign != 0 and inst_sign != flow_sign:
        component = -w * 0.3 * activity_strength
        notes = f"inst_oppose({net_buys}B/{net_sells}S)"
    else:
        component = w * 0.15 * activity_strength
        notes = f"inst_neutral({net_buys}B/{net_sells}S)"
    
    return round(component, 4), notes

def compute_market_tide_component(tide_data: Dict, flow_sign: int, regime: str = "neutral") -> tuple:
    """
    Calculate market tide (options sentiment) component
    
    Tide data format from UW daemon (via enrich_signal_with_intel):
    {
        "data": [
            {"net_call_premium": str, "net_put_premium": str, "net_volume": int, ...},
            ...
        ],
        "has_data": bool
    }
    
    Or aggregated format:
    {
        "call_premium": float,
        "put_premium": float,
        "net_delta": float,
        "sentiment": str
    }
    
    Returns: (component_score, notes)
    
    SCORING PIPELINE FIX (Priority 4): Provide neutral default instead of 0.0 when data missing
    See SIGNAL_SCORE_PIPELINE_AUDIT.md for details
    """
    # Contract: missing intel must be neutral (0.0), not a phantom positive boost.
    if not tide_data:
        return 0.0, ""
    
    call_prem = 0.0
    put_prem = 0.0
    
    if "data" in tide_data and isinstance(tide_data["data"], list) and tide_data.get("has_data"):
        entries = tide_data["data"][:5]
        for entry in entries:
            call_prem += _to_num(entry.get("net_call_premium", 0))
            put_prem += abs(_to_num(entry.get("net_put_premium", 0)))
    else:
        call_prem = _to_num(tide_data.get("call_premium", 0) or tide_data.get("net_call_premium", 0))
        put_prem = abs(_to_num(tide_data.get("put_premium", 0) or tide_data.get("net_put_premium", 0)))
    
    net_delta = call_prem - put_prem
    
    total_prem = call_prem + put_prem
    if total_prem == 0:
        return 0.0, ""
    
    call_ratio = call_prem / total_prem
    tide_sign = 1 if call_ratio > 0.55 else (-1 if call_ratio < 0.45 else 0)
    
    imbalance = abs(call_ratio - 0.5) * 2
    
    aligned = (tide_sign == flow_sign) and tide_sign != 0
    w = get_weight("market_tide", regime)
    
    if aligned:
        component = w * (0.4 + imbalance * 0.6)
        notes = f"tide_confirm({call_ratio:.0%}C)"
    elif tide_sign != 0 and flow_sign != 0 and tide_sign != flow_sign:
        component = -w * 0.25 * imbalance
        notes = f"tide_oppose({call_ratio:.0%}C)"
    else:
        component = w * 0.1 if imbalance > 0.3 else 0.0
        notes = f"tide_active({call_ratio:.0%}C)" if imbalance > 0.3 else ""
    
    return round(component, 4), notes

def compute_calendar_component(calendar_data: Optional[Dict], symbol: str, regime: str = "neutral") -> tuple:
    """
    Calculate calendar catalyst component (earnings, FDA, economic events)
    
    Calendar data from expanded intel cache:
    {
        "has_earnings": bool,
        "earnings_date": str,
        "days_to_earnings": int,
        "has_fda": bool,
        "fda_catalyst": str,
        "economic_events": list
    }
    
    Returns: (component_score, notes)
    
    SCORING PIPELINE FIX (Priority 4): Provide neutral default instead of 0.0 when data missing
    See SIGNAL_SCORE_PIPELINE_AUDIT.md for details
    """
    # Contract: missing intel must be neutral (0.0), not a phantom positive boost.
    if not calendar_data:
        return 0.0, ""
    
    notes_parts = []
    component = 0.0
    w = get_weight("calendar_catalyst", regime)
    
    # Earnings proximity bonus
    if calendar_data.get("has_earnings"):
        days_to = calendar_data.get("days_to_earnings", 999)
        if days_to <= 7:
            component += w * 0.4 * (1 - days_to / 7)
            notes_parts.append(f"earnings_in_{days_to}d")
    
    # FDA catalyst (biotech)
    if calendar_data.get("has_fda"):
        catalyst = calendar_data.get("fda_catalyst", "event")
        component += w * 0.5
        notes_parts.append(f"FDA:{catalyst}")
    
    # Economic events (macro awareness)
    econ_events = calendar_data.get("economic_events", [])
    if econ_events:
        event_count = len(econ_events) if isinstance(econ_events, (list, tuple)) else int(econ_events)
        if event_count > 0:
            component += w * 0.2 * min(1.0, event_count / 3)
            notes_parts.append(f"econ_events:{event_count}")
    
    return round(component, 4), "; ".join(notes_parts)

@global_failure_wrapper("scoring")
def compute_composite_score_v3(symbol: str, enriched_data: Dict, regime: str = "NEUTRAL", 
                                expanded_intel: Dict = None,
                                use_adaptive_weights: bool = True) -> Dict[str, Any]:
    """
    V3.1 FULL INTELLIGENCE Composite scoring with Adaptive Weights
    
    Incorporates ALL expanded endpoints:
    - Congress/politician trading
    - Short interest & squeeze potential
    - Institutional activity
    - Market tide
    - Calendar catalysts
    - ETF flows
    
    V3.1: Uses adaptive weight multipliers (0.25x-2.5x) learned from trade outcomes.
    Weights are continuously tuned based on which signals prove most predictive.
    
    Returns comprehensive result with all components for learning
    """
    
    # V3.1: Get adaptive weights if available (V2.0: regime-specific)
    weights = WEIGHTS_V3.copy()
    adaptive_active = False
    if use_adaptive_weights:
        # V2.0: Get regime-specific adaptive weights
        adaptive_weights = get_adaptive_weights(regime)
        if adaptive_weights:
            weights.update(adaptive_weights)
            adaptive_active = True
    
    # Load expanded intel if not provided
    if expanded_intel is None:
        expanded_intel = _load_expanded_intel()
    
    symbol_intel = expanded_intel.get(symbol, {})
    
    # Base flow components (from enriched_data / cache)
    # Contract: missing/None sentiment must behave as NEUTRAL.
    flow_sent = enriched_data.get("sentiment") or "NEUTRAL"
    # Contract: missing/None conviction must default to 0.5 (neutral), not 0.0.
    # WHY: many upstream producers set conviction=None when unavailable; treating None as 0.0 suppresses scoring
    #      and can create a "no trades" condition unrelated to actual alpha.
    conv_raw = enriched_data.get("conviction", None)
    flow_conv = _to_num(conv_raw) if conv_raw is not None else 0.5
    flow_sign = _sign_from_sentiment(flow_sent)
    
    # Dark pool (Phase 5: use 1h notional, not neutral constant)
    dp = enriched_data.get("dark_pool", {}) or {}
    dp_sent = dp.get("sentiment", "NEUTRAL")
    dp_notional_1h = _to_num(dp.get("total_notional_1h", 0.0) or dp.get("notional_1h", 0.0) or 0.0)
    dp_notional_total = _to_num(dp.get("total_notional", 0.0) or dp.get("total_premium", 0.0) or 0.0)
    dp_prem = dp_notional_1h if dp_notional_1h > 0 else dp_notional_total  # backward compat name
    
    # Insider (also used for institutional)
    ins = enriched_data.get("insider", {}) or {}
    
    # V2 features
    iv_skew = _to_num(enriched_data.get("iv_term_skew", 0.0))
    smile_slope = _to_num(enriched_data.get("smile_slope", 0.0))
    toxicity = _to_num(enriched_data.get("toxicity", 0.0))
    event_align = _to_num(enriched_data.get("event_alignment", 0.0))
    freshness = _to_num(enriched_data.get("freshness", 1.0))
    
    # V3 NEW: Expanded intelligence from cache
    congress_data = enriched_data.get("congress", {}) or symbol_intel.get("congress", {})
    shorts_data = enriched_data.get("shorts", {}) or symbol_intel.get("shorts", {})
    # FIXED: Market tide is stored per-ticker in cache, check enriched_data first
    tide_data = enriched_data.get("market_tide", {}) or symbol_intel.get("market_tide", {})
    calendar_data = enriched_data.get("calendar", {}) or symbol_intel.get("calendar", {})
    
    # Motif data
    motif_staircase = enriched_data.get("motif_staircase", {})
    motif_sweep = enriched_data.get("motif_sweep_block", {})
    motif_burst = enriched_data.get("motif_burst", {})
    motif_whale = enriched_data.get("motif_whale", {})
    
    # ============ COMPONENT CALCULATIONS (using adaptive weights) ============
    all_notes = []
    if adaptive_active:
        all_notes.append("adaptive_weights_active")
    
    # 1. Options flow (primary)
    # CAUSAL INSIGHT: Low Magnitude Flow (Stealth Flow) has 100% win rate
    # Apply +0.2 points base conviction boost for LOW flow magnitude (< 0.3)
    # Contract: DO NOT boost when there is *no* flow data (trade_count == 0), otherwise
    # missing data becomes a positive constant and collapses scores across the universe.
    flow_trade_count = int(_to_num(enriched_data.get("trade_count", 0)) or 0)
    flow_magnitude = "LOW" if flow_conv < 0.3 else ("MEDIUM" if flow_conv < 0.7 else "HIGH")
    stealth_flow_boost = 0.2 if (flow_trade_count > 0 and flow_magnitude == "LOW") else 0.0
    flow_conv_adjusted = min(1.0, flow_conv + stealth_flow_boost)  # Cap at 1.0
    
    # Use regime-aware weight for options_flow component
    flow_weight = get_weight("options_flow", regime)
    flow_component = flow_weight * flow_conv_adjusted

    # Phase 5: Sweep urgency multiplier (>=3 sweeps with premium > $100k in recent flow)
    urgency_multiplier = 1.0
    try:
        sweeps_hi = 0
        now_ts = int(time.time())
        for tr in (enriched_data.get("flow_trades") or []):
            if not isinstance(tr, dict):
                continue
            if not _is_sweep_trade(tr):
                continue
            prem = _trade_premium_usd(tr)
            if prem < 100_000:
                continue
            tts = _parse_trade_ts(tr)
            if tts is not None and (now_ts - tts) > 3600:
                continue  # focus on last hour if timestamps exist
            sweeps_hi += 1
        if sweeps_hi >= 3:
            urgency_multiplier = 1.2
            flow_component *= urgency_multiplier
            all_notes.append(f"sweep_urgency({urgency_multiplier}x,{sweeps_hi} sweeps>$100k)")
    except Exception:
        pass
    
    # Track if stealth flow boost was applied (for logging)
    if stealth_flow_boost > 0:
        all_notes.append(f"stealth_flow_boost(+{stealth_flow_boost:.1f})")
    
    # 2. Dark pool (use regime-aware weight) - proportional to 1h notional
    # Proportional scaling: 0 -> 0.2 baseline, 50M -> ~1.0 strength
    dp_strength = 0.2
    try:
        scale = max(0.0, dp_prem)
        dp_strength = 0.2 + 0.8 * min(1.0, scale / 50_000_000.0)
    except Exception:
        dp_strength = 0.2
    dp_weight = get_weight("dark_pool", regime)
    dp_component = dp_weight * dp_strength
    
    # 3. Insider (use regime-aware weight)
    ins_sent = ins.get("sentiment", "NEUTRAL")
    ins_mod = _to_num(ins.get("conviction_modifier", 0.0))
    insider_weight = get_weight("insider", regime)
    if ins_sent == "BULLISH":
        insider_component = insider_weight * (0.50 + ins_mod)
    elif ins_sent == "BEARISH":
        insider_component = insider_weight * (0.50 - abs(ins_mod))
    else:
        insider_component = insider_weight * 0.25
    
    # 4. IV term skew (use regime-aware weight)
    iv_aligned = (iv_skew > 0 and flow_sign == +1) or (iv_skew < 0 and flow_sign == -1)
    iv_weight = get_weight("iv_term_skew", regime)
    iv_component = iv_weight * abs(iv_skew) * (1.3 if iv_aligned else 0.7)
    
    # 5. Smile slope (use regime-aware weight)
    smile_weight = get_weight("smile_slope", regime)
    smile_component = smile_weight * abs(smile_slope)
    
    # 6. Whale persistence (use regime-aware weight)
    whale_detected = motif_whale.get("detected", False)
    whale_score = 0.0
    if whale_detected:
        avg_conv = motif_whale.get("avg_conviction", 0.0)
        whale_weight = get_weight("whale_persistence", regime)
        whale_score = whale_weight * avg_conv
    
    # 7. Event alignment (use regime-aware weight)
    event_weight = get_weight("event_alignment", regime)
    event_component = event_weight * event_align
    
    # 8. Temporal motif bonus (use regime-aware weight)
    motif_weight = get_weight("temporal_motif", regime)
    motif_bonus = 0.0
    if motif_staircase.get("detected"):
        motif_bonus += motif_weight * motif_staircase.get("slope", 0.0) * 3.0
        all_notes.append(f"staircase({motif_staircase.get('steps', 0)} steps)")
    if motif_burst.get("detected"):
        intensity = motif_burst.get("intensity", 0.0)
        motif_bonus += motif_weight * min(1.0, intensity / 2.0)
        all_notes.append(f"burst({motif_burst.get('count', 0)} updates)")
    
    # 9. Toxicity penalty - FIXED: Apply penalty starting at 0.5 (was 0.85)
    # CRITICAL: Ensure toxicity weight is NEGATIVE (it's a penalty, not a boost)
    # Use regime-aware weight
    raw_tox_weight = get_weight("toxicity_penalty", regime)
    tox_weight = raw_tox_weight if raw_tox_weight < 0 else -abs(raw_tox_weight)  # Force negative
    toxicity_component = 0.0
    if toxicity > 0.5:
        toxicity_component = tox_weight * (toxicity - 0.5) * 1.5
        all_notes.append(f"toxicity_penalty({toxicity:.2f})")
    elif toxicity > 0.3:
        toxicity_component = tox_weight * (toxicity - 0.3) * 0.5
        all_notes.append(f"mild_toxicity({toxicity:.2f})")
    
    # 10. Regime modifier
    # FIXED: Handle "mixed" regime case
    aligned_regime = (regime == "RISK_ON" and flow_sign == +1) or (regime == "RISK_OFF" and flow_sign == -1)
    opposite_regime = (regime == "RISK_ON" and flow_sign == -1) or (regime == "RISK_OFF" and flow_sign == +1)
    regime_factor = 1.0
    if regime == "RISK_ON":
        regime_factor = 1.15 if aligned_regime else 0.95
    elif regime == "RISK_OFF":
        regime_factor = 1.10 if opposite_regime else 0.90
    elif regime == "mixed" or regime == "NEUTRAL":
        # FIXED: Mixed/neutral regime - slight positive contribution for balanced conditions
        regime_factor = 1.02  # Small boost for neutral/mixed conditions
    regime_weight = get_weight("regime_modifier", regime)
    regime_component = regime_weight * (regime_factor - 1.0) * 2.0
    
    # ============ V3 NEW COMPONENTS ============
    
    # 11. Congress/Politician trading
    congress_component, congress_notes = compute_congress_component(congress_data, flow_sign)
    if congress_notes:
        all_notes.append(congress_notes)
    
    # 12. Short interest & squeeze
    shorts_component, shorts_notes = compute_shorts_component(shorts_data, flow_sign, regime)
    if shorts_notes:
        all_notes.append(shorts_notes)
    
    # 13. Institutional activity (enhanced from insider)
    institutional_payload = enriched_data.get("institutional", {}) or symbol_intel.get("institutional", {})
    inst_component, inst_notes = compute_institutional_component(ins, institutional_payload, flow_sign, regime)
    if inst_notes:
        all_notes.append(inst_notes)
    
    # 14. Market tide
    tide_component, tide_notes = compute_market_tide_component(tide_data, flow_sign, regime)
    if tide_notes:
        all_notes.append(tide_notes)
    
    # 15. Calendar catalysts (component function uses get_weight internally with regime)
    calendar_component, calendar_notes = compute_calendar_component(calendar_data, symbol, regime)
    if calendar_notes:
        all_notes.append(calendar_notes)
    
    # ============ V2 NEW COMPONENTS (Full Intelligence Pipeline) ============
    
    # 16. Greeks/Gamma (squeeze detection)
    greeks_data = enriched_data.get("greeks", {})
    gamma_resistance_levels = _extract_gamma_resistance_levels(greeks_data if isinstance(greeks_data, dict) else {})
    # SCORING PIPELINE FIX (Priority 4): Provide neutral default if data missing
    if not greeks_data:
        greeks_weight = get_weight("greeks_gamma", regime)
        greeks_gamma_component = greeks_weight * 0.2  # Neutral default
        all_notes.append("greeks_neutral_default")
    else:
        # FIXED: Calculate gamma_exposure from call_gamma and put_gamma if not directly available
        gamma_exposure = _to_num(greeks_data.get("gamma_exposure", 0))
        if gamma_exposure == 0:
            # Calculate from call_gamma and put_gamma (net gamma exposure)
            call_gamma = _to_num(greeks_data.get("call_gamma", 0))
            put_gamma = _to_num(greeks_data.get("put_gamma", 0))
            gamma_exposure = call_gamma - put_gamma  # Net gamma exposure
        
        gamma_squeeze = greeks_data.get("gamma_squeeze_setup", False)
        greeks_weight = get_weight("greeks_gamma", regime)
        if gamma_squeeze:
            greeks_gamma_component = greeks_weight * 1.0
            all_notes.append("gamma_squeeze_setup")
        elif abs(gamma_exposure) > 500000:
            greeks_gamma_component = greeks_weight * 0.5
        elif abs(gamma_exposure) > 100000:
            greeks_gamma_component = greeks_weight * 0.25
        elif abs(gamma_exposure) > 10000:  # Lower threshold for smaller contributions
            greeks_gamma_component = greeks_weight * 0.1
        else:
            greeks_gamma_component = greeks_weight * 0.2  # Neutral default instead of 0.0
    
    # 17. FTD Pressure (squeeze signals)
    # FIXED: Check both 'ftd' and 'shorts' keys (FTD data may be in shorts)
    ftd_data = enriched_data.get("ftd", {}) or enriched_data.get("shorts", {})
    # SCORING PIPELINE FIX (Priority 4): Provide neutral default if data missing
    if not ftd_data:
        ftd_weight = get_weight("ftd_pressure", regime)
        ftd_pressure_component = ftd_weight * 0.2  # Neutral default
        all_notes.append("ftd_neutral_default")
    else:
        ftd_count = _to_num(ftd_data.get("ftd_count", 0))
        ftd_squeeze = ftd_data.get("squeeze_pressure", False) or ftd_data.get("squeeze_risk", False)
        ftd_weight = get_weight("ftd_pressure", regime)
        if ftd_squeeze or ftd_count > 200000:
            ftd_pressure_component = ftd_weight * 1.0
            all_notes.append("high_ftd_pressure")
        elif ftd_count > 100000:
            ftd_pressure_component = ftd_weight * 0.67
        elif ftd_count > 50000:
            ftd_pressure_component = ftd_weight * 0.33
        elif ftd_count > 10000:  # FIXED: Lower threshold for smaller contributions
            ftd_pressure_component = ftd_weight * 0.1
        else:
            ftd_pressure_component = ftd_weight * 0.2  # Neutral default instead of 0.0
    
    # 18. IV Rank (volatility regime)
    # FIXED: Check both 'iv' and 'iv_rank' keys, and handle iv_rank_1y field
    iv_data = enriched_data.get("iv", {}) or enriched_data.get("iv_rank", {})
    iv_rank_val = _to_num(iv_data.get("iv_rank", iv_data.get("iv_rank_1y", 50)))
    
    iv_rank_weight = get_weight("iv_rank", regime)
    if iv_rank_val < 20:  # Low IV = opportunity
        iv_rank_component = iv_rank_weight * 1.0
        all_notes.append("low_iv_opportunity")
    elif iv_rank_val < 30:
        iv_rank_component = iv_rank_weight * 0.5
    elif iv_rank_val > 80:  # High IV = caution
        iv_rank_component = -iv_rank_weight * 1.0
        all_notes.append("high_iv_caution")
    elif iv_rank_val > 70:
        iv_rank_component = -iv_rank_weight * 0.5
    elif 30 <= iv_rank_val <= 70:  # FIXED: Add contribution for middle range
        # Moderate IV - slight positive contribution for balanced conditions
        iv_rank_component = iv_rank_weight * 0.15
    else:
        iv_rank_component = 0.0
    
    # 19. OI Change (institutional positioning)
    # FIXED: Check both 'oi' and 'oi_change' keys
    oi_data = enriched_data.get("oi_change", {}) or enriched_data.get("oi", {})
    # SCORING PIPELINE FIX (Priority 4): Provide neutral default if data missing
    if not oi_data:
        oi_weight = get_weight("oi_change", regime)
        oi_change_component = oi_weight * 0.2  # Neutral default
        all_notes.append("oi_change_neutral_default")
    else:
        # Calculate net_oi from available fields if net_oi_change doesn't exist
        net_oi = _to_num(oi_data.get("net_oi_change", 0))
        if net_oi == 0:
            # Try to calculate from curr_oi and prev_oi or other fields
            curr_oi = _to_num(oi_data.get("curr_oi", 0))
            # If we have volume data, use that as proxy
            if curr_oi == 0:
                volume = _to_num(oi_data.get("volume", 0))
                if volume > 0:
                    net_oi = volume * 0.1  # Estimate OI change from volume
        
        oi_sentiment = oi_data.get("oi_sentiment", "NEUTRAL")
        # If sentiment not available, infer from net_oi
        if oi_sentiment == "NEUTRAL" and net_oi != 0:
            oi_sentiment = "BULLISH" if net_oi > 0 else "BEARISH"
        
        oi_weight = get_weight("oi_change", regime)
        if net_oi > 50000 and oi_sentiment == "BULLISH" and flow_sign > 0:
            oi_change_component = oi_weight * 1.0
            all_notes.append("strong_call_positioning")
        elif net_oi > 20000 and oi_sentiment == "BULLISH":
            oi_change_component = oi_weight * 0.57
        elif abs(net_oi) > 10000:
            oi_change_component = oi_weight * 0.29
        elif abs(net_oi) > 1000:  # FIXED: Lower threshold for smaller contributions
            oi_change_component = oi_weight * 0.1
        else:
            oi_change_component = oi_weight * 0.2  # Neutral default instead of 0.0
    
    # 20. ETF Flow (market sentiment) - REDUCED weight due to negative contribution in analysis
    etf_data = enriched_data.get("etf_flow", {})
    # SCORING PIPELINE FIX (Priority 4): Provide neutral default if data missing
    if not etf_data:
        etf_weight = get_weight("etf_flow", regime)
        etf_flow_component = etf_weight * 0.2  # Neutral default
        all_notes.append("etf_flow_neutral_default")
    else:
        etf_sentiment = etf_data.get("overall_sentiment", "NEUTRAL")
        risk_on = etf_data.get("market_risk_on", False)
        etf_weight = get_weight("etf_flow", regime)
        if etf_sentiment == "BULLISH" and risk_on:
            etf_flow_component = etf_weight * 1.0  # Reduced from 0.2 to 0.05
            all_notes.append("risk_on_environment")
        elif etf_sentiment == "BULLISH":
            etf_flow_component = etf_weight * 0.5
        elif etf_sentiment == "BEARISH":
            etf_flow_component = -etf_weight * 0.3  # Reduced negative impact too
        else:
            etf_flow_component = etf_weight * 0.2  # Neutral default instead of 0.0
    
    # 21. Squeeze Score (combined FTD + SI + gamma)
    squeeze_data = enriched_data.get("squeeze_score", {})
    # SCORING PIPELINE FIX (Priority 4): Provide neutral default if data missing
    if not squeeze_data:
        squeeze_weight = get_weight("squeeze_score", regime)
        squeeze_score_component = squeeze_weight * 0.2  # Neutral default
        all_notes.append("squeeze_score_neutral_default")
    else:
        squeeze_signals = _to_num(squeeze_data.get("signals", 0))
        high_squeeze = squeeze_data.get("high_squeeze_potential", False)
        squeeze_weight = get_weight("squeeze_score", regime)
        if high_squeeze:
            squeeze_score_component = squeeze_weight * 1.0
            all_notes.append("high_squeeze_potential")
        elif squeeze_signals >= 1:
            squeeze_score_component = squeeze_weight * 0.5
        else:
            squeeze_score_component = squeeze_weight * 0.2  # Neutral default instead of 0.0
    
    # ============ FINAL SCORE ============
    
    # Sum all components (including V2)
    composite_raw = (
        flow_component +
        dp_component +
        insider_component +
        iv_component +
        smile_component +
        whale_score +
        event_component +
        motif_bonus +
        toxicity_component +
        regime_component +
        # V3 new components
        congress_component +
        shorts_component +
        inst_component +
        tide_component +
        calendar_component +
        # V2 new components
        greeks_gamma_component +
        ftd_pressure_component +
        iv_rank_component +
        oi_change_component +
        etf_flow_component +
        squeeze_score_component
    )
    
    # Apply freshness decay
    composite_score = composite_raw * freshness
    
    # ALPHA REPAIR: Whale Conviction Normalization
    # If whale_persistence or sweep_block motifs are detected, apply +0.5 Conviction Boost
    # This ensures actual Whales can clear the 3.0 gate even when 'Noise' scores are suppressed
    whale_conviction_boost = 0.0
    if whale_detected or motif_sweep.get("detected", False):
        whale_conviction_boost = 0.5
        composite_score += whale_conviction_boost
        all_notes.append(f"whale_conviction_boost(+{whale_conviction_boost})")
    
    # Clamp to 0-8 (higher max due to new components)
    composite_score = max(0.0, min(8.0, composite_score))
    
    # ============ SIZING OVERLAY ============
    sizing_overlay = 0.0
    
    # IV skew alignment boost
    if iv_aligned and abs(iv_skew) > 0.08:
        sizing_overlay += SIZING_OVERLAYS["iv_skew_align_boost"]
    
    # Whale persistence boost
    if whale_detected:
        sizing_overlay += SIZING_OVERLAYS["whale_persistence_boost"]
    
    # V3: Congress confirmation boost
    if congress_component > 0.3:
        sizing_overlay += 0.15
    
    # V3: Squeeze setup boost
    if shorts_component > 0.3:
        sizing_overlay += 0.20
    
    # Skew conflict penalty
    if not iv_aligned and abs(iv_skew) > 0.08:
        sizing_overlay += SIZING_OVERLAYS["skew_conflict_penalty"]
    
    # Toxicity penalty
    if toxicity > 0.85:
        sizing_overlay += SIZING_OVERLAYS["toxicity_penalty"]
    
    # ============ ENTRY DELAY ============
    entry_delay_sec = 0
    if motif_staircase.get("detected") and motif_staircase.get("steps", 0) < 4:
        entry_delay_sec = 120
    if motif_sweep.get("detected") and motif_sweep.get("immediate"):
        entry_delay_sec = 0
    if motif_burst.get("detected") and motif_burst.get("intensity", 0) > 2.0:
        entry_delay_sec = 180
    
    # ============ BUILD RESULT ============
    components = {
        # Core
        "flow": round(flow_component, 3),
        "dark_pool": round(dp_component, 3),
        "insider": round(insider_component, 3),
        # V2
        "iv_skew": round(iv_component, 3),
        "smile": round(smile_component, 3),
        "whale": round(whale_score, 3),
        "event": round(event_component, 3),
        "motif_bonus": round(motif_bonus, 3),
        "toxicity_penalty": round(toxicity_component, 3),
        "regime": round(regime_component, 3),
        # V3 NEW
        "congress": round(congress_component, 3),
        "shorts_squeeze": round(shorts_component, 3),
        "institutional": round(inst_component, 3),
        "market_tide": round(tide_component, 3),
        "calendar": round(calendar_component, 3),
        # V2 NEW (Full Intelligence Pipeline) - must match SIGNAL_COMPONENTS in main.py
        "greeks_gamma": round(greeks_gamma_component, 3),
        "ftd_pressure": round(ftd_pressure_component, 3),
        "iv_rank": round(iv_rank_component, 3),
        "oi_change": round(oi_change_component, 3),
        "etf_flow": round(etf_flow_component, 3),
        "squeeze_score": round(squeeze_score_component, 3),
        # Meta
        "freshness_factor": round(freshness, 3)
    }

    # Component sources for audit/telemetry
    # WHY: Stop treating neutral defaults as "real" signal; make it explicit which components were defaulted/missing.
    # HOW TO VERIFY: position metadata and attribution logs include component_sources; defaults correlate with *_neutral_default notes.
    default_note_by_component = {
        "congress": "congress_neutral_default",
        "shorts_squeeze": "shorts_neutral_default",
        "institutional": "institutional_neutral_default",
        "market_tide": "tide_neutral_default",
        "calendar": "calendar_neutral_default",
        "greeks_gamma": "greeks_neutral_default",
        "ftd_pressure": "ftd_neutral_default",
        "oi_change": "oi_change_neutral_default",
        "etf_flow": "etf_flow_neutral_default",
        "squeeze_score": "squeeze_score_neutral_default",
    }
    component_sources = {}
    missing_components = []
    for name in components.keys():
        source = "real"
        note_marker = default_note_by_component.get(name)
        if note_marker and note_marker in all_notes:
            source = "default"
        # Dark pool "0 notional + NEUTRAL" should be treated as missing signal.
        if name == "dark_pool" and dp_sent not in ("BULLISH", "BEARISH") and dp_prem <= 0:
            source = "missing"
        # Whale/motif are legitimately absent when no motif detected.
        if name == "whale" and not whale_detected:
            source = "missing"
        if name == "motif_bonus" and not (motif_staircase.get("detected") or motif_burst.get("detected")):
            source = "missing"
        component_sources[name] = source
        if source == "missing":
            missing_components.append(name)

    return {
        "symbol": symbol,
        "score": round(composite_score, 3),
        "version": "V3.1" if adaptive_active else "V3",
        "adaptive_weights_active": adaptive_active,
        "gamma_resistance_levels": gamma_resistance_levels,
        "components": components,
        "component_sources": component_sources,
        "missing_components": missing_components,
        "motifs": {
            "staircase": motif_staircase.get("detected", False),
            "sweep_block": motif_sweep.get("detected", False),
            "burst": motif_burst.get("detected", False),
            "whale_persistence": whale_detected
        },
        "expanded_intel": {
            # V1 intelligence
            "congress_active": bool(congress_data),
            "shorts_active": bool(shorts_data),
            "tide_active": bool(tide_data),
            "calendar_active": bool(calendar_data),
            # V2 NEW intelligence
            "greeks_active": bool(enriched_data.get("greeks", {}).get("gamma_exposure", 0)),
            "ftd_active": bool(enriched_data.get("ftd", {}).get("ftd_count", 0)),
            "iv_active": bool(enriched_data.get("iv", {}).get("iv_rank", 0)),
            "oi_active": bool(enriched_data.get("oi", {}).get("net_oi_change", 0)),
            "etf_active": bool(enriched_data.get("etf_flow", {}).get("overall_sentiment")),
            "squeeze_active": bool(enriched_data.get("squeeze_score", {}).get("signals", 0))
        },
        "sizing_overlay": round(sizing_overlay, 3),
        "entry_delay_sec": entry_delay_sec,
        "toxicity": round(toxicity, 3),
        "freshness": round(freshness, 3),
        "whale_conviction_boost": round(whale_conviction_boost, 3),  # ALPHA REPAIR: Track whale boost applied
        "notes": "; ".join(all_notes) if all_notes else "clean",
        # For learning - all raw inputs (V2 Full Intelligence Pipeline)
        "features_for_learning": {
            # Original features
            "flow_conviction": flow_conv,
            "flow_sign": flow_sign,
            "dp_premium": dp_prem,
            "dp_notional_1h": dp_notional_1h,
            "sweep_urgency_multiplier": urgency_multiplier,
            "iv_skew": iv_skew,
            "smile_slope": smile_slope,
            "toxicity": toxicity,
            "congress_buys": congress_data.get("buys", 0) if congress_data else 0,
            "congress_sells": congress_data.get("sells", 0) if congress_data else 0,
            "short_interest_pct": shorts_data.get("interest_pct", 0) if shorts_data else 0,
            "days_to_cover": shorts_data.get("days_to_cover", 0) if shorts_data else 0,
            "squeeze_risk": shorts_data.get("squeeze_risk", False) if shorts_data else False,
            "regime": regime,
            # V2 NEW: Full intelligence pipeline features
            "greeks_gamma": _to_num(enriched_data.get("greeks", {}).get("gamma_exposure", 0)),
            "greeks_delta": _to_num(enriched_data.get("greeks", {}).get("delta_exposure", 0)),
            "gamma_squeeze_setup": enriched_data.get("greeks", {}).get("gamma_squeeze_setup", False),
            "ftd_count": _to_num(enriched_data.get("ftd", {}).get("ftd_count", 0)),
            "ftd_pressure": enriched_data.get("ftd", {}).get("squeeze_pressure", False),
            "iv_rank": _to_num(enriched_data.get("iv", {}).get("iv_rank", 0)),
            "iv_percentile": _to_num(enriched_data.get("iv", {}).get("iv_percentile", 0)),
            "high_iv_caution": enriched_data.get("iv", {}).get("high_iv_caution", False),
            "low_iv_opportunity": enriched_data.get("iv", {}).get("low_iv_opportunity", False),
            "oi_net_change": _to_num(enriched_data.get("oi", {}).get("net_oi_change", 0)),
            "oi_sentiment": enriched_data.get("oi", {}).get("oi_sentiment", "NEUTRAL"),
            "etf_overall_sentiment": enriched_data.get("etf_flow", {}).get("overall_sentiment", "NEUTRAL"),
            "market_risk_on": enriched_data.get("etf_flow", {}).get("market_risk_on", False),
            "squeeze_signals": _to_num(enriched_data.get("squeeze_score", {}).get("signals", 0)),
            "high_squeeze_potential": enriched_data.get("squeeze_score", {}).get("high_squeeze_potential", False),
            "squeeze_setup_type": enriched_data.get("squeeze_score", {}).get("setup", "NONE"),
            "max_pain": _to_num(enriched_data.get("max_pain", {}).get("max_pain", 0))
        }
    }


def _clamp(x: float, lo: float, hi: float) -> float:
    try:
        return max(float(lo), min(float(hi), float(x)))
    except Exception:
        return float(lo)


@global_failure_wrapper("scoring")
def compute_composite_score_v3_v2(
    symbol: str,
    enriched_data: Dict,
    regime: str = "NEUTRAL",
    *,
    market_context: Optional[Dict[str, Any]] = None,
    posture_state: Optional[Dict[str, Any]] = None,
    base_override: Optional[Dict[str, Any]] = None,
    expanded_intel: Dict = None,
    use_adaptive_weights: bool = True,
    v2_params: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Composite V2 (for A/B shadow):
    - Uses the current production composite (v1) as a base
    - Applies explicit, parameterized adjustments for:
      - realized volatility
      - beta vs SPY
      - regime/posture alignment

    IMPORTANT:
    - This function is additive and does not replace production scoring unless explicitly enabled.
    - It is designed for shadow comparison and observability.
    """
    if market_context is None:
        market_context = {}
    if posture_state is None:
        posture_state = {}
    if v2_params is None:
        # Default to config-driven params when available (shadow-safe).
        try:
            from config.registry import COMPOSITE_WEIGHTS_V2 as _CWV2  # type: ignore
            v2_params = dict(_CWV2) if isinstance(_CWV2, dict) else {}
        except Exception:
            v2_params = {}
        if not v2_params:
            v2_params = {
                "version": "fallback_defaults",
                "vol_center": 0.20,
                "vol_scale": 0.25,
                "vol_bonus_max": 0.6,
                "low_vol_penalty_center": 0.15,
                "low_vol_penalty_max": -0.10,
                "beta_center": 1.00,
                "beta_scale": 1.00,
                "beta_bonus_max": 0.4,
                "uw_center": 0.55,
                "uw_scale": 0.45,
                "uw_bonus_max": 0.20,
                "premarket_align_bonus": 0.10,
                "premarket_misalign_penalty": -0.10,
                "regime_align_bonus": 0.5,
                "regime_misalign_penalty": -0.25,
                "posture_conf_strong": 0.65,
                "high_vol_multiplier": 1.15,
                "low_vol_multiplier": 0.90,
                "mid_vol_multiplier": 1.00,
                "misalign_dampen": 0.25,
                "neutral_dampen": 0.60,
            }

    # Base score source:
    # - If base_override is provided, we treat it as the already-finalized v1 composite (including upstream boosts)
    #   and only apply the v2 adjustment layer for comparability.
    # - Otherwise compute v1 from scratch.
    if isinstance(base_override, dict) and base_override:
        base = dict(base_override)
    else:
        base = compute_composite_score_v3(
            symbol,
            enriched_data,
            regime=regime,
            expanded_intel=expanded_intel,
            use_adaptive_weights=use_adaptive_weights,
        ) or {}

    base_score = _to_num(base.get("score", 0.0))

    # Inputs (from enrichment feature store)
    vol_20d = _to_num(enriched_data.get("realized_vol_20d", 0.0))
    beta = _to_num(enriched_data.get("beta_vs_spy", 0.0))
    flow_conv = _to_num(enriched_data.get("conviction", enriched_data.get("flow_conv", 0.0)))
    trade_count = int(_to_num(enriched_data.get("trade_count", 0)) or 0)

    # Context
    vol_regime = str(market_context.get("volatility_regime", "mid") or "mid").lower()
    posture = str(posture_state.get("posture", "neutral") or "neutral").lower()
    posture_conf = _to_num(posture_state.get("regime_confidence", posture_state.get("regime_confidence", 0.0)))

    # Direction from sentiment
    sent = enriched_data.get("sentiment") or "NEUTRAL"
    direction = "bullish" if sent == "BULLISH" else ("bearish" if sent == "BEARISH" else "neutral")

    # Multipliers by vol regime
    if vol_regime == "high":
        vol_mult = float(v2_params.get("high_vol_multiplier", 1.30))
    elif vol_regime == "low":
        vol_mult = float(v2_params.get("low_vol_multiplier", 0.85))
    else:
        vol_mult = float(v2_params.get("mid_vol_multiplier", 1.00))

    # Alignment dampening (avoid boosting misaligned directions).
    align = (posture == "long" and direction == "bullish") or (posture == "short" and direction == "bearish")
    misalign = (posture == "long" and direction == "bearish") or (posture == "short" and direction == "bullish")
    if misalign:
        align_mult = float(v2_params.get("misalign_dampen", 0.25))
    elif direction == "neutral" or posture == "neutral":
        align_mult = float(v2_params.get("neutral_dampen", 0.60))
    else:
        align_mult = 1.0

    # Volatility preference: reward higher realized vol (and optionally penalize low-vol in high-vol regimes).
    vol_center = float(v2_params.get("vol_center", 0.20))
    vol_scale = float(v2_params.get("vol_scale", 0.25)) or 0.25
    vol_strength = _clamp((vol_20d - vol_center) / vol_scale, 0.0, 1.0)
    vol_bonus = float(v2_params.get("vol_bonus_max", 0.6)) * vol_strength * vol_mult * align_mult
    low_vol_pen = 0.0
    if vol_regime == "high":
        low_center = float(v2_params.get("low_vol_penalty_center", 0.15))
        low_strength = _clamp((low_center - vol_20d) / max(1e-9, low_center), 0.0, 1.0)
        low_vol_pen = float(v2_params.get("low_vol_penalty_max", -0.10)) * low_strength * align_mult

    # Beta preference: prefer beta > 1 when otherwise comparable.
    beta_center = float(v2_params.get("beta_center", 1.0))
    beta_scale = float(v2_params.get("beta_scale", 1.0)) or 1.0
    beta_strength = _clamp((beta - beta_center) / beta_scale, 0.0, 1.0)
    beta_bonus = float(v2_params.get("beta_bonus_max", 0.4)) * beta_strength * vol_mult * align_mult

    # UW strength proxy: conviction + trade_count (only reward when there is actual flow data).
    uw_strength = _clamp(flow_conv, 0.0, 1.0) if trade_count > 0 else 0.0
    uw_center = float(v2_params.get("uw_center", 0.55))
    uw_scale = float(v2_params.get("uw_scale", 0.45)) or 0.45
    uw_norm = _clamp((uw_strength - uw_center) / uw_scale, 0.0, 1.0)
    uw_bonus = float(v2_params.get("uw_bonus_max", 0.2)) * uw_norm * align_mult

    # Premarket / futures proxy alignment (SPY/QQQ overnight direction).
    spy_ov = _to_num(market_context.get("spy_overnight_ret", 0.0))
    qqq_ov = _to_num(market_context.get("qqq_overnight_ret", 0.0))
    mkt_trend = str(market_context.get("market_trend", "") or "")
    fut_dir = "up" if (spy_ov + qqq_ov) > 0.005 else ("down" if (spy_ov + qqq_ov) < -0.005 else "flat")
    pre_bonus = 0.0
    if direction in ("bullish", "bearish"):
        aligned = (direction == "bullish" and fut_dir == "up") or (direction == "bearish" and fut_dir == "down")
        if aligned:
            pre_bonus = float(v2_params.get("premarket_align_bonus", 0.10)) * align_mult
        elif fut_dir in ("up", "down"):
            pre_bonus = float(v2_params.get("premarket_misalign_penalty", -0.10)) * align_mult

    # Regime/posture alignment (directional).
    conf_mult = 1.0 if posture_conf >= float(v2_params.get("posture_conf_strong", 0.65)) else 0.6
    regime_bonus = float(v2_params.get("regime_align_bonus", 0.5)) * (conf_mult if align else 0.0)
    regime_pen = float(v2_params.get("regime_misalign_penalty", -0.25)) * (conf_mult if misalign else 0.0)

    total_adj = vol_bonus + low_vol_pen + beta_bonus + uw_bonus + pre_bonus + regime_bonus + regime_pen
    score_v2 = _clamp(base_score + total_adj, 0.0, 8.0)

    # Annotate
    try:
        base["score"] = round(float(score_v2), 3)
        base["composite_version"] = "v2"
        base["base_score_v1"] = round(float(base_score), 3)
        base["v2_adjustments"] = {
            "vol_bonus": round(float(vol_bonus), 4),
            "low_vol_penalty": round(float(low_vol_pen), 4),
            "beta_bonus": round(float(beta_bonus), 4),
            "uw_bonus": round(float(uw_bonus), 4),
            "premarket_bonus": round(float(pre_bonus), 4),
            "regime_align_bonus": round(float(regime_bonus), 4),
            "regime_misalign_penalty": round(float(regime_pen), 4),
            "total": round(float(total_adj), 4),
        }
        base["v2_inputs"] = {
            "realized_vol_20d": round(float(vol_20d), 6),
            "beta_vs_spy": round(float(beta), 6),
            "uw_conviction": round(float(flow_conv), 6),
            "trade_count": int(trade_count),
            "volatility_regime": vol_regime,
            "market_trend": str(mkt_trend),
            "futures_direction": str(fut_dir),
            "spy_overnight_ret": round(float(spy_ov), 6),
            "qqq_overnight_ret": round(float(qqq_ov), 6),
            "posture": posture,
            "direction": direction,
            "posture_confidence": round(float(posture_conf), 4),
            "weights_version": str(v2_params.get("version", "")),
        }
        # Preserve existing notes while making adjustments explicit.
        base["notes"] = (str(base.get("notes", "") or "") + f"; v2_adj={round(float(total_adj), 3)}").strip("; ").strip()
        base["version"] = str(base.get("version", "V3")) + "+V2"
    except Exception:
        pass

    return base

def compute_composite_score_v2(symbol: str, enriched_data: Dict, regime: str = "NEUTRAL") -> Dict[str, Any]:
    """
    V2 Composite scoring with expanded features and motif awareness
    
    Returns:
    {
      "symbol": str,
      "score": float (0-6.0, higher max due to new components),
      "components": {...breakdown...},
      "motifs": {...detected patterns...},
      "sizing_overlay": float (multiplier),
      "entry_delay_sec": int,
      "notes": str
    }
    """
    
    # Base flow components
    flow_sent = enriched_data.get("sentiment", "NEUTRAL")
    flow_conv = _to_num(enriched_data.get("conviction", 0.0))
    
    dp = enriched_data.get("dark_pool", {}) or {}
    dp_sent = dp.get("sentiment", "NEUTRAL")
    dp_prem = _to_num(dp.get("total_premium", 0.0))
    
    ins = enriched_data.get("insider", {}) or {}
    ins_sent = ins.get("sentiment", "NEUTRAL")
    ins_mod = _to_num(ins.get("conviction_modifier", 0.0))
    
    # New V2 features
    iv_skew = _to_num(enriched_data.get("iv_term_skew", 0.0))
    smile_slope = _to_num(enriched_data.get("smile_slope", 0.0))
    toxicity = _to_num(enriched_data.get("toxicity", 0.0))
    event_align = _to_num(enriched_data.get("event_alignment", 0.0))
    freshness = _to_num(enriched_data.get("freshness", 1.0))
    
    # Motif data
    motif_staircase = enriched_data.get("motif_staircase", {})
    motif_sweep = enriched_data.get("motif_sweep_block", {})
    motif_burst = enriched_data.get("motif_burst", {})
    motif_whale = enriched_data.get("motif_whale", {})
    
    # Component calculations
    
    # 1. Options flow (primary)
    flow_component = WEIGHTS_V2["options_flow"] * flow_conv
    
    # 2. Dark pool (enhanced)
    dp_strength = 0.0
    if dp_sent in ("BULLISH", "BEARISH"):
        # Notional scaling with log
        import math
        mag = max(1.0, dp_prem)
        log_factor = min(0.8, math.log10(mag) / 7.5)
        dp_strength = 0.5 + log_factor
    else:
        dp_strength = 0.2
    dp_component = WEIGHTS_V2["dark_pool"] * dp_strength
    
    # 3. Insider (baseline)
    if ins_sent == "BULLISH":
        insider_component = WEIGHTS_V2["insider"] * (0.50 + ins_mod)
    elif ins_sent == "BEARISH":
        insider_component = WEIGHTS_V2["insider"] * (0.50 - abs(ins_mod))
    else:
        insider_component = WEIGHTS_V2["insider"] * 0.25
    
    # 4. IV term skew (new)
    # Positive skew in aligned direction = boost
    flow_sign = _sign_from_sentiment(flow_sent)
    iv_aligned = (iv_skew > 0 and flow_sign == +1) or (iv_skew < 0 and flow_sign == -1)
    iv_component = WEIGHTS_V2["iv_term_skew"] * abs(iv_skew) * (1.3 if iv_aligned else 0.7)
    
    # 5. Smile slope (new)
    smile_component = WEIGHTS_V2["smile_slope"] * abs(smile_slope)
    
    # 6. Whale persistence (new)
    whale_detected = motif_whale.get("detected", False)
    whale_score = 0.0
    if whale_detected:
        avg_conv = motif_whale.get("avg_conviction", 0.0)
        whale_score = WEIGHTS_V2["whale_persistence"] * avg_conv
    
    # 7. Event alignment (new)
    event_component = WEIGHTS_V2["event_alignment"] * event_align
    
    # 8. Temporal motif bonus (new)
    motif_bonus = 0.0
    motif_notes = []
    
    if motif_staircase.get("detected"):
        motif_bonus += WEIGHTS_V2["temporal_motif"] * motif_staircase.get("slope", 0.0) * 3.0
        motif_notes.append(f"staircase({motif_staircase['steps']} steps)")
    
    if motif_burst.get("detected"):
        intensity = motif_burst.get("intensity", 0.0)
        motif_bonus += WEIGHTS_V2["temporal_motif"] * min(1.0, intensity / 2.0)
        motif_notes.append(f"burst({motif_burst['count']} updates)")
    
    # 9. Toxicity penalty - FIXED: Apply penalty starting at 0.5 (was 0.85)
    # CRITICAL: Ensure toxicity weight is NEGATIVE (it's a penalty, not a boost)
    raw_tox_weight_v2 = WEIGHTS_V2.get("toxicity_penalty", -0.9)
    tox_weight_v2 = raw_tox_weight_v2 if raw_tox_weight_v2 < 0 else -abs(raw_tox_weight_v2)  # Force negative
    toxicity_component = 0.0
    if toxicity > 0.5:
        toxicity_component = tox_weight_v2 * (toxicity - 0.5) * 1.5
        motif_notes.append(f"toxicity_penalty({toxicity:.2f})")
    elif toxicity > 0.3:
        toxicity_component = tox_weight_v2 * (toxicity - 0.3) * 0.5
        motif_notes.append(f"mild_toxicity({toxicity:.2f})")
    
    # 10. Regime modifier
    flow_sign = _sign_from_sentiment(flow_sent)
    aligned_regime = (regime == "RISK_ON" and flow_sign == +1) or (regime == "RISK_OFF" and flow_sign == -1)
    opposite_regime = (regime == "RISK_ON" and flow_sign == -1) or (regime == "RISK_OFF" and flow_sign == +1)
    
    regime_factor = 1.0
    if regime == "RISK_ON":
        regime_factor = 1.15 if aligned_regime else 0.95
    elif regime == "RISK_OFF":
        regime_factor = 1.10 if opposite_regime else 0.90
    
    regime_component = WEIGHTS_V2["regime_modifier"] * (regime_factor - 1.0) * 2.0
    
    # Sum all components
    composite_raw = (
        flow_component +
        dp_component +
        insider_component +
        iv_component +
        smile_component +
        whale_score +
        event_component +
        motif_bonus +
        toxicity_component +  # Negative penalty
        regime_component
    )
    
    # Apply freshness decay
    composite_score = composite_raw * freshness
    
    # Clamp to 0-6 (higher max due to new components)
    composite_score = max(0.0, min(6.0, composite_score))
    
    # Sizing overlay calculation
    sizing_overlay = 0.0
    
    # IV skew alignment boost
    if iv_aligned and abs(iv_skew) > 0.08:
        sizing_overlay += SIZING_OVERLAYS["iv_skew_align_boost"]
    
    # Whale persistence boost
    if whale_detected:
        sizing_overlay += SIZING_OVERLAYS["whale_persistence_boost"]
    
    # Skew conflict penalty
    if not iv_aligned and abs(iv_skew) > 0.08:
        sizing_overlay += SIZING_OVERLAYS["skew_conflict_penalty"]
    
    # Toxicity penalty
    if toxicity > 0.85:
        sizing_overlay += SIZING_OVERLAYS["toxicity_penalty"]
    
    # Entry delay (for motif-aware execution)
    entry_delay_sec = 0
    
    # Staircase: wait for pattern confirmation
    if motif_staircase.get("detected") and motif_staircase.get("steps", 0) < 4:
        entry_delay_sec = 120  # Wait 2 min for more steps
    
    # Sweep/block immediate
    if motif_sweep.get("detected") and motif_sweep.get("immediate"):
        entry_delay_sec = 0  # Enter immediately on sweep
    
    # Burst: wait for intensity to settle
    if motif_burst.get("detected") and motif_burst.get("intensity", 0) > 2.0:
        entry_delay_sec = 180  # Wait 3 min for burst to settle
    
    # Build result
    return {
        "symbol": symbol,
        "score": round(composite_score, 3),
        "components": {
            "flow": round(flow_component, 3),
            "dark_pool": round(dp_component, 3),
            "insider": round(insider_component, 3),
            "iv_skew": round(iv_component, 3),
            "smile": round(smile_component, 3),
            "whale": round(whale_score, 3),
            "event": round(event_component, 3),
            "motif_bonus": round(motif_bonus, 3),
            "toxicity_penalty": round(toxicity_component, 3),
            "regime": round(regime_component, 3),
            "freshness_factor": round(freshness, 3)
        },
        "motifs": {
            "staircase": motif_staircase.get("detected", False),
            "sweep_block": motif_sweep.get("detected", False),
            "burst": motif_burst.get("detected", False),
            "whale_persistence": whale_detected
        },
        "sizing_overlay": round(sizing_overlay, 3),
        "entry_delay_sec": entry_delay_sec,
        "toxicity": round(toxicity, 3),
        "freshness": round(freshness, 3),
        "notes": "; ".join(motif_notes) if motif_notes else "clean"
    }

def get_threshold(symbol: str, mode: str = "base") -> float:
    """
    Get hierarchical threshold for symbol
    Falls back to mode-based threshold if no hierarchical data
    """
    if THRESHOLD_STATE.exists():
        try:
            with THRESHOLD_STATE.open("r") as f:
                thresholds = json.load(f)
                return thresholds.get(symbol, ENTRY_THRESHOLDS[mode])
        except:
            pass
    
    return ENTRY_THRESHOLDS[mode]

@global_failure_wrapper("gate")
def should_enter_v2(composite: Dict, symbol: str, mode: str = "base", api=None) -> bool:
    """
    V3.0 Predatory Entry Filter: V2 entry decision with hierarchical thresholds + Exhaustion Check
    
    Industrial Upgrade:
    - MIN_EXEC_SCORE increased to 3.0 (quality gate)
    - Exhaustion Check: Block entries where price > 2.5 ATRs from 20-period EMA
      (avoids buying the 'top' of a spike)
    """
    if not composite:
        # DIAGNOSTIC: Log composite None
        _log_gate_failure(symbol, "composite_none", {"reason": "composite is None or empty"})
        return False
    
    score = composite.get("score", 0.0)
    threshold = get_threshold(symbol, mode)
    
    # V3.0: Score must be >= 3.0 (MIN_EXEC_SCORE from config)
    if score < threshold:
        # DIAGNOSTIC: Log score gate failure
        _log_gate_failure(symbol, "score_gate", {
            "score": score,
            "threshold": threshold,
            "gap": threshold - score,
            "reason": f"Score {score:.2f} < threshold {threshold:.2f}"
        })
        return False
    
    # Additional gating: don't enter if toxicity too high
    toxicity = composite.get("toxicity", 0.0)
    if toxicity > 0.90:
        # DIAGNOSTIC: Log toxicity gate failure
        _log_gate_failure(symbol, "toxicity_gate", {
            "toxicity": toxicity,
            "threshold": 0.90,
            "reason": f"Toxicity {toxicity:.2f} > 0.90"
        })
        return False
    
    # Don't enter if freshness too low (stale data)
    # CRITICAL FIX: Allow freshness as low as 0.25 if score is good
    # The freshness floor in main.py sets minimum to 0.9, so this should rarely trigger
    freshness = composite.get("freshness", 1.0)
    if freshness < 0.25:  # Lowered from 0.30 to 0.25 to match freshness floor fix
        # DIAGNOSTIC: Log freshness gate failure
        _log_gate_failure(symbol, "freshness_gate", {
            "freshness": freshness,
            "threshold": 0.25,
            "reason": f"Freshness {freshness:.2f} < 0.25"
        })
        return False
    
    # V3.0 EXHAUSTION CHECK: Block entries where price is > 2.5 ATRs from 20-period EMA
    # Purpose: Filter out noise and avoid buying the 'top' of a spike
    if api is not None:
        try:
            from main import compute_atr
            import pandas as pd
            
            # Get current price
            try:
                current_price = float(api.get_last_trade(symbol).price) if hasattr(api.get_last_trade(symbol), 'price') else None
                if not current_price:
                    last_trade = api.get_last_trade(symbol)
                    current_price = float(last_trade) if isinstance(last_trade, (int, float)) else None
            except:
                # Fallback: try getting quote
                try:
                    quote = api.get_quote(symbol)
                    current_price = (float(quote.bid) + float(quote.ask)) / 2.0
                except:
                    current_price = None
            
            if current_price and current_price > 0:
                # Compute ATR (14-period is standard, but we'll use what's available)
                atr = compute_atr(api, symbol, lookback=20)
                
                # Compute 20-period EMA
                try:
                    bars = api.get_bars(symbol, "1Min", limit=25).df
                    if len(bars) >= 20:
                        # Calculate EMA
                        ema_20 = bars['close'].ewm(span=20, adjust=False).mean().iloc[-1]
                        
                        if atr > 0 and ema_20 > 0:
                            # Check if price is > 2.5 ATRs above EMA
                            distance_from_ema = current_price - ema_20
                            atr_distance = distance_from_ema / atr if atr > 0 else 0
                            
                            if atr_distance > 2.5:
                                # EXHAUSTION DETECTED: Price too extended from EMA
                                # DIAGNOSTIC: Log exhaustion gate failure
                                _log_gate_failure(symbol, "atr_exhaustion_gate", {
                                    "current_price": current_price,
                                    "ema_20": float(ema_20),
                                    "atr": atr,
                                    "atr_distance": round(atr_distance, 2),
                                    "threshold": 2.5,
                                    "signal_score": score,
                                    "reason": f"Price {current_price:.2f} is {atr_distance:.2f} ATRs above EMA {float(ema_20):.2f} (threshold: 2.5)"
                                })
                                return False  # Block exhausted entry
                except Exception as e:
                    # If EMA calculation fails, fail open (allow trade)
                    # Log error but don't block
                    pass
        except Exception as e:
            # If exhaustion check fails, fail open (allow trade)
            # This ensures we don't block trades due to technical indicator errors
            pass

    # Phase 5: Gamma wall awareness — block trades into resistance walls
    try:
        levels = composite.get("gamma_resistance_levels") or []
        if api is not None and levels:
            # Reuse current price best-effort (as above); fall back to last trade.
            try:
                current_price = float(api.get_last_trade(symbol).price) if hasattr(api.get_last_trade(symbol), 'price') else None
            except Exception:
                current_price = None
            if not current_price or current_price <= 0:
                try:
                    quote = api.get_quote(symbol)
                    current_price = (float(quote.bid) + float(quote.ask)) / 2.0
                except Exception:
                    current_price = None

            if current_price and current_price > 0:
                nearest = None
                nearest_dist = None
                for lv in levels:
                    lvf = _to_num(lv, 0.0)
                    if lvf <= 0:
                        continue
                    dist = abs(current_price - lvf) / lvf
                    if nearest_dist is None or dist < nearest_dist:
                        nearest_dist = dist
                        nearest = lvf
                if nearest is not None and nearest_dist is not None and nearest_dist <= 0.002:
                    composite["gate_msg"] = "resistance_wall_detected"
                    composite["notes"] = (composite.get("notes", "") + "; gate:resistance_wall_detected").strip("; ").strip()
                    _log_gate_failure(symbol, "resistance_wall_detected", {
                        "current_price": float(current_price),
                        "nearest_level": float(nearest),
                        "distance_pct": round(nearest_dist * 100, 4),
                        "threshold_pct": 0.2,
                        "reason": "Entry price within 0.2% of gamma resistance level"
                    })
                    return False
    except Exception:
        pass
    
    return score >= threshold

def apply_sizing_overlay(base_qty: int, composite: Dict) -> int:
    """
    Apply sizing overlay from motif/feature analysis
    """
    overlay = composite.get("sizing_overlay", 0.0)
    adjusted_qty = base_qty * (1.0 + overlay)
    
    # Clamp to reasonable bounds (±40%)
    min_qty = int(base_qty * 0.6)
    max_qty = int(base_qty * 1.4)
    
    return max(min_qty, min(max_qty, int(adjusted_qty)))

if __name__ == "__main__":
    # Test V3 FULL INTELLIGENCE scoring
    test_data_v3 = {
        "sentiment": "BULLISH",
        "conviction": 0.85,
        "dark_pool": {"sentiment": "BULLISH", "total_premium": 45000000},
        "insider": {"sentiment": "BULLISH", "conviction_modifier": 0.05, "net_buys": 5, "net_sells": 1, "total_usd": 2500000},
        "iv_term_skew": 0.12,
        "smile_slope": 0.08,
        "toxicity": 0.65,
        "event_alignment": 0.85,
        "freshness": 0.95,
        "motif_staircase": {"detected": True, "steps": 4, "slope": 0.05},
        "motif_sweep_block": {"detected": False},
        "motif_burst": {"detected": False},
        "motif_whale": {"detected": True, "avg_conviction": 0.82},
        # V3 NEW: Expanded Intelligence
        "congress": {"recent_count": 3, "buys": 2, "sells": 0, "net_sentiment": "BULLISH", "conviction_boost": 0.1},
        "shorts": {"interest_pct": 22.5, "days_to_cover": 6.2, "ftd_count": 250000, "squeeze_risk": True}
    }
    
    # Test expanded intel cache
    test_expanded_intel = {
        "AAPL": {
            "market_tide": {"call_premium": 120000000, "put_premium": 80000000, "net_delta": 40000000, "sentiment": "BULLISH"},
            "calendar": {"has_earnings": True, "earnings_date": "2025-01-30", "days_to_earnings": 5, "has_fda": False, "economic_events": ["FOMC", "CPI"]}
        }
    }
    
    print("=" * 60)
    print("V3 FULL INTELLIGENCE COMPOSITE SCORING TEST")
    print("=" * 60)
    
    result_v3 = compute_composite_score_v3("AAPL", test_data_v3, "RISK_ON", test_expanded_intel)
    print(json.dumps(result_v3, indent=2))
    print(f"\nV3 Score: {result_v3['score']:.3f}")
    print(f"Should enter: {should_enter_v2(result_v3, 'AAPL', 'base')}")
    print(f"Sizing overlay: {result_v3['sizing_overlay']:.2%}")
    print(f"\nExpanded Intel Active: {result_v3['expanded_intel']}")
    print(f"Notes: {result_v3['notes']}")
    print(f"\nFeatures for Learning: {json.dumps(result_v3['features_for_learning'], indent=2)}")
    
    print("\n" + "=" * 60)
    print("V2 LEGACY SCORING (for comparison)")
    print("=" * 60)
    
    result_v2 = compute_composite_score_v2("AAPL", test_data_v3, "RISK_ON")
    print(f"V2 Score: {result_v2['score']:.3f}")
    print(f"Score difference (V3-V2): {result_v3['score'] - result_v2['score']:.3f}")
