#!/usr/bin/env python3
"""
Directional Intelligence — Canonical Components & Storage (TELEMETRY ONLY)
==========================================================================

Defines CANONICAL_DIRECTION_INTEL_COMPONENTS and writes:
- logs/intel_snapshot_entry.jsonl
- logs/intel_snapshot_exit.jsonl
- logs/direction_event.jsonl
Embeds snapshots into attribution/exit_attribution/exit_event via payloads only.
No live behavior changes.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Optional registry
try:
    from config.registry import Directories
    _logs = getattr(Directories, "LOGS", None)
    LOGS_DIR = _logs if isinstance(_logs, Path) else Path(_logs or "logs")
except Exception:
    LOGS_DIR = Path("logs")

# Canonical list for replay and conditioning
CANONICAL_DIRECTION_INTEL_COMPONENTS: List[str] = [
    "premarket_direction",
    "postmarket_direction",
    "overnight_direction",
    "futures_direction",
    "volatility_direction",
    "breadth_direction",
    "sector_direction",
    "etf_flow_direction",
    "macro_direction",
    "uw_direction",
]

# Default log paths (can override via env)
INTEL_SNAPSHOT_ENTRY = Path(os.environ.get("INTEL_SNAPSHOT_ENTRY", str(LOGS_DIR / "intel_snapshot_entry.jsonl")))
INTEL_SNAPSHOT_EXIT = Path(os.environ.get("INTEL_SNAPSHOT_EXIT", str(LOGS_DIR / "intel_snapshot_exit.jsonl")))
DIRECTION_EVENT_LOG = Path(os.environ.get("DIRECTION_EVENT_LOG", str(LOGS_DIR / "direction_event.jsonl")))


def _direction_from_sentiment(sentiment: str) -> str:
    s = (sentiment or "").strip().lower()
    if s in ("bullish", "up", "long"):
        return "up"
    if s in ("bearish", "down", "short"):
        return "down"
    return "flat"


def _contribution_to_direction_score(direction: str) -> float:
    if direction == "up":
        return 1.0
    if direction == "down":
        return -1.0
    return 0.0


def build_direction_components_from_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    From a full intel snapshot, build canonical direction components with
    raw_value, normalized_value, contribution_to_direction_score.
    """
    components: Dict[str, Dict[str, Any]] = {}
    pre = (snapshot.get("premarket_intel") or {})
    post = (snapshot.get("postmarket_intel") or {})
    overnight = (snapshot.get("overnight_intel") or {})
    futures = (snapshot.get("futures_intel") or {})
    vol = (snapshot.get("volatility_intel") or {})
    breadth = (snapshot.get("breadth_intel") or {})
    sector = (snapshot.get("sector_intel") or {})
    etf = (snapshot.get("etf_flow_intel") or {})
    macro = (snapshot.get("macro_intel") or {})
    uw = (snapshot.get("uw_intel") or {})

    def _dir_comp(name: str, raw: Any, direction: str) -> None:
        components[name] = {
            "raw_value": raw,
            "normalized_value": _contribution_to_direction_score(direction),
            "contribution_to_direction_score": _contribution_to_direction_score(direction),
        }

    _dir_comp("premarket_direction", pre.get("premarket_sentiment"), _direction_from_sentiment(str(pre.get("premarket_sentiment", ""))))
    _dir_comp("postmarket_direction", post.get("postmarket_sentiment"), _direction_from_sentiment(str(post.get("postmarket_sentiment", ""))))
    ret = overnight.get("overnight_return", 0.0)
    _dir_comp("overnight_direction", ret, "up" if ret > 0.0025 else ("down" if ret < -0.0025 else "flat"))
    _dir_comp("futures_direction", futures.get("futures_trend_strength", 0.0), futures.get("ES_direction", "flat"))
    _dir_comp("volatility_direction", vol.get("vol_regime"), "down" if vol.get("vol_regime") == "low" else ("up" if vol.get("vol_regime") == "high" else "flat"))
    _dir_comp("breadth_direction", breadth.get("adv_dec_ratio", 1.0), "up" if (breadth.get("adv_dec_ratio") or 1.0) > 1.1 else ("down" if (breadth.get("adv_dec_ratio") or 1.0) < 0.9 else "flat"))
    _dir_comp("sector_direction", sector.get("sector_momentum", 0.0), "up" if (sector.get("sector_momentum") or 0) > 0 else ("down" if (sector.get("sector_momentum") or 0) < 0 else "flat"))
    _dir_comp("etf_flow_direction", etf.get("SPY_flow", 0.0), "up" if (etf.get("SPY_flow") or 0) > 0 else ("down" if (etf.get("SPY_flow") or 0) < 0 else "flat"))
    _dir_comp("macro_direction", macro.get("macro_sentiment_score", 0.0), "up" if (macro.get("macro_sentiment_score") or 0) > 0.1 else ("down" if (macro.get("macro_sentiment_score") or 0) < -0.1 else "flat"))
    _dir_comp("uw_direction", uw.get("uw_premarket_sentiment", "neutral"), _direction_from_sentiment(str(uw.get("uw_premarket_sentiment", ""))))

    return components


