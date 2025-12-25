#!/usr/bin/env python3
"""
TCA (Transaction Cost Analysis) Data Manager
Provides recent slippage data and TCA quality metrics for trading decisions.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

TCA_SUMMARY_LOG = Path("data/tca_summary.jsonl")

def get_recent_slippage(symbol: Optional[str] = None, lookback_hours: int = 24) -> float:
    """
    Get recent average slippage percentage from TCA data.
    
    Args:
        symbol: Optional symbol to filter by. If None, returns overall average.
        lookback_hours: How many hours back to look (default 24)
    
    Returns:
        Average slippage percentage (e.g., 0.003 = 0.3%)
    """
    if not TCA_SUMMARY_LOG.exists():
        return 0.003  # Default fallback
    
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    slippages = []
    
    try:
        with open(TCA_SUMMARY_LOG, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    rec_time_str = rec.get("timestamp", "")
                    if not rec_time_str:
                        continue
                    
                    # Parse timestamp
                    try:
                        if 'T' in rec_time_str:
                            rec_time = datetime.fromisoformat(rec_time_str.replace('Z', '+00:00'))
                        else:
                            continue
                    except:
                        continue
                    
                    if rec_time < cutoff_time:
                        continue
                    
                    # Check symbol filter
                    if symbol and rec.get("symbol") != symbol:
                        continue
                    
                    slippage = rec.get("slippage_pct")
                    if slippage is not None:
                        slippages.append(float(slippage))
                except:
                    continue
    except Exception:
        return 0.003  # Default fallback
    
    if not slippages:
        return 0.003  # Default fallback
    
    return sum(slippages) / len(slippages)

def get_tca_quality_score(symbol: Optional[str] = None, lookback_hours: int = 24) -> float:
    """
    Get TCA quality score (0.0 to 1.0) based on recent execution quality.
    
    Higher score = better execution quality (lower slippage, better fills)
    
    Args:
        symbol: Optional symbol to filter by
        lookback_hours: How many hours back to look
    
    Returns:
        Quality score: 0.0 (poor) to 1.0 (excellent)
    """
    if not TCA_SUMMARY_LOG.exists():
        return 0.0  # Unknown quality
    
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    slippages = []
    fill_ratios = []
    
    try:
        with open(TCA_SUMMARY_LOG, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    rec_time_str = rec.get("timestamp", "")
                    if not rec_time_str:
                        continue
                    
                    try:
                        if 'T' in rec_time_str:
                            rec_time = datetime.fromisoformat(rec_time_str.replace('Z', '+00:00'))
                        else:
                            continue
                    except:
                        continue
                    
                    if rec_time < cutoff_time:
                        continue
                    
                    if symbol and rec.get("symbol") != symbol:
                        continue
                    
                    slippage = rec.get("slippage_pct")
                    if slippage is not None:
                        slippages.append(float(slippage))
                    
                    # Fill ratio would be in order logs, not TCA summary
                    # For now, assume good quality if slippage is low
                except:
                    continue
    except Exception:
        return 0.0
    
    if not slippages:
        return 0.0
    
    avg_slippage = sum(slippages) / len(slippages)
    
    # Convert slippage to quality score
    # < 0.2% = excellent (1.0)
    # 0.2-0.4% = good (0.8)
    # 0.4-0.6% = fair (0.5)
    # > 0.6% = poor (0.2)
    if avg_slippage < 0.002:
        return 1.0
    elif avg_slippage < 0.004:
        return 0.8
    elif avg_slippage < 0.006:
        return 0.5
    else:
        return 0.2

def get_regime_forecast_modifier(current_regime: str) -> float:
    """
    Get regime forecast modifier based on current regime and forecast.
    
    This integrates with regime classification to provide forward-looking adjustments.
    
    Args:
        current_regime: Current market regime (e.g., "RISK_ON", "RISK_OFF", "mixed")
    
    Returns:
        Modifier value (typically -0.1 to +0.1)
    """
    # For now, use regime-based heuristics
    # Future: Integrate with actual regime forecasting system
    
    regime_modifiers = {
        "RISK_ON": 0.05,  # Slightly positive in risk-on
        "RISK_OFF": -0.05,  # Slightly negative in risk-off
        "high_vol_neg_gamma": -0.08,  # Negative in high vol negative gamma
        "low_vol_uptrend": 0.08,  # Positive in low vol uptrend
        "downtrend_flow_heavy": -0.06,  # Negative in downtrend
        "mixed": 0.0  # Neutral
    }
    
    return regime_modifiers.get(current_regime, 0.0)

def get_toxicity_sentinel_score(symbol: str, cluster_data: Dict) -> float:
    """
    Get toxicity sentinel score from cluster data.
    
    Args:
        symbol: Symbol being evaluated
        cluster_data: Cluster data containing toxicity information
    
    Returns:
        Toxicity score (0.0 to 1.0)
    """
    # Extract toxicity from cluster data
    toxicity = cluster_data.get("toxicity", 0) or cluster_data.get("features_for_learning", {}).get("toxicity", 0)
    
    # If not in cluster, compute from other signals
    if toxicity == 0:
        conviction = cluster_data.get("conviction", 0.5)
        dp_premium = cluster_data.get("dark_pool", {}).get("total_premium", 0) if isinstance(cluster_data.get("dark_pool"), dict) else 0
        
        # High conviction + large dark pool = potentially toxic
        base_toxicity = conviction * 0.7
        
        if dp_premium > 50_000_000:
            base_toxicity += 0.25
        elif dp_premium > 30_000_000:
            base_toxicity += 0.15
        
        toxicity = min(1.0, base_toxicity)
    
    return float(toxicity)

def track_execution_failure(symbol: str, failure_type: str, details: Dict = None):
    """
    Track per-symbol execution failures for learning.
    
    Args:
        symbol: Symbol that had execution failure
        failure_type: Type of failure (e.g., "fill_timeout", "slippage_exceeded", "rejected")
        details: Additional failure details
    """
    from config.registry import StateFiles
    
    failures_file = StateFiles.STATE_DIR / "execution_failures.jsonl"
    failures_file.parent.mkdir(parents=True, exist_ok=True)
    
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "failure_type": failure_type,
        "details": details or {}
    }
    
    with open(failures_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + "\n")

def get_recent_failures(symbol: str, lookback_hours: int = 24) -> int:
    """
    Get count of recent execution failures for a symbol.
    
    Args:
        symbol: Symbol to check
        lookback_hours: How many hours back to look
    
    Returns:
        Count of recent failures
    """
    from config.registry import StateFiles
    
    failures_file = StateFiles.STATE_DIR / "execution_failures.jsonl"
    if not failures_file.exists():
        return 0
    
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    count = 0
    
    try:
        with open(failures_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("symbol") != symbol:
                        continue
                    
                    rec_time_str = rec.get("timestamp", "")
                    if not rec_time_str:
                        continue
                    
                    try:
                        if 'T' in rec_time_str:
                            rec_time = datetime.fromisoformat(rec_time_str.replace('Z', '+00:00'))
                        else:
                            continue
                    except:
                        continue
                    
                    if rec_time >= cutoff_time:
                        count += 1
                except:
                    continue
    except Exception:
        return 0
    
    return count

