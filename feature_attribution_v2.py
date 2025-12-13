"""
Feature Attribution V2 - Per-Feature Alpha Decomposition
Attributes P&L to individual features (iv_skew, smile_slope, toxicity, etc.)
Enables feature-level learning and optimization
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

ALPHA_ATTRIBUTION_V2 = Path("data/alpha_attribution_v2.jsonl")
FEATURE_PNL_ROLLUP = Path("state/pnl_feature_rollup.json")
AUDIT_LOG = Path("data/audit_v2_execution.jsonl")

# Feature weights for attribution
FEATURE_WEIGHTS = {
    "iv_skew": 0.15,
    "smile_slope": 0.10,
    "toxicity": -0.12,  # Negative = penalty
    "event_alignment": 0.08,
    "freshness": 0.05,
    "whale_persistence": 0.18,
    "cross_asset_agree": 0.12,
    "motif_bonus": 0.15,
    "regime_align": 0.07
}

def audit(event: str, **kwargs):
    """Audit log"""
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG.open("a") as f:
        rec = {"event": event, "ts": int(time.time()), "dt": datetime.utcnow().isoformat() + "Z"}
        rec.update(kwargs)
        f.write(json.dumps(rec) + "\n")

def decompose_alpha(fill: Dict[str, Any], cluster: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decompose P&L into feature contributions
    
    Args:
        fill: {symbol, entry_price, exit_price, qty, pnl, entry_ts, exit_ts, ...}
        cluster: {features, motifs, score, components, ...}
    
    Returns:
        Attribution record with per-feature P&L
    """
    pnl = fill.get("pnl", 0.0)
    features = cluster.get("features", {})
    components = cluster.get("components", {})
    motifs = cluster.get("motifs", {})
    
    # Normalize feature weights
    total_weight = sum(abs(w) for w in FEATURE_WEIGHTS.values())
    
    # Attribute P&L to each feature
    feature_pnl = {}
    for feature, weight in FEATURE_WEIGHTS.items():
        # Get feature value
        if feature == "motif_bonus":
            # Motif bonus is sum of detected motifs
            value = sum([
                motifs.get("staircase", False),
                motifs.get("sweep_block", False),
                motifs.get("burst", False),
                motifs.get("whale_persistence", False)
            ]) / 4.0
        elif feature == "cross_asset_agree":
            value = cluster.get("cross_asset", {}).get("agree_score", 0.0)
        elif feature == "regime_align":
            value = components.get("regime", 0.0) / max(components.get("flow", 1.0), 1.0)
        else:
            value = features.get(feature, 0.0)
        
        # Attribute proportional P&L
        contribution = (weight / total_weight) * value
        feature_pnl[feature] = round(pnl * contribution, 2)
    
    # Build attribution record
    attribution = {
        "ts": int(time.time()),
        "dt": datetime.utcnow().isoformat() + "Z",
        "symbol": fill.get("symbol", ""),
        "entry_ts": fill.get("entry_ts", 0),
        "exit_ts": fill.get("exit_ts", 0),
        "pnl_total": round(pnl, 2),
        "feature_pnl": feature_pnl,
        "features": features,
        "motifs": motifs,
        "score": cluster.get("score", 0.0),
        "sector": cluster.get("sector", "UNKNOWN")
    }
    
    return attribution

def capture_live_attribution(fills: List[Dict], clusters_map: Dict[str, Dict]) -> List[Dict]:
    """
    Capture live feature attribution for recent fills
    
    Args:
        fills: List of recent fills from executor
        clusters_map: Map of symbol -> cluster data
    
    Returns:
        List of attribution records
    """
    attributions = []
    
    for fill in fills:
        symbol = fill.get("symbol", "")
        
        # Match to cluster
        if symbol not in clusters_map:
            continue
        
        cluster = clusters_map[symbol]
        
        # Decompose alpha
        attr = decompose_alpha(fill, cluster)
        
        # Save attribution
        ALPHA_ATTRIBUTION_V2.parent.mkdir(parents=True, exist_ok=True)
        with ALPHA_ATTRIBUTION_V2.open("a") as f:
            f.write(json.dumps(attr) + "\n")
        
        attributions.append(attr)
    
    audit("feature_attribution_live", fills=len(fills), attributed=len(attributions))
    
    return attributions

