#!/usr/bin/env python3
"""
Adaptive Entry Thresholds + Theme-level UW Scoring

Purpose:
- Make composite UW entry thresholds self-adjusting based on rolling win rate and drawdown.
- Maintain per-bucket performance stats (2.5–3.0, 3.0–4.0, 4.0+).
- Apply theme-level composite adjustments using market-wide signals (e.g., SPY dark pool).
- Provide simple persistence to JSON for continuity across sessions.

Integration:
1) Instantiate AdaptiveGate at startup, load state.
2) On every trade close, call record_outcome(...) with composite score and P&L.
3) Each evaluation tick, call compute_dynamic_threshold(drawdown_pct) to get current gate.
4) Apply theme_adjustments(...) to modulate composite scores per symbol before gating.
5) Save state periodically or on shutdown.

Files:
- data/adaptive_gate_state.json
"""

from config.registry import StateFiles, CacheFiles, LogFiles, ConfigFiles
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from config.registry import StateFiles

STATE_FILE = StateFiles.ADAPTIVE_GATE_STATE

# Default bucket edges for composite UW scores
BUCKETS = [
    (2.50, 3.00),  # Low-High A
    (3.00, 4.00),  # Low-High B
    (4.00, 10.00), # Low-High C (cap above 5 to catch any overflows)
]

# Target performance bands for bucket-based adaptation
TARGETS = {
    (2.50, 3.00): {"min_win": 0.60, "drop_raise": 0.45, "raise_to": 3.00},
    (3.00, 4.00): {"min_win": 0.55, "drop_raise": 0.45, "raise_to": 3.25},
    (4.00, 10.00): {"min_win": 0.50, "drop_raise": 0.40, "raise_to": 3.50},
}

# Drawdown sensitivity rules
DD_RULES = [
    {"dd_gt": 8.0, "delta": +0.75},
    {"dd_gt": 6.0, "delta": +0.50},
    {"dd_gt": 4.0, "delta": +0.25},
    {"dd_lt": 2.0, "delta": -0.25},  # modest relaxation when healthy
]

# Base threshold
BASE_THRESHOLD = 2.50

# Minimum samples per bucket before adaptation decisions
MIN_SAMPLES_BUCKET = 30

# Theme penalties/bonuses caps
THEME_MAX_PENALTY = -0.50
THEME_MAX_BONUS = +0.25


