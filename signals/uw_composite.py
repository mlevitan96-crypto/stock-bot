#!/usr/bin/env python3
"""
Composite UW Scoring + Attribution

Purpose:
- Compute a composite Unusual Whales (UW) score that fuses options flow conviction,
  dark pool sentiment/notional, insider modifiers, and regime weighting.
- Gate entries with a single threshold.
- Apply sizing and exit adjustments consistently.
- Log full UW attribution with every trade decision for postmortems.

How to use:
1) Import and call `compute_uw_composite_score(symbol, uw_cache, regime)`.
2) Use `should_enter(composite)` to gate entries.
3) Use `apply_sizing(base_contracts, composite)` to size positions.
4) Use `adjust_exit(open_position, composite)` to tighten stops if flow flips.
5) Call `log_uw_attribution(event_file, symbol, composite, decision, extra)` on signal/entry/exit.

Cache schema (per symbol), produced by uw_flow_daemon.py:
uw_cache[symbol] = {
  "sentiment": "BULLISH"|"BEARISH"|"NEUTRAL",
  "conviction": 0.0..1.0,
  "clusters": [...],
  "dark_pool": {
    "total_volume": int,
    "total_premium": float,
    "print_count": int,
    "avg_premium": float,
    "sentiment": "BULLISH"|"BEARISH"|"MIXED"
  },
  "insider": {
    "net_buys": int,
    "net_sells": int,
    "total_usd": float,
    "sentiment": "BULLISH"|"BEARISH"|"MIXED",
    "conviction_modifier": float
  }
}
"""

import json
import math
import time
from pathlib import Path
from typing import Dict, Any, Optional

# -----------------------
# Configuration
# -----------------------

PRIMARY_WATCHLIST = ["AAPL", "MSFT", "NVDA", "QQQ", "SPY", "TSLA"]

# Base weights for composite score
W_FLOW = 3.0        # options flow carries most weight
W_DARK = 1.25       # dark pool sentiment + notional provides confirmation
W_INSIDER = 0.75    # insider filings are slower-moving but valuable
W_REGIME = 0.35     # regime modulates overall influence

# Normalization caps
MAX_SCORE = 5.0
ENTRY_THRESHOLD = 2.5       # gate; trade only if composite > 2.5
CONVICTION_SIZE_UP = 0.20   # +20% sizing when strong and aligned
CONVICTION_SIZE_DOWN = 0.20 # -20% sizing when strong but opposite

# Strong signal thresholds
STRONG_CONVICTION = 0.70    # flow conviction considered strong
DARK_POOL_STRONG_NOTIONAL = 25_000_000.0  # strong DP notional in USD

# -----------------------
# Helpers
# -----------------------

