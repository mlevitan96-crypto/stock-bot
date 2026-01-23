#!/usr/bin/env python3
"""
Signal Weight Recommendations (advisory, computed)
=================================================

Produces transparent, read-only tuning suggestions based on signal performance.
It MUST NOT modify any live configs or weights.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(v: Any) -> float:
    try:
        if v is None:
            return 0.0
        return float(v)
    except Exception:
        return 0.0


def build_signal_weight_recommendations(*, signal_performance: Dict[str, Any]) -> Dict[str, Any]:
    """
    Structure:
    {
      "as_of_ts": "<ISO8601>",
      "recommendations": [
        { "signal": "<name>", "suggested_delta_weight": <number>, "confidence": "<low|medium|high>", "rationale": "<text>" }
      ]
    }
    """
    sigs = signal_performance.get("signals") if isinstance(signal_performance, dict) else None
    rows = sigs if isinstance(sigs, list) else []

    recs: List[Dict[str, Any]] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        name = str(r.get("name") or "").strip()
        if not name:
            continue
        n = int(r.get("trade_count") or 0)
        exp = float(_safe_float(r.get("expectancy_usd")))

        # Simple, transparent rule:
        # - Underperforming expectancy => negative delta
        # - Overperforming expectancy => positive delta
        # - Scale by magnitude, clamp to [-0.25, 0.25]
        mag = min(1.0, abs(exp) / 50.0)  # 50 USD/trade ~ "strong" signal
        base = 0.25 * mag
        suggested = base if exp > 0 else (-base if exp < 0 else 0.0)

        # Confidence based on sample size.
        if n >= 30:
            conf = "high"
        elif n >= 10:
            conf = "medium"
        else:
            conf = "low"

        rationale = f"expectancy_usd={round(exp, 4)} over {n} trades; suggestion scales with |expectancy| and clamps to ±0.25."
        recs.append(
            {
                "signal": name,
                "suggested_delta_weight": float(suggested),
                "confidence": conf,
                "rationale": rationale,
            }
        )

    # Stable ordering: strongest absolute suggestions first.
    recs_sorted = sorted(recs, key=lambda x: abs(_safe_float(x.get("suggested_delta_weight"))), reverse=True)
    return {"as_of_ts": _now_iso(), "recommendations": recs_sorted}

