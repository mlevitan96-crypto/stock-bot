"""
Signal Snapshot Writer — observability-only.
Captures component presence/defaulted/missing at decision time.
Output: logs/signal_snapshots.jsonl
Schema: timestamp_utc, symbol, lifecycle_event, mode, trade_id, regime_label,
        composite_score_v2, freshness_factor, components, uw_artifacts_used, notes.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

LOG_PATH = Path("logs/signal_snapshots.jsonl")
LIFECYCLE_EVENTS = frozenset({"ENTRY_DECISION", "ENTRY_FILL", "EXIT_DECISION", "EXIT_FILL"})
MODES = frozenset({"LIVE", "PAPER", "SHADOW"})


def _bucket_value(v: Any) -> str | float | None:
    """Bucket sensitive numeric values."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        if v < 0:
            return "negative"
        if v == 0:
            return 0.0
        if v < 1:
            return "low"
        if v < 3:
            return "medium"
        return "high"
    return str(v)[:64] if v else None


def build_component_map(composite_meta: Optional[Dict], enriched: Optional[Dict]) -> Dict[str, Dict]:
    """Build components dict: component_name -> {present, defaulted, value_bucket, contrib, source}."""
    COMPONENTS = [
        "flow", "dark_pool", "insider", "iv_skew", "smile", "whale", "event", "motif_bonus",
        "toxicity_penalty", "regime", "congress", "shorts_squeeze", "institutional", "market_tide",
        "calendar", "greeks_gamma", "ftd_pressure", "iv_rank", "oi_change", "etf_flow",
        "squeeze_score", "freshness_factor",
    ]
    comps = composite_meta.get("components", {}) if composite_meta else {}
    contribs = composite_meta.get("component_contributions", comps) if composite_meta else comps
    sources = composite_meta.get("component_sources", {}) if composite_meta else {}

    out: Dict[str, Dict] = {}
    for c in COMPONENTS:
        contrib = contribs.get(c)
        src = sources.get(c, "unknown")
        present = contrib is not None and (isinstance(contrib, (int, float)) and contrib != 0 or contrib)
        defaulted = not present and c in comps
        out[c] = {
            "present": bool(present),
            "defaulted": bool(defaulted),
            "value_bucket": _bucket_value(contrib) if contrib is not None else None,
            "contrib": round(float(contrib), 4) if isinstance(contrib, (int, float)) else None,
            "source": str(src)[:32],
        }
    return out


def build_snapshot_record(
    symbol: str,
    lifecycle_event: str,
    mode: str,
    composite_score_v2: Optional[float] = None,
    freshness_factor: Optional[float] = None,
    composite_meta: Optional[Dict] = None,
    enriched: Optional[Dict] = None,
    regime_label: Optional[str] = None,
    trade_id: Optional[str] = None,
    position_id: Optional[str] = None,
    uw_artifacts_used: Optional[Dict] = None,
    notes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build canonical snapshot record. Redact account/order IDs."""
    if lifecycle_event not in LIFECYCLE_EVENTS:
        lifecycle_event = "ENTRY_DECISION"
    if mode not in MODES:
        mode = "PAPER"

    components = build_component_map(composite_meta, enriched)

    rec = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "symbol": str(symbol).upper(),
        "lifecycle_event": lifecycle_event,
        "mode": mode,
        "trade_id": str(trade_id)[:64] if trade_id else None,
        "position_id": str(position_id)[:64] if position_id else None,
        "regime_label": regime_label,
        "composite_score_v2": round(float(composite_score_v2), 4) if composite_score_v2 is not None else None,
        "freshness_factor": round(float(freshness_factor), 4) if freshness_factor is not None else None,
        "components": components,
        "uw_artifacts_used": uw_artifacts_used or {},
        "notes": notes or [],
    }
    return rec


def write_snapshot(
    base_dir: Path,
    record: Dict[str, Any],
    log_path: Optional[Path] = None,
) -> bool:
    """
    Append record to logs/signal_snapshots.jsonl.
    Atomic append + failure-safe. Never raises.
    """
    path = (base_dir / (log_path or LOG_PATH)).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, default=str) + "\n"
    try:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            os.write(fd, line.encode("utf-8"))
        finally:
            os.close(fd)
        return True
    except Exception:
        return False


def write_snapshot_safe(
    base_dir: Path,
    symbol: str,
    lifecycle_event: str,
    mode: str = "PAPER",
    composite_score_v2: Optional[float] = None,
    freshness_factor: Optional[float] = None,
    composite_meta: Optional[Dict] = None,
    enriched: Optional[Dict] = None,
    regime_label: Optional[str] = None,
    trade_id: Optional[str] = None,
    uw_artifacts_used: Optional[Dict] = None,
    notes: Optional[List[str]] = None,
) -> bool:
    """Convenience: build and write. Never raises."""
    try:
        rec = build_snapshot_record(
            symbol=symbol,
            lifecycle_event=lifecycle_event,
            mode=mode,
            composite_score_v2=composite_score_v2,
            freshness_factor=freshness_factor,
            composite_meta=composite_meta,
            enriched=enriched,
            regime_label=regime_label,
            trade_id=trade_id,
            uw_artifacts_used=uw_artifacts_used,
            notes=notes,
        )
        return write_snapshot(base_dir, rec)
    except Exception:
        return False