class AdaptiveGate:
    """
    Self-adjusting entry threshold based on performance feedback.
    
    Tracks win rates across composite score buckets and adjusts entry
    requirements based on historical success rates and current drawdown.
    """
    
    def __init__(self, state_path: Path = STATE_FILE):
        self.state_path = state_path
        self.state: Dict[str, Any] = {
            "threshold": BASE_THRESHOLD,
            "buckets": {str(b): {"wins": 0, "losses": 0, "pnl": 0.0} for b in BUCKETS},
            "history": [],  # recent thresholds with context
            "last_update_ts": 0,
        }
        self.load()

    def load(self) -> None:
        """Load adaptive gate state from disk"""
        try:
            if self.state_path.exists():
                self.state = json.loads(self.state_path.read_text())
        except Exception:
            # keep defaults if corrupted
            pass

    def save(self) -> None:
        """Save adaptive gate state to disk"""
        try:
            self.state_path.parent.mkdir(exist_ok=True)
            self.state_path.write_text(json.dumps(self.state, indent=2))
        except Exception:
            pass

    def _bucket_key(self, score: float) -> str:
        """Determine which bucket a composite score belongs to"""
        for lo, hi in BUCKETS:
            if lo <= score < hi:
                return str((lo, hi))
        return str(BUCKETS[-1])

    def record_outcome(self, composite_score: float, pnl: float) -> None:
        """
        Record a trade outcome into the appropriate bucket.
        pnl > 0 → win, pnl <= 0 → loss
        """
        key = self._bucket_key(float(composite_score))
        b = self.state["buckets"].get(key)
        if not b:
            b = {"wins": 0, "losses": 0, "pnl": 0.0}
            self.state["buckets"][key] = b
        if pnl > 0:
            b["wins"] += 1
        else:
            b["losses"] += 1
        b["pnl"] += float(pnl)
        self.state["last_update_ts"] = int(time.time())

    def bucket_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Returns win rate and avg pnl per bucket.
        """
        stats = {}
        for k, v in self.state["buckets"].items():
            total = v["wins"] + v["losses"]
            win_rate = (v["wins"] / total) if total > 0 else 0.0
            avg_pnl = (v["pnl"] / total) if total > 0 else 0.0
            stats[k] = {"samples": total, "win_rate": round(win_rate, 4), "avg_pnl": round(avg_pnl, 2)}
        return stats

    def _apply_drawdown_rules(self, threshold: float, drawdown_pct: float) -> float:
        """Apply drawdown-based adjustments to threshold"""
        t = float(threshold)
        dd = float(drawdown_pct)
        # tighten in drawdown; relax slightly when healthy
        for rule in DD_RULES:
            if "dd_gt" in rule and dd > rule["dd_gt"]:
                t += rule["delta"]
            elif "dd_lt" in rule and dd < rule["dd_lt"]:
                t += rule["delta"]
        return max(2.50, min(4.25, round(t, 2)))  # clamp

    def compute_dynamic_threshold(self, drawdown_pct: float) -> float:
        """
        Adapt threshold based on bucket performance and drawdown.
        
        - If buckets underperform (win < drop_raise with sufficient samples), raise gate.
        - If buckets meet/exceed min_win, maintain base threshold.
        - Apply drawdown sensitivity on top.
        
        Returns current entry threshold.
        """
        base_t = BASE_THRESHOLD
        stats = self.bucket_stats()

        # Evaluate each bucket rule
        for (lo, hi), target in TARGETS.items():
            key = str((lo, hi))
            s = stats.get(key, {"samples": 0, "win_rate": 0.0})
            if s["samples"] >= MIN_SAMPLES_BUCKET:
                if s["win_rate"] < target["drop_raise"]:
                    base_t = max(base_t, target["raise_to"])  # raise gate
                elif s["win_rate"] >= target["min_win"]:
                    # keep or potentially relax modestly (handled by drawdown rules)
                    base_t = max(base_t, BASE_THRESHOLD)

        # Drawdown sensitivity
        final_t = self._apply_drawdown_rules(base_t, drawdown_pct)

        # Track changes
        if abs(final_t - self.state.get("threshold", BASE_THRESHOLD)) >= 0.01:
            self.state["threshold"] = final_t
            self.state["history"].append({
                "ts": int(time.time()),
                "threshold": final_t,
                "drawdown_pct": round(float(drawdown_pct), 2),
                "bucket_stats": stats
            })
            # keep history trimmed
            if len(self.state["history"]) > 200:
                self.state["history"] = self.state["history"][-200:]
            self.save()

        return final_t

    def should_enter(self, composite: Dict[str, Any]) -> bool:
        """
        Determine if a signal should enter based on composite score and adaptive threshold.
        
        Args:
            composite: Composite UW score dict with 'score' field
            
        Returns:
            True if signal passes entry gate, False otherwise
        """
        score = composite.get("score", 0.0)
        threshold = self.compute_dynamic_threshold(drawdown_pct=0.0)  # TODO: pass actual drawdown
        return float(score) >= float(threshold)


# ---------------------------
# Theme-level adjustments
# ---------------------------

def resolve_symbol_theme(symbol: str, theme_map: Dict[str, List[str]]) -> Optional[str]:
    """Find which theme a symbol belongs to"""
    for theme, symbols in theme_map.items():
        if symbol in symbols:
            return theme
    return None


def theme_adjustments(symbol: str,
                      composite_score: float,
                      uw_cache: Dict[str, Any],
                      theme_map: Dict[str, List[str]],
                      market_symbol: str = "SPY") -> float:
    """
    Apply theme-level composite adjustments based on market-wide UW sentiment.
    
    Example:
      - If SPY dark pool is BEARISH with heavy notional, penalize Tech Growth theme.
      - If insider is net BULLISH in Healthcare, add small bonus.
    
    Returns adjusted composite score (clamped to 0-5 range).
    """
    theme = resolve_symbol_theme(symbol, theme_map)
    if not theme:
        return composite_score

    # Market-wide signals (e.g., SPY or QQQ)
    ms = uw_cache.get(market_symbol, {}) or {}
    ms_dp = (ms.get("dark_pool") or {})
    ms_dp_sent = (ms_dp.get("sentiment") or "MIXED").upper()
    ms_dp_notional = float(ms_dp.get("total_premium", 0.0))

    # Theme heuristics
    adj = 0.0
    if theme in ("Tech Growth", "Cloud Software", "Semiconductors"):
        if ms_dp_sent == "BEARISH" and ms_dp_notional >= 50_000_000.0:
            adj += THEME_MAX_PENALTY  # strong sector headwind
    if theme in ("Healthcare",):
        ins = uw_cache.get(symbol, {}).get("insider", {}) or {}
        if (ins.get("sentiment") or "MIXED").upper() == "BULLISH":
            adj += min(THEME_MAX_BONUS, 0.25)

    adjusted = max(0.0, min(5.0, round(composite_score + adj, 3)))
    return adjusted
