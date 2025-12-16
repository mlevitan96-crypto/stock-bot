"""
Cross-Asset Confirmation Module - V2.1
Validates UW signals against correlated ETF movements (SPY, QQQ, sector ETFs)
Boosts aligned signals, penalizes divergent signals
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import requests
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv

load_dotenv()

CROSS_ASSET_MAP = Path("state/cross_asset_map.json")
AUDIT_LOG = Path("data/audit_v2_execution.jsonl")

CONFIRM_ASSETS = ["SPY", "QQQ", "XLF", "XLK", "XLE", "XLV"]
MIN_CONFIRM_SCORE = 0.15
MAX_LATENCY_MIN = 20
PENALTY_IF_DISAGREE = -0.2
BOOST_IF_AGREE = 0.15

SECTOR_ETF_MAP = {
    "TECH": "XLK",
    "FINANCE": "XLF",
    "ENERGY": "XLE",
    "HEALTHCARE": "XLV",
    "CONSUMER": "XLY",
    "INDUSTRIAL": "XLI"
}

def audit(event: str, **kwargs):
    """Audit log"""
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG.open("a") as f:
        rec = {"event": event, "ts": int(time.time()), "dt": datetime.utcnow().isoformat() + "Z"}
        rec.update(kwargs)
        f.write(json.dumps(rec) + "\n")

_alpaca_client = None

def _get_alpaca():
    """Lazy-load Alpaca API client"""
    global _alpaca_client
    if _alpaca_client is None:
        # Respect environment-configured Alpaca endpoint.
        # Default remains paper trading for safety.
        base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        _alpaca_client = tradeapi.REST(
            os.getenv("ALPACA_KEY"),
            os.getenv("ALPACA_SECRET"),
            base_url=base_url
        )
    return _alpaca_client

def get_etf_sentiment(etf: str, window_min: int = 20) -> Dict[str, Any]:
    """
    Get recent ETF price movement to determine sentiment
    Returns: {"etf": str, "sentiment": "BULLISH"|"BEARISH"|"NEUTRAL", "strength": float, "ts": int}
    """
    try:
        api = _get_alpaca()
        
        # Get recent bars (last window_min minutes)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=window_min)
        
        bars = api.get_bars(
            etf,
            "1Min",
            start=start_time.isoformat(),
            end=end_time.isoformat(),
            limit=window_min
        ).df
        
        if bars.empty or len(bars) < 5:
            # Insufficient data
            return {"etf": etf, "sentiment": "NEUTRAL", "strength": 0.0, "ts": int(time.time())}
        
        # Calculate price movement: (current - start) / start
        start_price = bars.iloc[0]['close']
        current_price = bars.iloc[-1]['close']
        pct_change = (current_price - start_price) / start_price
        
        # Determine sentiment and strength
        if pct_change > 0.002:  # +0.2% = BULLISH
            sentiment = "BULLISH"
            strength = min(1.0, abs(pct_change) * 100)  # Scale: 1% move = 1.0 strength
        elif pct_change < -0.002:  # -0.2% = BEARISH
            sentiment = "BEARISH"
            strength = min(1.0, abs(pct_change) * 100)
        else:
            sentiment = "NEUTRAL"
            strength = abs(pct_change) * 100
        
        return {
            "etf": etf,
            "sentiment": sentiment,
            "strength": round(strength, 3),
            "pct_change": round(pct_change * 100, 3),
            "ts": int(time.time())
        }
        
    except Exception as e:
        # Fallback on error
        audit("etf_sentiment_error", etf=etf, error=str(e))
        return {"etf": etf, "sentiment": "NEUTRAL", "strength": 0.0, "ts": int(time.time())}

def correlate_symbol_to_etf(symbol: str, sector: str) -> str:
    """Map symbol to relevant sector ETF"""
    # Primary: sector ETF
    if sector in SECTOR_ETF_MAP:
        return SECTOR_ETF_MAP[sector]
    
    # Fallback: QQQ for tech-like, SPY for others
    return "QQQ" if sector in ["TECH", "CONSUMER"] else "SPY"

def compute_agreement_score(signal_sentiment: str, etf_sentiment: str, etf_strength: float) -> float:
    """
    Compute agreement score between signal and ETF
    Returns: -1.0 to +1.0 (higher = more aligned)
    """
    if signal_sentiment == "NEUTRAL" or etf_sentiment == "NEUTRAL":
        return 0.0
    
    aligned = (signal_sentiment == etf_sentiment)
    score = etf_strength if aligned else -etf_strength
    return max(-1.0, min(1.0, score))

def build_cross_asset_map(clusters: List[Dict], latency_min: int = MAX_LATENCY_MIN) -> List[Dict]:
    """
    Build cross-asset confirmation map for all clusters
    
    Args:
        clusters: List of V2 clusters with {symbol, sentiment, sector, score, ...}
        latency_min: Max allowed latency for ETF data (minutes)
    
    Returns:
        List of clusters with added cross_asset field: {agree_score, score_adj, etf, etf_sentiment}
    """
    now_ts = int(time.time())
    confirmed_clusters = []
    
    for cluster in clusters:
        symbol = cluster.get("symbol", "")
        sentiment = cluster.get("sentiment", "NEUTRAL")
        sector = cluster.get("sector", "UNKNOWN")
        
        # Select relevant ETF
        etf = correlate_symbol_to_etf(symbol, sector)
        
        # Get ETF sentiment
        etf_data = get_etf_sentiment(etf, window_min=latency_min)
        etf_age_min = (now_ts - etf_data["ts"]) / 60.0
        
        # Skip if ETF data too stale
        if etf_age_min > latency_min:
            cluster["cross_asset"] = {
                "agree_score": 0.0,
                "score_adj": 0.0,
                "etf": etf,
                "etf_sentiment": "STALE",
                "note": f"etf_data_age={etf_age_min:.1f}min"
            }
            confirmed_clusters.append(cluster)
            continue
        
        # Compute agreement
        agree_score = compute_agreement_score(sentiment, etf_data["sentiment"], etf_data["strength"])
        
        # Determine adjustment
        score_adj = 0.0
        if agree_score >= MIN_CONFIRM_SCORE:
            score_adj = BOOST_IF_AGREE
        elif agree_score <= -MIN_CONFIRM_SCORE:
            score_adj = PENALTY_IF_DISAGREE
        
        cluster["cross_asset"] = {
            "agree_score": round(agree_score, 3),
            "score_adj": round(score_adj, 3),
            "etf": etf,
            "etf_sentiment": etf_data["sentiment"],
            "etf_strength": round(etf_data["strength"], 3)
        }
        
        confirmed_clusters.append(cluster)
    
    # Save map
    CROSS_ASSET_MAP.parent.mkdir(parents=True, exist_ok=True)
    with CROSS_ASSET_MAP.open("w") as f:
        json.dump({
            "ts": now_ts,
            "dt": datetime.utcnow().isoformat() + "Z",
            "count": len(confirmed_clusters),
            "clusters": confirmed_clusters
        }, f, indent=2)
    
    audit("cross_asset_confirmation_built", count=len(confirmed_clusters))
    
    return confirmed_clusters

def apply_cross_asset_adjustment(clusters: List[Dict]) -> List[Dict]:
    """
    Apply cross-asset score adjustments to clusters
    Modifies cluster["score"] based on cross_asset agreement
    """
    adjusted = []
    
    for cluster in clusters:
        if "cross_asset" not in cluster:
            adjusted.append(cluster)
            continue
        
        adj = cluster["cross_asset"].get("score_adj", 0.0)
        cluster["score"] = cluster.get("score", 0.0) + adj
        cluster["score"] = max(0.0, min(6.0, cluster["score"]))  # Clamp to valid range
        adjusted.append(cluster)
    
    return adjusted

if __name__ == "__main__":
    # Test cross-asset confirmation
    test_clusters = [
        {"symbol": "AAPL", "sentiment": "BULLISH", "sector": "TECH", "score": 3.2},
        {"symbol": "JPM", "sentiment": "BEARISH", "sector": "FINANCE", "score": 2.9},
        {"symbol": "XOM", "sentiment": "BULLISH", "sector": "ENERGY", "score": 3.5}
    ]
    
    confirmed = build_cross_asset_map(test_clusters)
    adjusted = apply_cross_asset_adjustment(confirmed)
    
    print(f"Confirmed {len(confirmed)} clusters with cross-asset validation")
    for c in adjusted:
        print(f"  {c['symbol']}: score={c['score']:.2f}, adj={c.get('cross_asset', {}).get('score_adj', 0):.2f}")
