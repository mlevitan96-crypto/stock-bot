#!/usr/bin/env python3
"""
Reconstruct directional intelligence as-of entry for each trade in the 30d cohort.

Uses:
- direction_intel_embed.intel_snapshot_entry when present (from telemetry)
- Otherwise: synthetic snapshot from regime_at_entry

Writes: reports/replay/direction_reconstruction_30d.jsonl (one JSON per trade).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _synthetic_snapshot_from_regime(regime_at_entry: str) -> Dict[str, Any]:
    """Build minimal intel snapshot from regime_at_entry for trades without direction_intel_embed."""
    r = (regime_at_entry or "").strip().lower()
    if r in ("crash", "panic"):
        vol_regime = "high"
        trend = "down"
        pre_sentiment = "bearish"
    elif r in ("bear", "risk_off"):
        vol_regime = "high"
        trend = "down"
        pre_sentiment = "bearish"
    elif r in ("bull", "risk_on"):
        vol_regime = "low"
        trend = "up"
        pre_sentiment = "bullish"
    else:
        vol_regime = "mid"
        trend = "flat"
        pre_sentiment = "neutral"

    return {
        "timestamp": "",
        "premarket_intel": {"premarket_sentiment": pre_sentiment},
        "postmarket_intel": {"postmarket_sentiment": "neutral"},
        "overnight_intel": {"overnight_return": 0.0 if trend == "flat" else (0.005 if trend == "up" else -0.005)},
        "futures_intel": {"ES_direction": trend, "futures_trend_strength": 0.005 if trend == "up" else (-0.005 if trend == "down" else 0.0)},
        "volatility_intel": {"vol_regime": vol_regime},
        "breadth_intel": {"adv_dec_ratio": 1.0 if trend == "flat" else (1.2 if trend == "up" else 0.8)},
        "sector_intel": {"sector_momentum": 0.0, "sector": "UNKNOWN"},
        "etf_flow_intel": {"SPY_flow": 0.0},
        "macro_intel": {"macro_sentiment_score": 0.0, "macro_risk_flag": vol_regime == "high"},
        "uw_intel": {"uw_premarket_sentiment": pre_sentiment},
        "regime_posture": {},
    }


def reconstruct_direction_components(trade: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], float, str]:
    """
    Reconstruct direction_components and direction_confidence for one trade.
    Returns (direction_components, direction_confidence, source).
    """
    embed = trade.get("direction_intel_embed") or {}
    snapshot = embed.get("intel_snapshot_entry") if isinstance(embed, dict) else None

    try:
        from src.intelligence.direction_intel import build_direction_components_from_snapshot
    except Exception:
        def build_direction_components_from_snapshot(s: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
            return {}

    if isinstance(snapshot, dict) and snapshot:
        components = build_direction_components_from_snapshot(snapshot)
        source = "telemetry"
    else:
        synthetic = _synthetic_snapshot_from_regime(trade.get("regime_at_entry") or "")
        components = build_direction_components_from_snapshot(synthetic)
        source = "synthetic_from_regime"

    # direction_confidence = average of |normalized_value| across components
    n = 0
    total = 0.0
    for c in (components or {}).values():
        if isinstance(c, dict):
            v = c.get("normalized_value") or c.get("contribution_to_direction_score")
            if v is not None:
                total += abs(float(v))
                n += 1
    direction_confidence = total / n if n else 0.0

    return (components or {}, direction_confidence, source)


def main() -> int:
    ap = argparse.ArgumentParser(description="Reconstruct direction intel for 30d cohort")
    ap.add_argument("--base-dir", default="", help="Repo root")
    ap.add_argument("--end-date", default="", help="End date YYYY-MM-DD")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--out", default="", help="Output path (default: reports/replay/direction_reconstruction_30d.jsonl)")
    args = ap.parse_args()
    base = Path(args.base_dir) if args.base_dir else REPO
    out_path = Path(args.out) if args.out else REPO / "reports" / "replay" / "direction_reconstruction_30d.jsonl"

    from scripts.replay.load_30d_backtest_cohort import load_30d_backtest_cohort
    from datetime import datetime, timezone
    end_date = args.end_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cohort, _ = load_30d_backtest_cohort(base, end_date, args.days)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    n_telemetry = 0
    with out_path.open("w", encoding="utf-8") as f:
        for t in cohort:
            components, confidence, source = reconstruct_direction_components(t)
            if source == "telemetry":
                n_telemetry += 1
            rec = {
                "trade_id": t.get("trade_id"),
                "symbol": t.get("symbol"),
                "entry_ts": t.get("entry_ts"),
                "exit_ts": t.get("exit_ts"),
                "side": t.get("side"),
                "realized_pnl": t.get("realized_pnl"),
                "regime_at_entry": t.get("regime_at_entry"),
                "direction_components": components,
                "direction_confidence": round(confidence, 4),
                "reconstruction_source": source,
            }
            f.write(json.dumps(rec, default=str) + "\n")

    print(f"Wrote {len(cohort)} reconstructions to {out_path} ({n_telemetry} from telemetry)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