def _to_num(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default

def _norm_sentiment(s: Optional[str]) -> str:
    s = (s or "NEUTRAL").upper()
    return s if s in ("BULLISH", "BEARISH", "NEUTRAL", "MIXED") else "NEUTRAL"

def _regime_factor(regime: Optional[str], aligned: bool, opposite: bool) -> float:
    r = (regime or "NEUTRAL").upper()
    if r == "RISK_ON":
        return 1.15 if aligned else (0.95 if opposite else 1.05)
    if r == "RISK_OFF":
        return 1.10 if opposite else (0.90 if aligned else 0.95)
    return 1.00

def _sign_from_sentiment(sent: str) -> int:
    if sent == "BULLISH": return +1
    if sent == "BEARISH": return -1
    return 0

def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

# -----------------------
# Composite score
# -----------------------

def compute_uw_composite_score(symbol: str, uw_cache: Dict[str, Any], regime: str) -> Dict[str, Any]:
    """
    Returns a composite dict:
    {
      "symbol": symbol,
      "score": float (0..5),
      "flow": {"sentiment":..., "conviction":...},
      "dark_pool": {"sentiment":..., "total_premium":..., "print_count":...},
      "insider": {"sentiment":..., "net_buys":..., "net_sells":..., "total_usd":..., "modifier":...},
      "aligned": bool,
      "opposite": bool,
      "notes": str
    }
    """
    sdata = uw_cache.get(symbol, {}) if uw_cache else {}
    
    # Handle string-encoded data (defensive)
    if isinstance(sdata, str):
        try:
            sdata = json.loads(sdata)
        except Exception:
            return None  # skip this signal safely
    
    if not isinstance(sdata, dict):
        return None  # unexpected type, skip safely
    
    flow_sent = _norm_sentiment(sdata.get("sentiment"))
    flow_conv = _clip(_to_num(sdata.get("conviction", 0.0)), 0.0, 1.0)

    dp = sdata.get("dark_pool", {}) or {}
    dp_sent = _norm_sentiment(dp.get("sentiment"))
    dp_prem = _to_num(dp.get("total_premium", 0.0))
    dp_count = int(_to_num(dp.get("print_count", 0)))

    ins = sdata.get("insider", {}) or {}
    ins_sent = _norm_sentiment(ins.get("sentiment"))
    ins_buys = int(_to_num(ins.get("net_buys", 0)))
    ins_sells = int(_to_num(ins.get("net_sells", 0)))
    ins_total = _to_num(ins.get("total_usd", 0.0))
    ins_mod = _clip(_to_num(ins.get("conviction_modifier", 0.0)), -0.05, 0.05)

    # Alignment/opposition signals
    aligned = (flow_sent in ("BULLISH", "BEARISH")) and (flow_sent == dp_sent)
    opposite = (flow_sent in ("BULLISH", "BEARISH")) and (dp_sent in ("BULLISH", "BEARISH")) and (flow_sent != dp_sent)

    # Flow base: scaled to W_FLOW
    flow_component = W_FLOW * flow_conv

    # Dark pool component: sentiment +/- and notional strength
    dp_strength = 0.0
    if dp_sent in ("BULLISH", "BEARISH"):
        base = 0.6
        # Notional scaling: 0..0.65 additional weight by log magnitude
        mag = max(1.0, dp_prem)
        log_mag = min(0.65, (math.log10(mag) / 7.0))
        dp_strength = base + log_mag
        dp_component = W_DARK * dp_strength
    else:
        dp_component = 0.25  # mild neutral/mixed contribution

    # Insider component: small boost/penalty
    if ins_sent == "BULLISH":
        insider_component = W_INSIDER * (0.50 + ins_mod)
    elif ins_sent == "BEARISH":
        insider_component = W_INSIDER * (0.50 - abs(ins_mod))
    else:
        insider_component = W_INSIDER * 0.25

    # Regime factor: amplify if aligned with regime risk characteristics
    flow_sign = _sign_from_sentiment(flow_sent)
    aligned_with_regime = (regime.upper() == "RISK_ON" and flow_sign == +1) or (regime.upper() == "RISK_OFF" and flow_sign == -1)
    opposite_to_regime = (regime.upper() == "RISK_ON" and flow_sign == -1) or (regime.upper() == "RISK_OFF" and flow_sign == +1)
    regime_component = W_REGIME * (_regime_factor(regime, aligned_with_regime, opposite_to_regime) - 1.0)

    # Penalize when flow and dark pool are strongly opposite
    opposition_penalty = 0.0
    if opposite and (flow_conv >= STRONG_CONVICTION or dp_prem >= DARK_POOL_STRONG_NOTIONAL):
        opposition_penalty = 0.35

    # Final composite score
    raw_score = flow_component + dp_component + insider_component + regime_component - opposition_penalty
    score = _clip(raw_score, 0.0, MAX_SCORE)

    # Notes
    reason = []
    reason.append(f"flow {flow_sent}({flow_conv:.2f})")
    reason.append(f"dp {dp_sent}(${int(dp_prem):,}, {dp_count} prints)")
    reason.append(f"ins {ins_sent}(buys={ins_buys}, sells={ins_sells}, mod={ins_mod:+.2f})")
    if aligned: reason.append("aligned(flow=dp)")
    if opposite: reason.append("opposite(flow≠dp)")
    if opposition_penalty > 0: reason.append(f"penalty({opposition_penalty:.2f})")
    if regime_component != 0: reason.append(f"regime_adj({regime_component:+.2f})")

    return {
        "symbol": symbol,
        "score": round(score, 3),
        "flow": {"sentiment": flow_sent, "conviction": round(flow_conv, 3)},
        "dark_pool": {"sentiment": dp_sent, "total_premium": round(dp_prem, 2), "print_count": dp_count},
        "insider": {"sentiment": ins_sent, "net_buys": ins_buys, "net_sells": ins_sells, "total_usd": round(ins_total, 2), "modifier": round(ins_mod, 3)},
        "aligned": aligned,
        "opposite": opposite,
        "notes": "; ".join(reason)
    }

# -----------------------
# Gating, sizing, exits
# -----------------------

def should_enter(composite: Dict[str, Any]) -> bool:
    """
    Entry gate:
    - Composite score must exceed threshold.
    - For PRIMARY_WATCHLIST, require options flow conviction >= STRONG_CONVICTION.
    """
    score_ok = composite["score"] > ENTRY_THRESHOLD
    flow_conv_ok = composite["flow"]["conviction"] >= STRONG_CONVICTION if composite["symbol"] in PRIMARY_WATCHLIST else True
    # Block if flow and dark pool are opposite and strong
    strong_dp = composite["dark_pool"]["total_premium"] >= DARK_POOL_STRONG_NOTIONAL
    opposition_block = composite["opposite"] and (composite["flow"]["conviction"] >= STRONG_CONVICTION or strong_dp)
    return bool(score_ok and flow_conv_ok and not opposition_block)

def apply_sizing(base_contracts: int, composite: Dict[str, Any]) -> int:
    """
    Sizing based on composite:
    - If options flow is strong and dark pool aligned → +20%.
    - If strong but opposite → -20%.
    """
    strong_flow = composite["flow"]["conviction"] >= STRONG_CONVICTION
    if strong_flow and composite["aligned"]:
        return max(1, int(round(base_contracts * (1.0 + CONVICTION_SIZE_UP))))
    if strong_flow and composite["opposite"]:
        return max(1, int(round(base_contracts * (1.0 - CONVICTION_SIZE_DOWN))))
    return base_contracts

def adjust_exit(open_position: Dict[str, Any], composite: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tighten trailing stops when composite signals conflict with current side:
    - If position is LONG and composite flow sentiment is BEARISH → tighten.
    - If position is SHORT and composite flow sentiment is BULLISH → tighten.
    """
    pos = dict(open_position or {})
    side = (pos.get("side") or "").upper()
    flow = composite["flow"]["sentiment"]
    conv = composite["flow"]["conviction"]
    if conv < 0.60:
        return pos
    if side == "LONG" and flow == "BEARISH":
        pos["trail_stop"] = round(float(pos.get("trail_stop", 1.0)) * 0.80, 4)
    elif side == "SHORT" and flow == "BULLISH":
        pos["trail_stop"] = round(float(pos.get("trail_stop", 1.0)) * 0.80, 4)
    return pos

# -----------------------
# Attribution logging
# -----------------------

def log_uw_attribution(event_file: Path, symbol: str, composite: Dict[str, Any], decision: str, extra: Optional[Dict[str, Any]] = None) -> None:
    """
    Log UW attribution for signals/entries/exits to a JSONL file.
    decision: "SIGNAL_EVAL"|"ENTRY_APPROVED"|"ENTRY_BLOCKED"|"EXIT_TIGHTENED"|"EXIT_NORMAL"
    """
    rec = {
        "event": "UW_ATTRIBUTION",
        "decision": decision,
        "symbol": symbol,
        "score": composite["score"],
        "flow_sentiment": composite["flow"]["sentiment"],
        "flow_conviction": composite["flow"]["conviction"],
        "dark_pool_sentiment": composite["dark_pool"]["sentiment"],
        "dark_pool_total_premium": composite["dark_pool"]["total_premium"],
        "insider_sentiment": composite["insider"]["sentiment"],
        "insider_net_buys": composite["insider"]["net_buys"],
        "insider_net_sells": composite["insider"]["net_sells"],
        "aligned": composite["aligned"],
        "opposite": composite["opposite"],
        "notes": composite["notes"],
        "_ts": int(time.time())
    }
    if extra:
        rec["extra"] = extra
    event_file.parent.mkdir(exist_ok=True)
    with event_file.open("a") as f:
        f.write(json.dumps(rec) + "\n")
