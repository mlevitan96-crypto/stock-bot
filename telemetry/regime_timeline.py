"""
Regime timeline (telemetry-only)
===============================

Builds an hour-by-hour "posture/regime timeline" summary for a given UTC day.

Best-effort sources:
- v1 attribution log (market_regime, gamma_regime) via attribution.context
- v2 shadow_trades candidates (market_regime, regime_label, posture, volatility_regime)
- state snapshots (regime_state / regime_posture_state / market_context_v2) for fallback

Contract:
- Read-only.
- Always emits a non-empty hourly array (24 entries).
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional


def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


def _iter_jsonl_text(text: str) -> Iterable[Dict[str, Any]]:
    for ln in (text or "").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
            if isinstance(obj, dict):
                yield obj
        except Exception:
            continue


def _parse_iso(ts: Any) -> Optional[datetime]:
    try:
        if ts is None:
            return None
        s = str(ts).strip().replace("Z", "+00:00")
        if "T" not in s and " " in s:
            s = s.replace(" ", "T", 1)
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _day_from_iso(ts: Any) -> Optional[str]:
    s = str(ts or "").strip()
    return s[:10] if len(s) >= 10 else None


def _dominant(counter: Counter, default: str = "") -> str:
    try:
        if not counter:
            return default
        return str(counter.most_common(1)[0][0])
    except Exception:
        return default


def build_regime_timeline(
    *,
    day: str,
    v1_attribution_log_path: str,
    shadow_trades_log_path: str,
    regime_state: Dict[str, Any] | None = None,
    posture_state: Dict[str, Any] | None = None,
    market_context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    # Hour bins for the day (UTC)
    by_hour: Dict[int, Dict[str, Counter]] = {
        h: {
            "v1_market_regime": Counter(),
            "v1_gamma_regime": Counter(),
            "v2_market_regime": Counter(),
            "v2_regime_label": Counter(),
            "v2_posture": Counter(),
            "v2_volatility_regime": Counter(),
        }
        for h in range(24)
    }

    # v1 attribution
    v1_text = _read_text(v1_attribution_log_path)
    for r in _iter_jsonl_text(v1_text):
        ts = r.get("ts") or r.get("timestamp")
        if _day_from_iso(ts) != day:
            continue
        dt = _parse_iso(ts)
        if not dt:
            continue
        h = int(dt.hour)
        ctx = r.get("context") if isinstance(r.get("context"), dict) else {}
        mr = str(ctx.get("market_regime") or "")
        gr = str(ctx.get("gamma_regime") or "")
        if mr:
            by_hour[h]["v1_market_regime"][mr] += 1
        if gr:
            by_hour[h]["v1_gamma_regime"][gr] += 1

    # v2 shadow candidates (richest per-tick regime/posture fields)
    v2_text = _read_text(shadow_trades_log_path)
    for r in _iter_jsonl_text(v2_text):
        ts = r.get("ts") or r.get("timestamp") or r.get("entry_ts")
        if _day_from_iso(ts) != day:
            continue
        if str(r.get("event_type") or "") != "shadow_trade_candidate":
            continue
        dt = _parse_iso(ts)
        if not dt:
            continue
        h = int(dt.hour)
        mr = str(r.get("market_regime") or "")
        rl = str(r.get("regime_label") or "")
        po = str(r.get("posture") or "")
        vr = str(r.get("volatility_regime") or "")
        if mr:
            by_hour[h]["v2_market_regime"][mr] += 1
        if rl:
            by_hour[h]["v2_regime_label"][rl] += 1
        if po:
            by_hour[h]["v2_posture"][po] += 1
        if vr:
            by_hour[h]["v2_volatility_regime"][vr] += 1

    # Fallbacks
    rs = regime_state if isinstance(regime_state, dict) else {}
    ps = posture_state if isinstance(posture_state, dict) else {}
    mc = market_context if isinstance(market_context, dict) else {}

    fallback_regime = str(rs.get("regime_label") or "")
    fallback_posture = str(ps.get("posture") or "")
    fallback_vol = str(rs.get("volatility_regime") or mc.get("volatility_regime") or "")

    hourly: List[Dict[str, Any]] = []
    for h in range(24):
        bucket = by_hour[h]
        hourly.append(
            {
                "hour_utc": int(h),
                "dominant_market_regime": _dominant(bucket["v2_market_regime"], default=_dominant(bucket["v1_market_regime"], default=fallback_regime)),
                "dominant_regime_label": _dominant(bucket["v2_regime_label"], default=fallback_regime),
                "dominant_posture": _dominant(bucket["v2_posture"], default=fallback_posture),
                "volatility_bucket": _dominant(bucket["v2_volatility_regime"], default=fallback_vol),
                "trend_bucket": "unknown",
                "feature_posture": str(ps.get("feature_posture") or ""),
                "equalizer_posture": str(ps.get("equalizer_posture") or ""),
                "counts": {k: int(sum(c.values())) for k, c in bucket.items()},
            }
        )

    day_summary = {
        "dominant_market_regime": _dominant(Counter([x["dominant_market_regime"] for x in hourly if x.get("dominant_market_regime")])),
        "dominant_posture": _dominant(Counter([x["dominant_posture"] for x in hourly if x.get("dominant_posture")])),
        "dominant_regime_label": _dominant(Counter([x["dominant_regime_label"] for x in hourly if x.get("dominant_regime_label")])),
        "volatility_bucket": _dominant(Counter([x["volatility_bucket"] for x in hourly if x.get("volatility_bucket")])),
        "trend_bucket": "unknown",
    }

    return {
        "_meta": {"date": str(day), "kind": "regime_timeline", "version": "2026-01-22_v1"},
        "day_summary": day_summary,
        "hourly": hourly,
        "notes": {
            "fallbacks_used": {
                "regime_state_present": bool(rs),
                "posture_state_present": bool(ps),
                "market_context_present": bool(mc),
            }
        },
    }

