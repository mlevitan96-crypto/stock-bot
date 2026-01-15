#!/usr/bin/env python3
"""
UW Intelligence Enrichment V2
Adds advanced features: IV skew, smile slope, whale persistence, event alignment, 
toxicity detection, temporal motifs, and burst intensity analysis.
"""

import json
import math
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque

ENRICHED_LOG = Path("data/uw_flow_enriched.jsonl")
MOTIF_STATE = Path("state/uw_motifs.json")
AUDIT_LOG = Path("data/audit_uw_upgrade.jsonl")

# SCORING PIPELINE FIX (Priority 1): Increased decay_min from 45 to 180 minutes
# See SIGNAL_SCORE_PIPELINE_AUDIT.md for details
# This reduces score decay from 50% after 45min to 50% after 180min
DECAY_MINUTES = 180
# Institutional Remediation Phase 3: aggressive half-life freshness to prevent "ghost signal" trading
FRESHNESS_HALF_LIFE_MINUTES = 15.0

def audit(event: str, **kwargs):
    """Log enrichment audit events"""
    AUDIT_LOG.parent.mkdir(exist_ok=True)
    with AUDIT_LOG.open("a") as f:
        f.write(json.dumps({
            "event": event,
            "ts": int(time.time()),
            "dt": datetime.utcnow().isoformat() + "Z",
            **kwargs
        }) + "\n")

class TemporalMotifDetector:
    """
    Detects temporal patterns in UW flow:
    - Staircase: Progressive conviction increase over time
    - Sweep/Block: Sudden large flow events
    - Burst: High-frequency cluster of trades
    - Persistence: Whale activity continuity
    """
    
    def __init__(self):
        self.history = defaultdict(lambda: deque(maxlen=20))  # Last 20 updates per symbol
        self.motif_cache = {}
    
    def update(self, symbol: str, data: Dict[str, Any]):
        """Add new data point to temporal history"""
        self.history[symbol].append({
            "ts": int(time.time()),
            "conviction": data.get("conviction", 0.0),
            "dark_pool_premium": data.get("dark_pool", {}).get("total_notional", 0) or data.get("dark_pool", {}).get("total_premium", 0),
            "sentiment": data.get("sentiment", "NEUTRAL")
        })
    
    def detect_staircase(self, symbol: str, min_steps: int = 3) -> Optional[Dict]:
        """
        Detect staircase pattern: progressive conviction increase
        Returns: {detected: bool, steps: int, slope: float}
        """
        hist = list(self.history[symbol])
        if len(hist) < min_steps:
            return {"detected": False, "steps": 0, "slope": 0.0}
        
        recent = hist[-min_steps:]
        convictions = [h["conviction"] for h in recent]
        
        # Check if monotonically increasing
        is_staircase = all(convictions[i] < convictions[i+1] for i in range(len(convictions)-1))
        
        if is_staircase:
            slope = (convictions[-1] - convictions[0]) / min_steps
            return {"detected": True, "steps": len(convictions), "slope": slope}
        
        return {"detected": False, "steps": 0, "slope": 0.0}
    
    def detect_sweep_block(self, symbol: str, threshold_premium: float = 10_000_000) -> Dict:
        """
        Detect sweep/block: sudden large dark pool print
        Returns: {detected: bool, premium: float, immediate: bool}
        """
        hist = list(self.history[symbol])
        if not hist:
            return {"detected": False, "premium": 0, "immediate": False}
        
        latest = hist[-1]
        premium = latest.get("dark_pool_premium", 0)
        
        if premium >= threshold_premium:
            # Check if this is sudden (vs average of previous)
            if len(hist) > 1:
                prev_avg = sum(h.get("dark_pool_premium", 0) for h in hist[-5:-1]) / max(1, len(hist)-1)
                immediate = premium > prev_avg * 2.0  # 2x spike
            else:
                immediate = True
            
            return {"detected": True, "premium": premium, "immediate": immediate}
        
        return {"detected": False, "premium": premium, "immediate": False}
    
    def detect_burst(self, symbol: str, window_sec: int = 300) -> Dict:
        """
        Detect burst intensity: high-frequency updates in short window
        Returns: {detected: bool, intensity: float, count: int}
        """
        hist = list(self.history[symbol])
        if len(hist) < 2:
            return {"detected": False, "intensity": 0.0, "count": 0}
        
        now = int(time.time())
        recent = [h for h in hist if now - h["ts"] <= window_sec]
        
        if len(recent) >= 5:  # 5+ updates in 5 minutes = burst
            intensity = len(recent) / (window_sec / 60)  # updates per minute
            return {"detected": True, "intensity": intensity, "count": len(recent)}
        
        return {"detected": False, "intensity": 0.0, "count": len(recent)}
    
    def detect_whale_persistence(self, symbol: str, min_duration_sec: int = 1800) -> Dict:
        """
        Detect whale persistence: sustained high conviction over time
        Returns: {detected: bool, duration_sec: int, avg_conviction: float}
        """
        hist = list(self.history[symbol])
        if len(hist) < 3:
            return {"detected": False, "duration_sec": 0, "avg_conviction": 0.0}
        
        # Check if conviction stayed above 0.70 for sustained period
        high_conv = [h for h in hist if h["conviction"] >= 0.70]
        
        if len(high_conv) >= 3:
            duration = high_conv[-1]["ts"] - high_conv[0]["ts"]
            avg_conv = sum(h["conviction"] for h in high_conv) / len(high_conv)
            
            if duration >= min_duration_sec:
                return {"detected": True, "duration_sec": duration, "avg_conviction": avg_conv}
        
        return {"detected": False, "duration_sec": 0, "avg_conviction": 0.0}

