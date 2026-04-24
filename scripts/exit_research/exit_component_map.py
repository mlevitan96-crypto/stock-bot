#!/usr/bin/env python3
"""
Exit component map: given an exit attribution record, return canonical component vector,
raw signal values, regime, UW conviction, composite_at_entry, etc.
Maps v2_exit_components (exit_score_v2 / exit_pressure_v3) to canonical exit_* names.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

# Canonical component names (spec alignment)
CANONICAL_COMPONENTS = [
    "exit_flow_deterioration",
    "exit_volatility_spike",
    "exit_regime_shift",
    "exit_sentiment_reversal",
    "exit_gamma_collapse",
    "exit_dark_pool_reversal",
    "exit_insider_shift",
    "exit_sector_rotation",
    "exit_time_decay",
    "exit_microstructure_noise",
    "exit_score_deterioration",
]

# v2 (exit_score_v2) and v3 (exit_pressure_v3) key -> canonical
V2_TO_CANONICAL = {
    "flow_deterioration": "exit_flow_deterioration",
    "darkpool_deterioration": "exit_dark_pool_reversal",
    "sentiment_deterioration": "exit_sentiment_reversal",
    "score_deterioration": "exit_score_deterioration",
    "regime_shift": "exit_regime_shift",
    "sector_shift": "exit_sector_rotation",
    "vol_expansion": "exit_volatility_spike",
    "thesis_invalidated": "exit_sentiment_reversal",
    "earnings_risk": "exit_volatility_spike",
    "overnight_flow_risk": "exit_flow_deterioration",
}
V3_TO_CANONICAL = {
    "signal_deterioration": "exit_score_deterioration",
    "flow_reversal": "exit_flow_deterioration",
    "regime_risk": "exit_regime_shift",
    "position_risk": "exit_volatility_spike",
    "time_decay": "exit_time_decay",
    "profit_protection": "exit_microstructure_noise",
    "crowding_risk": "exit_microstructure_noise",
    "price_action": "exit_microstructure_noise",
}


def _exit_signal_id(key: str) -> str:
    return key if key.startswith("exit_") else f"exit_{key}"


def get_component_vector(rec: Dict[str, Any]) -> Dict[str, float]:
    """
    Returns component_name -> contribution_to_exit_score (0..1 style).
    Builds from v2_exit_components or attribution_components; normalizes keys to canonical.
    """
    out: Dict[str, float] = {c: 0.0 for c in CANONICAL_COMPONENTS}
    comp = rec.get("v2_exit_components") or {}
    # Also check list-style attribution (signal_id, contribution_to_score)
    attr_list = rec.get("attribution_components") or []
    if isinstance(attr_list, list):
        for a in attr_list:
            if isinstance(a, dict):
                sid = (a.get("signal_id") or a.get("name") or "").strip()
                contrib = float(a.get("contribution_to_score") or a.get("contribution") or 0)
                if sid:
                    canon = V2_TO_CANONICAL.get(sid.replace("exit_", "")) or (
                        sid if sid in CANONICAL_COMPONENTS else _exit_signal_id(sid) if not sid.startswith("exit_") else sid
                    )
                    if canon in out:
                        out[canon] = out.get(canon, 0) + contrib
    for k, v in comp.items():
        if v is None:
            continue
        try:
            val = float(v)
        except (TypeError, ValueError):
            continue
        canon = V2_TO_CANONICAL.get(k) or V3_TO_CANONICAL.get(k) or _exit_signal_id(k)
        if canon in out:
            out[canon] = out.get(canon, 0) + val
        elif canon not in out:
            out[canon] = val
    return {k: round(v, 6) for k, v in out.items()}


def get_raw_signal_values(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Raw signal values where available (entry_uw, exit_uw, regime, etc.)."""
    raw: Dict[str, Any] = {}
    raw["entry_uw"] = rec.get("entry_uw") or {}
    raw["exit_uw"] = rec.get("exit_uw") or {}
    raw["entry_regime"] = rec.get("entry_regime") or ""
    raw["exit_regime"] = rec.get("exit_regime") or ""
    raw["score_deterioration"] = rec.get("score_deterioration")
    raw["relative_strength_deterioration"] = rec.get("relative_strength_deterioration")
    raw["v2_exit_score"] = rec.get("v2_exit_score")
    return raw


def parse_signal_decay_from_reason(exit_reason: Optional[str]) -> Optional[float]:
    """Parse numeric threshold from exit_reason e.g. 'signal_decay(0.92)' -> 0.92."""
    if not exit_reason:
        return None
    m = re.search(r"signal_decay\s*\(\s*([\d.]+)\s*\)", str(exit_reason), re.I)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def exit_component_map(rec: Dict[str, Any]) -> Tuple[Dict[str, float], Dict[str, Any], str, float]:
    """
    Given an exit record, returns:
      (component_vector, raw_signal_values, entry_regime, composite_at_entry)
    """
    components = get_component_vector(rec)
    raw = get_raw_signal_values(rec)
    regime = str(rec.get("entry_regime") or raw.get("entry_regime") or "UNKNOWN").strip()
    composite = float(rec.get("entry_score") or rec.get("entry_v2_score") or 0)
    return components, raw, regime, composite


def sample_exits_interpretable(records: List[Dict[str, Any]], max_sample: int = 5) -> List[Dict[str, Any]]:
    """For a sample of exits, return component vectors and parsed decay; confirm non-empty and interpretable."""
    out: List[Dict[str, Any]] = []
    for r in records[: max_sample * 3]:
        if len(out) >= max_sample:
            break
        comp, raw, regime, composite = exit_component_map(r)
        decay = parse_signal_decay_from_reason(r.get("exit_reason"))
        total_contrib = sum(comp.values())
        out.append({
            "symbol": r.get("symbol"),
            "exit_reason": r.get("exit_reason"),
            "signal_decay_parsed": decay,
            "component_vector": comp,
            "total_component_sum": round(total_contrib, 4),
            "entry_regime": regime,
            "composite_at_entry": composite,
            "time_in_trade_minutes": r.get("time_in_trade_minutes"),
        })
    return out


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path
    ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(ROOT))
    exit_path = ROOT / "logs" / "exit_attribution.jsonl"
    if not exit_path.exists():
        print("No exit_attribution.jsonl found; run on droplet or with data.", file=sys.stderr)
        sys.exit(0)
    records = []
    for line in exit_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    sample = sample_exits_interpretable(records[-100:], max_sample=5)
    print(json.dumps(sample, indent=2, default=str))
