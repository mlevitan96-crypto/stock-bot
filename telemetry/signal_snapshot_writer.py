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
        src = sources.get(c, "artifact_or_computed") or "artifact_or_computed"
        present = contrib is not None and (isinstance(contrib, (int, float)) and contrib != 0 or contrib)
        defaulted = not present and c in comps
        out[c] = {
            "present": bool(present),
            "defaulted": bool(defaulted),
            "value_bucket": _bucket_value(contrib) if contrib is not None else None,
            "contrib": round(float(contrib), 4) if isinstance(contrib, (int, float)) else None,
            "source": str(src)[:32] if src and str(src) != "unknown" else "artifact_or_computed",
        }
    return out


REQUIRED_KEYS = frozenset({
    "join_key", "join_key_fields", "timestamp_utc", "symbol", "lifecycle_event", "mode",
    "components", "uw_artifacts_used", "notes",
})


def validate_snapshot_record(rec: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Validate required keys present. Returns (ok, list of missing keys)."""
    missing = [k for k in REQUIRED_KEYS if k not in rec]
    for k in ("timestamp_utc", "symbol", "lifecycle_event", "mode"):
        if k in rec and rec[k] is None:
            missing.append(k)
    if "components" in rec and isinstance(rec["components"], dict):
        for comp_name, comp_val in rec["components"].items():
            if isinstance(comp_val, dict) and str(comp_val.get("source", "")).lower() == "unknown":
                if "reason" not in comp_val:
                    missing.append(f"components.{comp_name}.reason_for_unknown")
    return len(missing) == 0, missing


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
    timestamp_utc: Optional[str] = None,
    entry_timestamp_utc: Optional[str] = None,
    side: Optional[str] = None,
) -> Dict[str, Any]:
    """Build canonical snapshot record. Redact account/order IDs. timestamp_utc override for harness.
    For EXIT_DECISION/EXIT_FILL, pass entry_timestamp_utc and trade_id=live:SYMBOL:entry_ts for deterministic joins."""
    if lifecycle_event not in LIFECYCLE_EVENTS:
        lifecycle_event = "ENTRY_DECISION"
    if mode not in MODES:
        mode = "PAPER"

    components = build_component_map(composite_meta, enriched)
    ts = timestamp_utc or datetime.now(timezone.utc).isoformat()

    try:
        from telemetry.snapshot_join_keys import build_join_key
        join_key, join_key_fields = build_join_key(
            symbol=symbol,
            timestamp_utc=ts,
            trade_id=trade_id,
            lifecycle_event=lifecycle_event,
        )
    except Exception:
        join_key = f"{str(symbol).upper()}|{ts[:19]}"
        join_key_fields = {"symbol": symbol, "timestamp_utc": ts, "join_source": "fallback"}

    rec = {
        "join_key": join_key,
        "join_key_fields": join_key_fields,
        "timestamp_utc": ts,
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

    # Exit join keys for EXIT_DECISION and EXIT_FILL (deterministic join to master_trade_log / exit_attribution)
    if lifecycle_event in ("EXIT_DECISION", "EXIT_FILL"):
        try:
            from telemetry.snapshot_join_keys import build_exit_join_key
            entry_ts = entry_timestamp_utc or join_key_fields.get("entry_timestamp_utc")
            ejk, ejk_fields = build_exit_join_key(
                symbol=symbol,
                entry_timestamp_utc=entry_ts,
                exit_timestamp_utc=ts,
                position_id=position_id,
                trade_id=trade_id,
                side=side,
            )
            rec["exit_join_key"] = ejk
            rec["exit_join_key_fields"] = ejk_fields
            if entry_ts:
                rec["entry_timestamp_utc"] = entry_ts
        except Exception:
            rec["exit_join_key"] = rec.get("join_key", "")
            rec["exit_join_key_fields"] = dict(join_key_fields or {}, join_source="fallback")

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
    position_id: Optional[str] = None,
    uw_artifacts_used: Optional[Dict] = None,
    notes: Optional[List[str]] = None,
    timestamp_utc: Optional[str] = None,
    entry_timestamp_utc: Optional[str] = None,
    side: Optional[str] = None,
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
            position_id=position_id,
            uw_artifacts_used=uw_artifacts_used,
            notes=notes,
            timestamp_utc=timestamp_utc,
            entry_timestamp_utc=entry_timestamp_utc,
            side=side,
        )
        return write_snapshot(base_dir, rec)
    except Exception:
        return False