class UWEnricher:
    """
    Enriches raw UW cache data with advanced features
    """
    
    def __init__(self):
        self.motif_detector = TemporalMotifDetector()
    
    def compute_iv_term_skew(self, symbol: str, data: Dict) -> float:
        """
        IV term structure skew (simulated from flow conviction + sentiment)
        Positive = front-month IV > back-month (near-term event expected)
        Range: -0.15 to +0.15
        """
        conviction = data.get("conviction", 0.5)
        sentiment = data.get("sentiment", "NEUTRAL")
        
        # Simulate: high conviction + directional = positive skew
        base_skew = (conviction - 0.5) * 0.3  # -0.15 to +0.15
        
        if sentiment in ("BULLISH", "BEARISH"):
            base_skew *= 1.2  # Amplify for directional flow
        
        return max(-0.15, min(0.15, base_skew))
    
    def compute_smile_slope(self, symbol: str, data: Dict) -> float:
        """
        Option smile slope (simulated from dark pool sentiment alignment)
        Positive = OTM calls > OTM puts (bullish skew)
        Range: -0.10 to +0.10
        """
        flow_sent = data.get("sentiment", "NEUTRAL")
        dp_sent = data.get("dark_pool", {}).get("sentiment", "NEUTRAL")
        
        # Smile slope based on alignment
        if flow_sent == "BULLISH" and dp_sent == "BULLISH":
            return 0.08  # Strong bullish skew
        elif flow_sent == "BEARISH" and dp_sent == "BEARISH":
            return -0.08  # Strong bearish skew
        elif flow_sent != dp_sent and flow_sent != "NEUTRAL" and dp_sent != "NEUTRAL":
            return 0.0  # Conflicting = neutral
        else:
            return 0.02 if flow_sent == "BULLISH" else (-0.02 if flow_sent == "BEARISH" else 0.0)
    
    def compute_put_call_skew(self, symbol: str, data: Dict) -> float:
        """
        Put/Call volume skew
        >1.0 = more put volume (defensive/bearish)
        <1.0 = more call volume (aggressive/bullish)
        """
        sentiment = data.get("sentiment", "NEUTRAL")
        conviction = data.get("conviction", 0.5)
        
        # Simulate based on sentiment + conviction
        if sentiment == "BEARISH":
            return 1.0 + (conviction * 0.5)  # 1.0 to 1.5
        elif sentiment == "BULLISH":
            return 1.0 - (conviction * 0.4)  # 0.6 to 1.0
        else:
            return 1.0
    
    def compute_toxicity(self, symbol: str, data: Dict) -> float:
        """
        Order toxicity score (0-1): likelihood of informed/toxic flow
        High toxicity = smart money, but also means we're late
        Penalize very high toxicity (>0.85) as we may be on wrong side
        """
        conviction = data.get("conviction", 0.5)
        dp_premium = data.get("dark_pool", {}).get("total_notional", 0) or data.get("dark_pool", {}).get("total_premium", 0)
        
        # High conviction + large dark pool = potentially toxic
        base_toxicity = conviction * 0.7
        
        # Large dark pool premium increases toxicity
        if dp_premium > 30_000_000:
            base_toxicity += 0.15
        elif dp_premium > 50_000_000:
            base_toxicity += 0.25
        
        return min(1.0, base_toxicity)
    
    def compute_event_alignment(self, symbol: str, data: Dict) -> float:
        """
        Event alignment score: flow timing relative to known events
        (Simulated: checks if high conviction coincides with earnings/macro)
        Range: 0.0 to 1.0
        """
        # Simulate: if conviction is very high (>0.80), assume event alignment
        conviction = data.get("conviction", 0.5)
        
        if conviction >= 0.80:
            return 0.85  # Strong alignment
        elif conviction >= 0.70:
            return 0.60  # Moderate alignment
        else:
            return 0.20  # Weak/no alignment
    
    def compute_freshness(self, data: Dict, decay_min: int = None) -> float:
        """
        Data freshness score (1.0 = fresh, decays over time)
        Institutional Remediation Phase 3:
        freshness = 0.5 ** (age_min / 15)

        Note: decay_min param is retained only for backward compatibility; it is no longer used.
        """
        # CRITICAL FIX: Check both _last_update (from daemon) and last_update (legacy)
        last_update = data.get("_last_update", data.get("last_update", int(time.time())))
        age_sec = int(time.time()) - last_update
        age_min = age_sec / 60.0
        
        freshness = 0.5 ** (age_min / float(FRESHNESS_HALF_LIFE_MINUTES))
        # Clamp only to numerical bounds (no forced floor).
        return max(0.0, min(1.0, freshness))
    
    def enrich_symbol(self, symbol: str, raw_data: Dict, features: List[str]) -> Dict:
        """
        Enrich single symbol with requested features
        """
        enriched = raw_data.copy()
        
        # Update temporal motif detector
        self.motif_detector.update(symbol, raw_data)
        
        # Compute requested features
        if "iv_term_skew" in features:
            enriched["iv_term_skew"] = self.compute_iv_term_skew(symbol, raw_data)
        
        if "smile_slope" in features:
            enriched["smile_slope"] = self.compute_smile_slope(symbol, raw_data)
        
        if "put_call_skew" in features:
            enriched["put_call_skew"] = self.compute_put_call_skew(symbol, raw_data)
        
        if "toxicity" in features:
            enriched["toxicity"] = self.compute_toxicity(symbol, raw_data)
        
        if "event_alignment" in features:
            enriched["event_alignment"] = self.compute_event_alignment(symbol, raw_data)
        
        if "freshness" in features:
            enriched["freshness"] = self.compute_freshness(raw_data)
        
        # Motif detection
        if "staircase" in features:
            enriched["motif_staircase"] = self.motif_detector.detect_staircase(symbol)
        
        if "sweep_block" in features:
            enriched["motif_sweep_block"] = self.motif_detector.detect_sweep_block(symbol)
        
        if "burst_intensity" in features:
            enriched["motif_burst"] = self.motif_detector.detect_burst(symbol)
        
        if "whale_persistence" in features:
            enriched["motif_whale"] = self.motif_detector.detect_whale_persistence(symbol)
        
        return enriched
    
    def enrich_cache(self, raw_cache: Dict, features: List[str]) -> Dict:
        """
        Enrich entire UW cache with advanced features
        """
        enriched_cache = {}
        
        for symbol, data in raw_cache.items():
            # Skip metadata keys
            if symbol.startswith("_"):
                enriched_cache[symbol] = data
                continue
            
            # Handle string-encoded data
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    continue
            
            if not isinstance(data, dict):
                continue
            
            enriched_cache[symbol] = self.enrich_symbol(symbol, data, features)
        
        return enriched_cache

