#!/usr/bin/env python3
"""
Score Telemetry Module
======================
Tracks score distribution, component health, and missing data patterns.

SCORING PIPELINE FIX (Part 2): Telemetry for score monitoring
See SIGNAL_SCORE_PIPELINE_AUDIT.md for context
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict
from datetime import datetime, timezone

# State file for telemetry data
TELEMETRY_FILE = Path("state/score_telemetry.json")

# Global telemetry state
_telemetry_state = {
    "scores": [],  # List of (symbol, score, timestamp) tuples
    "components": defaultdict(lambda: {"count": 0, "total": 0.0, "zero_count": 0}),
    "missing_intel": defaultdict(int),  # Component name -> count of missing
    "defaulted_conviction": 0,  # Count of times conviction was defaulted to 0.5
    "decay_factors": [],  # List of freshness values applied
    "neutral_defaults": defaultdict(int),  # Component name -> count of neutral defaults
    "core_features_missing": defaultdict(int),  # Feature name -> count
    "last_update": None
}

_telemetry_lock = None  # Will be set to threading.Lock if needed


def _load_telemetry() -> Dict:
    """Load telemetry state from disk."""
    global _telemetry_state
    try:
        if TELEMETRY_FILE.exists():
            with open(TELEMETRY_FILE, 'r') as f:
                data = json.load(f)
                # Merge with defaults
                _telemetry_state.update(data)
                # Ensure all required keys exist
                for key in ["scores", "components", "missing_intel", "defaulted_conviction", 
                           "decay_factors", "neutral_defaults", "core_features_missing"]:
                    if key not in _telemetry_state:
                        if key == "scores":
                            _telemetry_state[key] = []
                        elif key == "decay_factors":
                            _telemetry_state[key] = []
                        else:
                            _telemetry_state[key] = defaultdict(int) if "missing" in key or "defaults" in key or "features" in key else 0
    except Exception as e:
        print(f"WARNING: Failed to load score telemetry: {e}", flush=True)
    return _telemetry_state


def _save_telemetry():
    """Save telemetry state to disk."""
    global _telemetry_state
    try:
        TELEMETRY_FILE.parent.mkdir(exist_ok=True, parents=True)
        
        # Convert defaultdicts to regular dicts for JSON serialization
        state_to_save = {
            "scores": _telemetry_state["scores"][-1000:],  # Keep last 1000 scores
            "components": {k: dict(v) for k, v in _telemetry_state["components"].items()},
            "missing_intel": dict(_telemetry_state["missing_intel"]),
            "defaulted_conviction": _telemetry_state["defaulted_conviction"],
            "decay_factors": _telemetry_state["decay_factors"][-1000:],  # Keep last 1000
            "neutral_defaults": dict(_telemetry_state["neutral_defaults"]),
            "core_features_missing": dict(_telemetry_state["core_features_missing"]),
            "last_update": datetime.now(timezone.utc).isoformat()
        }
        
        # Atomic write
        temp_file = TELEMETRY_FILE.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(state_to_save, f, indent=2)
        temp_file.replace(TELEMETRY_FILE)
    except Exception as e:
        print(f"WARNING: Failed to save score telemetry: {e}", flush=True)


def record(symbol: str, score: float, components: Dict[str, float], 
           metadata: Optional[Dict[str, Any]] = None):
    """
    Record a score calculation with component breakdown.
    
    Args:
        symbol: Stock symbol
        score: Final composite score
        components: Dict of component_name -> component_value
        metadata: Optional dict with:
            - freshness: float (freshness factor applied)
            - conviction_defaulted: bool (if conviction was defaulted to 0.5)
            - missing_intel: List[str] (list of missing expanded intel components)
            - neutral_defaults: List[str] (list of components using neutral defaults)
            - core_features_missing: List[str] (list of missing core features)
    """
    global _telemetry_state
    _load_telemetry()
    
    timestamp = time.time()
    
    # Record score
    _telemetry_state["scores"].append({
        "symbol": symbol,
        "score": round(score, 3),
        "timestamp": timestamp,
        "dt": datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
    })
    
    # Record component contributions
    for comp_name, comp_value in components.items():
        if comp_name not in _telemetry_state["components"]:
            _telemetry_state["components"][comp_name] = {"count": 0, "total": 0.0, "zero_count": 0}
        
        comp_stats = _telemetry_state["components"][comp_name]
        comp_stats["count"] += 1
        comp_stats["total"] += abs(comp_value)
        if comp_value == 0.0:
            comp_stats["zero_count"] += 1
    
    # Record metadata
    if metadata:
        if metadata.get("freshness"):
            _telemetry_state["decay_factors"].append({
                "symbol": symbol,
                "freshness": round(metadata["freshness"], 3),
                "timestamp": timestamp
            })
        
        if metadata.get("conviction_defaulted"):
            _telemetry_state["defaulted_conviction"] += 1
        
        if metadata.get("missing_intel"):
            for comp in metadata["missing_intel"]:
                _telemetry_state["missing_intel"][comp] += 1
        
        if metadata.get("neutral_defaults"):
            for comp in metadata["neutral_defaults"]:
                _telemetry_state["neutral_defaults"][comp] += 1
        
        if metadata.get("core_features_missing"):
            for feature in metadata["core_features_missing"]:
                _telemetry_state["core_features_missing"][feature] += 1
    
    _telemetry_state["last_update"] = datetime.now(timezone.utc).isoformat()
    
    # Save periodically (every 10 records or if scores list is getting long)
    if len(_telemetry_state["scores"]) % 10 == 0 or len(_telemetry_state["scores"]) > 1000:
        _save_telemetry()


def get_score_distribution(symbol: Optional[str] = None, lookback_hours: int = 24) -> Dict:
    """
    Get score distribution statistics.
    
    Args:
        symbol: Optional symbol to filter by
        lookback_hours: Hours to look back
    
    Returns:
        Dict with min, max, mean, median, percentiles, histogram
    """
    _load_telemetry()
    
    cutoff_time = time.time() - (lookback_hours * 3600)
    scores = [
        s["score"] for s in _telemetry_state["scores"]
        if s["timestamp"] >= cutoff_time and (symbol is None or s["symbol"] == symbol)
    ]
    
    if not scores:
        return {
            "count": 0,
            "min": 0.0,
            "max": 0.0,
            "mean": 0.0,
            "median": 0.0,
            "p25": 0.0,
            "p75": 0.0,
            "p90": 0.0,
            "histogram": {}
        }
    
    scores_sorted = sorted(scores)
    n = len(scores_sorted)
    
    # Calculate percentiles
    def percentile(data, p):
        if n == 0:
            return 0.0
        k = (n - 1) * p
        f = int(k)
        c = k - f
        if f + 1 < n:
            return data[f] + c * (data[f + 1] - data[f])
        return data[f]
    
    # Build histogram (bins: 0-1, 1-2, 2-3, 3-4, 4-5, 5-6, 6-7, 7-8, 8+)
    histogram = {f"{i}-{i+1}": 0 for i in range(8)}
    histogram["8+"] = 0
    
    for score in scores:
        if score < 1.0:
            histogram["0-1"] += 1
        elif score < 2.0:
            histogram["1-2"] += 1
        elif score < 3.0:
            histogram["2-3"] += 1
        elif score < 4.0:
            histogram["3-4"] += 1
        elif score < 5.0:
            histogram["4-5"] += 1
        elif score < 6.0:
            histogram["5-6"] += 1
        elif score < 7.0:
            histogram["6-7"] += 1
        elif score < 8.0:
            histogram["7-8"] += 1
        else:
            histogram["8+"] += 1
    
    return {
        "count": n,
        "min": round(min(scores), 3),
        "max": round(max(scores), 3),
        "mean": round(sum(scores) / n, 3),
        "median": round(percentile(scores_sorted, 0.5), 3),
        "p25": round(percentile(scores_sorted, 0.25), 3),
        "p75": round(percentile(scores_sorted, 0.75), 3),
        "p90": round(percentile(scores_sorted, 0.90), 3),
        "histogram": histogram
    }


def get_component_health(lookback_hours: int = 24) -> Dict:
    """
    Get component health statistics.
    
    Returns:
        Dict with per-component stats: avg_contribution, zero_percentage, total_count
    """
    _load_telemetry()
    
    cutoff_time = time.time() - (lookback_hours * 3600)
    
    # Filter recent scores
    recent_scores = [
        s for s in _telemetry_state["scores"]
        if s["timestamp"] >= cutoff_time
    ]
    total_recent = len(recent_scores)
    
    if total_recent == 0:
        return {}
    
    # Calculate component stats
    component_stats = {}
    for comp_name, comp_data in _telemetry_state["components"].items():
        if comp_data["count"] > 0:
            avg_contribution = comp_data["total"] / comp_data["count"]
            zero_pct = (comp_data["zero_count"] / comp_data["count"]) * 100
        else:
            avg_contribution = 0.0
            zero_pct = 0.0
        
        component_stats[comp_name] = {
            "avg_contribution": round(avg_contribution, 3),
            "zero_percentage": round(zero_pct, 1),
            "total_count": comp_data["count"],
            "zero_count": comp_data["zero_count"]
        }
    
    return component_stats


def get_missing_intel_stats(lookback_hours: int = 24) -> Dict:
    """
    Get statistics on missing expanded intel components.
    
    Returns:
        Dict with component -> count of times missing
    """
    _load_telemetry()
    
    cutoff_time = time.time() - (lookback_hours * 3600)
    
    # Count recent scores
    recent_scores = [
        s for s in _telemetry_state["scores"]
        if s["timestamp"] >= cutoff_time
    ]
    total_recent = len(recent_scores)
    
    if total_recent == 0:
        return {"missing_counts": {}, "total_scores": 0, "missing_percentages": {}}
    
    # Calculate percentages
    missing_pcts = {}
    for comp, count in _telemetry_state["missing_intel"].items():
        missing_pcts[comp] = round((count / total_recent) * 100, 1)
    
    return {
        "missing_counts": dict(_telemetry_state["missing_intel"]),
        "total_scores": total_recent,
        "missing_percentages": missing_pcts
    }


def get_telemetry_summary() -> Dict:
    """
    Get complete telemetry summary.
    
    Returns:
        Dict with all telemetry statistics
    """
    _load_telemetry()
    
    return {
        "score_distribution": get_score_distribution(),
        "component_health": get_component_health(),
        "missing_intel_stats": get_missing_intel_stats(),
        "defaulted_conviction_count": _telemetry_state["defaulted_conviction"],
        "neutral_defaults": dict(_telemetry_state["neutral_defaults"]),
        "core_features_missing": dict(_telemetry_state["core_features_missing"]),
        "decay_factor_stats": _get_decay_factor_stats(),
        "last_update": _telemetry_state.get("last_update")
    }


def _get_decay_factor_stats() -> Dict:
    """Get freshness decay factor statistics."""
    _load_telemetry()
    
    if not _telemetry_state["decay_factors"]:
        return {"count": 0, "min": 1.0, "max": 1.0, "mean": 1.0, "median": 1.0}
    
    freshness_values = [d["freshness"] for d in _telemetry_state["decay_factors"]]
    n = len(freshness_values)
    sorted_vals = sorted(freshness_values)
    
    def percentile(data, p):
        if n == 0:
            return 0.0
        k = (n - 1) * p
        f = int(k)
        c = k - f
        if f + 1 < n:
            return data[f] + c * (data[f + 1] - data[f])
        return data[f]
    
    return {
        "count": n,
        "min": round(min(freshness_values), 3),
        "max": round(max(freshness_values), 3),
        "mean": round(sum(freshness_values) / n, 3),
        "median": round(percentile(sorted_vals, 0.5), 3)
    }


# Initialize on import
_load_telemetry()
