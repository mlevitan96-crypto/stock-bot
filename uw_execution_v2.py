"""
UW Execution V2 - Motif-Aware Execution Engine
Routes orders with motif-based delay rules and sizing overlays
Supports paper mode for weekend burn-in testing
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from config.registry import CacheFiles, append_jsonl

ORDERS_LOG = CacheFiles.V2_ORDERS_LOG
AUDIT_LOG = CacheFiles.AUDIT_V2_EXECUTION

# Motif delay rules (seconds)
MOTIF_DELAY_RULES = {
    "staircase": {"min_steps": 3, "delay_sec": 60},
    "sweep_block_combo": {"immediate": True},
    "burst": {"delay_sec": 30},
    "whale_tracking": {"priority_boost": 0.15}
}

# Size overlays (multipliers)
SIZE_OVERLAYS = {
    "iv_skew_align": 0.25,
    "whale_persistence": 0.20,
    "toxicity_penalty": -0.25,
    "skew_conflict": -0.30
}

# Execution config
MAX_POSITIONS = 10
BASE_NOTIONAL_USD = 500
COOLDOWN_MIN = 20
PAPER_MODE = True

def audit(event: str, **kwargs):
    """Audit log"""
    rec = {"event": event, "ts": int(time.time()), "dt": datetime.utcnow().isoformat() + "Z"}
    rec.update(kwargs)
    append_jsonl(AUDIT_LOG, rec)

def compute_entry_delay(motif: Dict[str, Any]) -> int:
    """
    Compute entry delay based on motif patterns
    
    Args:
        motif: {staircase: bool, sweep_block: bool, burst: bool, whale_persistence: bool, ...}
    
    Returns:
        Delay in seconds (0 = immediate entry)
    """
    # Sweep/block combo: immediate entry
    if motif.get("sweep_block"):
        return 0
    
    # Staircase: wait for pattern confirmation
    if motif.get("staircase"):
        steps = motif.get("staircase_steps", 0)
        if steps < MOTIF_DELAY_RULES["staircase"]["min_steps"]:
            return MOTIF_DELAY_RULES["staircase"]["delay_sec"]
    
    # Burst: wait for intensity to settle
    if motif.get("burst"):
        return MOTIF_DELAY_RULES["burst"]["delay_sec"]
    
    # Default: no delay
    return 0

def compute_size_overlay(features: Dict[str, Any]) -> float:
    """
    Compute sizing multiplier based on feature alignment
    
    Args:
        features: {iv_skew_align: bool, whale_persistence: bool, toxicity: float, skew_conflict: bool, ...}
    
    Returns:
        Multiplier (-0.30 to +0.45)
    """
    overlay = 0.0
    
    # IV skew alignment boost
    if features.get("iv_skew_align", False):
        overlay += SIZE_OVERLAYS["iv_skew_align"]
    
    # Whale persistence boost
    if features.get("whale_persistence", False):
        overlay += SIZE_OVERLAYS["whale_persistence"]
    
    # Toxicity penalty
    if features.get("toxicity", 0.0) > 0.85:
        overlay += SIZE_OVERLAYS["toxicity_penalty"]
    
    # Skew conflict penalty
    if features.get("skew_conflict", False):
        overlay += SIZE_OVERLAYS["skew_conflict"]
    
    return max(-0.50, min(0.50, overlay))

def route_order(symbol: str, side: str, base_notional: float, delay_sec: int, 
                size_mult: float, paper_mode: bool = True) -> Dict[str, Any]:
    """
    Route order with motif-aware execution
    
    Returns:
        Order record with {symbol, side, notional, delay, status, ts, ...}
    """
    notional = base_notional * (1.0 + size_mult)
    notional = max(100, min(2000, notional))  # Clamp to reasonable range
    
    order = {
        "ts": int(time.time()),
        "dt": datetime.utcnow().isoformat() + "Z",
        "symbol": symbol,
        "side": side,
        "notional": round(notional, 2),
        "delay_sec": delay_sec,
        "size_mult": round(size_mult, 3),
        "paper_mode": paper_mode,
        "status": "queued" if delay_sec > 0 else "submitted"
    }
    
    # Log order
    append_jsonl(ORDERS_LOG, order)
    
    audit("order_routed", symbol=symbol, notional=notional, delay=delay_sec, paper=paper_mode)
    
    return order

def route_orders_from_clusters(clusters: List[Dict], current_positions: int, 
                                 max_positions: int = MAX_POSITIONS,
                                 base_notional: float = BASE_NOTIONAL_USD,
                                 paper_mode: bool = PAPER_MODE) -> List[Dict]:
    """
    Route orders for top clusters with available slots
    
    Args:
        clusters: Sorted list of V2 clusters (highest score first)
        current_positions: Number of existing positions
        max_positions: Max allowed positions
        base_notional: Base notional per position
        paper_mode: If True, log only (no actual execution)
    
    Returns:
        List of routed orders
    """
    slots = max(0, max_positions - current_positions)
    orders = []
    
    for i, cluster in enumerate(clusters[:slots]):
        symbol = cluster.get("symbol", "")
        sentiment = cluster.get("sentiment", "NEUTRAL")
        motif = cluster.get("motifs", {})
        features = cluster.get("features", {})
        
        # Determine side
        side = "BUY" if sentiment == "BULLISH" else "SELL" if sentiment == "BEARISH" else "SKIP"
        if side == "SKIP":
            continue
        
        # Compute delay and sizing
        delay = compute_entry_delay(motif)
        size_mult = compute_size_overlay(features)
        
        # Route order
        order = route_order(symbol, side, base_notional, delay, size_mult, paper_mode)
        order["cluster_rank"] = i + 1
        order["cluster_score"] = cluster.get("score", 0.0)
        orders.append(order)
    
    audit("orders_routed_from_clusters", count=len(orders), slots=slots)
    
    return orders

if __name__ == "__main__":
    # Test motif-aware execution
    test_clusters = [
        {
            "symbol": "AAPL",
            "sentiment": "BULLISH",
            "score": 3.5,
            "motifs": {"staircase": True, "staircase_steps": 2},
            "features": {"iv_skew_align": True, "toxicity": 0.2}
        },
        {
            "symbol": "MSFT",
            "sentiment": "BULLISH",
            "score": 3.2,
            "motifs": {"sweep_block": True},
            "features": {"whale_persistence": True}
        }
    ]
    
    orders = route_orders_from_clusters(test_clusters, current_positions=8, paper_mode=True)
    print(f"Routed {len(orders)} orders (paper mode)")
    for o in orders:
        print(f"  {o['symbol']}: ${o['notional']}, delay={o['delay_sec']}s, mult={o['size_mult']:.2f}")