def apply_enrichment(cache_path: Path, features: List[str]) -> Dict:
    """
    Main enrichment entry point
    Reads raw cache, applies enrichment, writes enriched log
    """
    if not cache_path.exists():
        audit("uw_enrichment_skip", reason="cache_not_found")
        return {}
    
    # Load raw cache
    with cache_path.open("r") as f:
        raw_cache = json.load(f)
    
    # Enrich
    enricher = UWEnricher()
    enriched = enricher.enrich_cache(raw_cache, features)
    
    # Write enriched log
    ENRICHED_LOG.parent.mkdir(exist_ok=True)
    with ENRICHED_LOG.open("a") as f:
        f.write(json.dumps({
            "ts": int(time.time()),
            "dt": datetime.utcnow().isoformat() + "Z",
            "count": len([k for k in enriched if not k.startswith("_")]),
            "data": enriched
        }) + "\n")
    
    # Save motif state
    motif_state = {}
    for symbol, data in enriched.items():
        if symbol.startswith("_"):
            continue
        
        motif_state[symbol] = {
            "staircase": data.get("motif_staircase", {}),
            "sweep_block": data.get("motif_sweep_block", {}),
            "burst": data.get("motif_burst", {}),
            "whale": data.get("motif_whale", {})
        }
    
    MOTIF_STATE.parent.mkdir(exist_ok=True)
    with MOTIF_STATE.open("w") as f:
        json.dump(motif_state, f, indent=2)
    
    audit("uw_enrichment_complete", count=len(enriched), features=features)
    
    return enriched