def append_intel_snapshot_entry(payload: Dict[str, Any], symbol: Optional[str] = None) -> None:
    """Append one entry snapshot to logs/intel_snapshot_entry.jsonl. Never raises."""
    try:
        INTEL_SNAPSHOT_ENTRY.parent.mkdir(parents=True, exist_ok=True)
        rec = dict(payload)
        if symbol:
            rec["symbol"] = symbol
        rec["event"] = "entry"
        with INTEL_SNAPSHOT_ENTRY.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception:
        return


def append_intel_snapshot_exit(payload: Dict[str, Any], symbol: Optional[str] = None) -> None:
    """Append one exit snapshot to logs/intel_snapshot_exit.jsonl. Never raises."""
    try:
        INTEL_SNAPSHOT_EXIT.parent.mkdir(parents=True, exist_ok=True)
        rec = dict(payload)
        if symbol:
            rec["symbol"] = symbol
        rec["event"] = "exit"
        with INTEL_SNAPSHOT_EXIT.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception:
        return


def append_direction_event(
    components: Dict[str, Dict[str, Any]],
    event_type: str = "entry",
    symbol: Optional[str] = None,
    snapshot_ts: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Append one direction_event to logs/direction_event.jsonl. Never raises."""
    try:
        DIRECTION_EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)
        rec = {
            "timestamp": snapshot_ts or datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "symbol": symbol,
            "direction_components": dict(components),
            "metadata": dict(metadata or {}),
        }
        with DIRECTION_EVENT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception:
        return


def compute_intel_deltas(
    entry_snapshot: Dict[str, Any],
    exit_snapshot: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compute entry->exit deltas for futures, vol_regime, breadth, sector, macro, overnight_vol.
    For embedding in exit_event.jsonl and direction_event.jsonl.
    """
    deltas: Dict[str, Any] = {}
    try:
        e_f = (entry_snapshot.get("futures_intel") or {})
        x_f = (exit_snapshot.get("futures_intel") or {})
        deltas["futures_direction_delta"] = (x_f.get("futures_trend_strength") or 0.0) - (e_f.get("futures_trend_strength") or 0.0)

        e_v = (entry_snapshot.get("volatility_intel") or {})
        x_v = (exit_snapshot.get("volatility_intel") or {})
        deltas["vol_regime_entry"] = e_v.get("vol_regime", "mid")
        deltas["vol_regime_exit"] = x_v.get("vol_regime", "mid")

        e_b = (entry_snapshot.get("breadth_intel") or {})
        x_b = (exit_snapshot.get("breadth_intel") or {})
        deltas["breadth_adv_dec_delta"] = (x_b.get("adv_dec_ratio") or 1.0) - (e_b.get("adv_dec_ratio") or 1.0)

        e_s = (entry_snapshot.get("sector_intel") or {})
        x_s = (exit_snapshot.get("sector_intel") or {})
        deltas["sector_strength_delta"] = (x_s.get("sector_momentum") or 0.0) - (e_s.get("sector_momentum") or 0.0)

        e_m = (entry_snapshot.get("macro_intel") or {})
        x_m = (exit_snapshot.get("macro_intel") or {})
        deltas["macro_risk_entry"] = e_m.get("macro_risk_flag", False)
        deltas["macro_risk_exit"] = x_m.get("macro_risk_flag", False)

        e_o = (entry_snapshot.get("overnight_intel") or {})
        x_o = (exit_snapshot.get("overnight_intel") or {})
        deltas["overnight_volatility_delta"] = (x_o.get("overnight_volatility") or 0.0) - (e_o.get("overnight_volatility") or 0.0)
    except Exception:
        pass
    return deltas


def build_embed_payload_for_attribution(
    snapshot: Dict[str, Any],
    direction_components: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Payload to embed in attribution.jsonl (telemetry only)."""
    return {
        "intel_snapshot": snapshot,
        "direction_intel_components": direction_components,
        "canonical_direction_components": CANONICAL_DIRECTION_INTEL_COMPONENTS,
    }


def build_embed_payload_for_exit(
    entry_snapshot: Dict[str, Any],
    exit_snapshot: Dict[str, Any],
    exit_direction_components: Dict[str, Dict[str, Any]],
    intel_deltas: Dict[str, Any],
) -> Dict[str, Any]:
    """Payload to embed in exit_attribution.jsonl and exit_event.jsonl (telemetry only)."""
    return {
        "intel_snapshot_entry": entry_snapshot,
        "intel_snapshot_exit": exit_snapshot,
        "direction_intel_components_exit": exit_direction_components,
        "intel_deltas": intel_deltas,
        "canonical_direction_components": CANONICAL_DIRECTION_INTEL_COMPONENTS,
    }


# ---------------------------------------------------------------------------
# Entry snapshot state (for exit-time deltas)
# ---------------------------------------------------------------------------

def _position_intel_state_path() -> Path:
    try:
        from config.registry import Directories
        return getattr(Directories, "STATE", Path("state")) / "position_intel_snapshots.json"
    except Exception:
        return Path("state/position_intel_snapshots.json")


def _load_position_intel_state() -> Dict[str, Any]:
    path = _position_intel_state_path()
    try:
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_position_intel_state(data: Dict[str, Any]) -> None:
    try:
        path = _position_intel_state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception:
        pass


def _normalize_entry_ts_for_key(entry_ts: str) -> str:
    """Canonical key part: first 19 chars, Z normalized to +00:00 for consistency."""
    s = (str(entry_ts or "").replace("Z", "+00:00"))[:19]
    return s if s else ""


def store_entry_snapshot_for_position(symbol: str, entry_ts: str, snapshot: Dict[str, Any]) -> None:
    """Store entry intel snapshot keyed by symbol:entry_ts for later delta at exit. Never raises."""
    try:
        if not isinstance(snapshot, dict) or not snapshot:
            return
        norm_ts = _normalize_entry_ts_for_key(entry_ts)
        key = f"{str(symbol).upper()}:{norm_ts}"
        state = _load_position_intel_state()
        state[key] = {"symbol": symbol, "entry_ts": entry_ts, "snapshot": snapshot}
        _save_position_intel_state(state)
    except Exception:
        pass


def load_entry_snapshot_for_position(symbol: str, entry_ts: str) -> Optional[Dict[str, Any]]:
    """Load entry intel snapshot for symbol+entry_ts. Returns None if missing. Never raises."""
    try:
        state = _load_position_intel_state()
        if not state:
            return None
        sym_upper = str(symbol).upper()
        # Primary key: symbol:entry_ts[:19] (normalized)
        norm_ts = _normalize_entry_ts_for_key(entry_ts)
        key = f"{sym_upper}:{norm_ts}"
        rec = state.get(key)
        if isinstance(rec, dict) and "snapshot" in rec and rec.get("snapshot"):
            return rec["snapshot"]
        # Alternate key (no normalization)
        key2 = f"{sym_upper}:{str(entry_ts)[:19]}"
        if key2 != key:
            rec = state.get(key2)
            if isinstance(rec, dict) and "snapshot" in rec and rec.get("snapshot"):
                return rec["snapshot"]
        # Fallback: match by symbol and date prefix
        ts_prefix = str(entry_ts)[:10]
        for k, v in state.items():
            if k.startswith(f"{sym_upper}:") and isinstance(v, dict):
                ets = str(v.get("entry_ts") or k.split(":", 1)[-1])[:10]
                if ets == ts_prefix:
                    snap = v.get("snapshot")
                    if isinstance(snap, dict) and snap:
                        return snap
    except Exception:
        pass
    return None


def prune_position_intel_snapshots(max_age_days: int = 30) -> None:
    """Remove entries older than max_age_days from state/position_intel_snapshots.json. Never raises."""
    try:
        from datetime import datetime, timezone, timedelta
        state = _load_position_intel_state()
        if not state:
            return
        cutoff = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).isoformat()[:19]
        to_drop = []
        for k, v in state.items():
            if not isinstance(v, dict):
                to_drop.append(k)
                continue
            ets = (v.get("entry_ts") or k.split(":", 1)[-1] if ":" in k else "")[:19]
            if ets and ets < cutoff:
                to_drop.append(k)
        for k in to_drop:
            state.pop(k, None)
        if to_drop:
            _save_position_intel_state(state)
    except Exception:
        pass


def capture_entry_intel_telemetry(
    api: Any = None,
    symbol: Optional[str] = None,
    market_context: Optional[Dict] = None,
    regime_posture: Optional[Dict] = None,
    symbol_risk: Optional[Dict] = None,
    entry_ts: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build entry intel snapshot, write to intel_snapshot_entry.jsonl and direction_event.jsonl,
    store snapshot for exit deltas. Returns embed payload for attribution (telemetry only).
    """
    try:
        from src.intelligence.intel_sources import build_full_intel_snapshot
        snapshot = build_full_intel_snapshot(
            api=api, symbol=symbol, market_context=market_context,
            regime_posture=regime_posture, symbol_risk=symbol_risk,
        )
        components = build_direction_components_from_snapshot(snapshot)
        append_intel_snapshot_entry(snapshot, symbol)
        append_direction_event(components, "entry", symbol, snapshot.get("timestamp"), {"source": "direction_intel"})
        if symbol and entry_ts:
            store_entry_snapshot_for_position(symbol, entry_ts, snapshot)
        return build_embed_payload_for_attribution(snapshot, components)
    except Exception:
        return {}


def capture_exit_intel_telemetry(
    api: Any = None,
    symbol: Optional[str] = None,
    entry_ts: Optional[str] = None,
    market_context: Optional[Dict] = None,
    regime_posture: Optional[Dict] = None,
    symbol_risk: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Build exit intel snapshot, load entry snapshot if available, compute deltas,
    write to intel_snapshot_exit.jsonl and direction_event.jsonl.
    Returns embed payload for exit_attribution/exit_event (telemetry only).
    """
    try:
        from src.intelligence.intel_sources import build_full_intel_snapshot
        if market_context is None or regime_posture is None:
            try:
                from structural_intelligence.market_context_v2 import read_market_context_v2
                if market_context is None:
                    market_context = read_market_context_v2()
            except Exception:
                pass
            try:
                from structural_intelligence.regime_posture_v2 import read_regime_posture_state
                if regime_posture is None:
                    regime_posture = read_regime_posture_state()
            except Exception:
                pass
        exit_snapshot = build_full_intel_snapshot(
            api=api, symbol=symbol, market_context=market_context,
            regime_posture=regime_posture, symbol_risk=symbol_risk,
        )
        entry_snapshot = load_entry_snapshot_for_position(symbol or "", entry_ts or "") if (symbol and entry_ts) else {}
        if not entry_snapshot:
            entry_snapshot = exit_snapshot  # no delta
        deltas = compute_intel_deltas(entry_snapshot, exit_snapshot)
        exit_components = build_direction_components_from_snapshot(exit_snapshot)
        append_intel_snapshot_exit(exit_snapshot, symbol)
        append_direction_event(
            exit_components, "exit", symbol, exit_snapshot.get("timestamp"),
            {"intel_deltas": deltas, "source": "direction_intel"},
        )
        embed = build_embed_payload_for_exit(
            entry_snapshot, exit_snapshot, exit_components, deltas,
        )
        prune_position_intel_snapshots(max_age_days=30)
        return embed
    except Exception:
        # Defensive: return minimal embed so exit_attribution still has non-empty direction_intel_embed
        try:
            ts = datetime.now(timezone.utc).isoformat()
            minimal = {"timestamp": ts, "premarket_intel": {}, "postmarket_intel": {}}
            return build_embed_payload_for_exit(
                minimal, minimal, {}, {},
            )
        except Exception:
            return {"intel_snapshot_entry": {"timestamp": datetime.now(timezone.utc).isoformat()}, "intel_snapshot_exit": {"timestamp": datetime.now(timezone.utc).isoformat()}}