def rollup_feature_pnl(lookback_days: int = 7) -> Dict[str, Any]:
    """
    Rollup P&L by feature over lookback window
    
    Returns:
        {
          "features": {feature_name: {total_pnl, count, avg_pnl, sharpe}, ...},
          "top_features": [sorted by avg_pnl],
          "worst_features": [sorted by avg_pnl]
        }
    """
    if not ALPHA_ATTRIBUTION_V2.exists():
        return {"features": {}, "top_features": [], "worst_features": []}
    
    cutoff_ts = int(time.time()) - (lookback_days * 86400)
    
    # Collect attributions
    feature_stats = {f: {"pnl": [], "count": 0} for f in FEATURE_WEIGHTS.keys()}
    
    with ALPHA_ATTRIBUTION_V2.open("r") as f:
        for line in f:
            try:
                attr = json.loads(line)
                if attr.get("ts", 0) < cutoff_ts:
                    continue
                
                for feature, pnl in attr.get("feature_pnl", {}).items():
                    if feature in feature_stats:
                        feature_stats[feature]["pnl"].append(pnl)
                        feature_stats[feature]["count"] += 1
            except:
                continue
    
    # Compute stats
    rollup = {}
    for feature, stats in feature_stats.items():
        if stats["count"] == 0:
            continue
        
        pnls = stats["pnl"]
        total = sum(pnls)
        avg = total / len(pnls)
        
        # Simple Sharpe approximation
        if len(pnls) > 1:
            import math
            variance = sum((p - avg) ** 2 for p in pnls) / (len(pnls) - 1)
            std = math.sqrt(variance)
            sharpe = (avg / std) if std > 0 else 0.0
        else:
            sharpe = 0.0
        
        rollup[feature] = {
            "total_pnl": round(total, 2),
            "count": len(pnls),
            "avg_pnl": round(avg, 2),
            "sharpe": round(sharpe, 3)
        }
    
    # Sort features
    sorted_features = sorted(rollup.items(), key=lambda x: x[1]["avg_pnl"], reverse=True)
    top_features = [f[0] for f in sorted_features[:3]]
    worst_features = [f[0] for f in sorted_features[-3:]]
    
    result = {
        "ts": int(time.time()),
        "dt": datetime.utcnow().isoformat() + "Z",
        "lookback_days": lookback_days,
        "features": rollup,
        "top_features": top_features,
        "worst_features": worst_features
    }
    
    # Save rollup
    FEATURE_PNL_ROLLUP.parent.mkdir(parents=True, exist_ok=True)
    with FEATURE_PNL_ROLLUP.open("w") as f:
        json.dump(result, f, indent=2)
    
    audit("feature_pnl_rollup", features=len(rollup), lookback_days=lookback_days)
    
    return result

if __name__ == "__main__":
    # Test feature attribution
    test_fill = {
        "symbol": "AAPL",
        "entry_price": 180.0,
        "exit_price": 182.0,
        "qty": 10,
        "pnl": 20.0,
        "entry_ts": int(time.time()) - 3600,
        "exit_ts": int(time.time())
    }
    
    test_cluster = {
        "symbol": "AAPL",
        "score": 3.5,
        "features": {"iv_skew": 0.12, "toxicity": 0.3, "whale_persistence": True},
        "motifs": {"staircase": True, "burst": False},
        "components": {"flow": 2.5, "regime": 0.3},
        "cross_asset": {"agree_score": 0.25},
        "sector": "TECH"
    }
    
    attr = decompose_alpha(test_fill, test_cluster)
    print(f"Attributed ${test_fill['pnl']:.2f} P&L across {len(attr['feature_pnl'])} features")
    print("Top feature contributors:")
    for feat, pnl in sorted(attr['feature_pnl'].items(), key=lambda x: x[1], reverse=True)[:3]:
        print(f"  {feat}: ${pnl:.2f}")