def enrich_signal(symbol: str, uw_cache: Dict, market_regime: str) -> Dict:
    """
    Per-symbol enrichment for live trading
    Called by main.py on each signal
    """
    if symbol not in uw_cache:
        return {}
    
    data = uw_cache[symbol]
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            return {}
    
    if not isinstance(data, dict):
        return {}
    
    enricher = UWEnricher()
    features = [
        "iv_term_skew", "smile_slope", "put_call_skew",
        "toxicity", "event_alignment", "freshness",
        "staircase", "sweep_block", "burst_intensity", "whale_persistence"
    ]
    
    enriched_symbol = enricher.enrich_symbol(symbol, data, features)
    
    # CRITICAL: Include all cache data fields in enriched output for composite scoring
    # These are needed by compute_composite_score_v3
    # ROOT CAUSE FIX: Must include sentiment and conviction - these are required for flow_component calculation
    enriched_symbol["sentiment"] = data.get("sentiment", "NEUTRAL")
    enriched_symbol["conviction"] = data.get("conviction", 0.0)
    enriched_symbol["dark_pool"] = data.get("dark_pool", {})
    enriched_symbol["insider"] = data.get("insider", {})
    enriched_symbol["market_tide"] = data.get("market_tide", {})
    enriched_symbol["calendar"] = data.get("calendar", {})
    enriched_symbol["congress"] = data.get("congress", {})
    enriched_symbol["institutional"] = data.get("institutional", {})
    enriched_symbol["shorts"] = data.get("ftd", {})  # FTD data is stored as "ftd" in cache
    enriched_symbol["greeks"] = data.get("greeks", {})
    enriched_symbol["iv_rank"] = data.get("iv_rank", {})
    enriched_symbol["oi_change"] = data.get("oi_change", {})
    enriched_symbol["etf_flow"] = data.get("etf_flow", {})
    
    # SYNTHETIC SQUEEZE ENGINE: Compute if official squeeze data is missing
    squeeze_data = data.get("squeeze_score", {})
    if not squeeze_data or not squeeze_data.get("signals", 0):
        synthetic_squeeze = _compute_synthetic_squeeze(enriched_symbol, data)
        if synthetic_squeeze:
            enriched_symbol["squeeze_score"] = synthetic_squeeze
            enriched_symbol["synthetic_squeeze"] = True  # Flag to indicate synthetic
    
    return enriched_symbol

def _compute_synthetic_squeeze(enriched_symbol: Dict, data: Dict) -> Dict:
    """
    Compute synthetic squeeze score if official UW squeeze data is missing.
    Logic: (High OI Change + Negative Gamma + Bullish Flow) = Squeeze Potential
    
    Returns:
        Dict with squeeze_score structure: {signals: int, high_squeeze_potential: bool}
    """
    signals = 0
    high_squeeze = False
    
    # 1. Check OI Change (high OI change = institutional positioning)
    oi_data = data.get("oi_change", {}) or enriched_symbol.get("oi_change", {})
    net_oi = float(oi_data.get("net_oi_change", 0) or 0)
    if net_oi > 50000:  # High OI change
        signals += 1
    
    # 2. Check Gamma (negative gamma = squeeze setup)
    greeks_data = data.get("greeks", {}) or enriched_symbol.get("greeks", {})
    call_gamma = float(greeks_data.get("call_gamma", 0) or 0)
    put_gamma = float(greeks_data.get("put_gamma", 0) or 0)
    gamma_exposure = call_gamma - put_gamma
    if gamma_exposure < -100000:  # Negative gamma (squeeze setup)
        signals += 1
    
    # 3. Check Flow (bullish flow = buying pressure)
    sentiment = data.get("sentiment", "NEUTRAL")
    conviction = float(data.get("conviction", 0) or 0)
    if sentiment == "BULLISH" and conviction > 0.5:  # Strong bullish flow
        signals += 1
    
    # High squeeze potential if all 3 conditions met
    if signals >= 3:
        high_squeeze = True
    
    return {
        "signals": signals,
        "high_squeeze_potential": high_squeeze,
        "synthetic": True,
        "components": {
            "high_oi_change": net_oi > 50000,
            "negative_gamma": gamma_exposure < -100000,
            "bullish_flow": sentiment == "BULLISH" and conviction > 0.5
        }
    }

if __name__ == "__main__":
    # Test enrichment
    cache_file = Path("data/uw_flow_cache.json")
    features = [
        "iv_term_skew", "smile_slope", "put_call_skew",
        "toxicity", "event_alignment", "freshness",
        "staircase", "sweep_block", "burst_intensity", "whale_persistence"
    ]
    
    enriched = apply_enrichment(cache_file, features)
    print(f"Enriched {len(enriched)} symbols with {len(features)} features")
