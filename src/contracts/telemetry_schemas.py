"""
Canonical telemetry schema contracts (validators) for data-integrity audits.

Defines required fields, types, and nesting for:
- master_trade_log.jsonl
- attribution.jsonl (entry + closed)
- exit_attribution.jsonl
- exit_event.jsonl
- intel_snapshot_entry.jsonl / intel_snapshot_exit.jsonl
- direction_event.jsonl

Canonical field names: direction, side, position_side, regime, timestamps.
Additive only; do not remove legacy fields without deprecation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _is_str(x: Any) -> bool:
    return isinstance(x, str)


def _is_num(x: Any) -> bool:
    return x is None or isinstance(x, (int, float))


def _is_dict(x: Any) -> bool:
    return isinstance(x, dict)


def _is_list(x: Any) -> bool:
    return isinstance(x, list)


# ---------------------------------------------------------------------------
# Master trade log (one record per trade at full close)
# ---------------------------------------------------------------------------
MASTER_TRADE_LOG_REQUIRED = ["trade_id", "symbol", "entry_ts", "exit_ts", "source"]


def validate_master_trade_log(rec: Dict[str, Any]) -> Tuple[bool, List[str]]:
    issues = []
    if not _is_dict(rec):
        return False, ["record is not a dict"]
    for k in MASTER_TRADE_LOG_REQUIRED:
        if k not in rec:
            issues.append(f"missing required '{k}'")
    if rec.get("trade_id") and not _is_str(rec["trade_id"]):
        issues.append("trade_id must be string")
    if rec.get("symbol") and not _is_str(rec["symbol"]):
        issues.append("symbol must be string")
    return len(issues) == 0, issues


# ---------------------------------------------------------------------------
# Attribution (entry open_* and closed)
# ---------------------------------------------------------------------------
ATTRIBUTION_REQUIRED = ["type", "ts"]
ATTRIBUTION_TYPE = "attribution"


def validate_attribution(rec: Dict[str, Any]) -> Tuple[bool, List[str]]:
    issues = []
    if not _is_dict(rec):
        return False, ["record is not a dict"]
    if rec.get("type") != ATTRIBUTION_TYPE:
        issues.append("type must be 'attribution'")
    if "ts" not in rec and "timestamp" not in rec:
        issues.append("missing ts or timestamp")
    return len(issues) == 0, issues


# ---------------------------------------------------------------------------
# Exit attribution (exit-side; must support direction_intel_embed)
# ---------------------------------------------------------------------------
EXIT_ATTRIBUTION_REQUIRED = ["symbol", "timestamp", "entry_timestamp", "exit_reason"]


def validate_exit_attribution(rec: Dict[str, Any]) -> Tuple[bool, List[str]]:
    issues = []
    if not _is_dict(rec):
        return False, ["record is not a dict"]
    for k in EXIT_ATTRIBUTION_REQUIRED:
        if k not in rec:
            issues.append(f"missing required '{k}'")
    # direction_intel_embed: optional but when present must have intel_snapshot_entry (dict, non-empty for readiness)
    embed = rec.get("direction_intel_embed")
    if embed is not None:
        if not _is_dict(embed):
            issues.append("direction_intel_embed must be dict")
        else:
            snap = embed.get("intel_snapshot_entry")
            if snap is not None and not _is_dict(snap):
                issues.append("direction_intel_embed.intel_snapshot_entry must be dict")
    return len(issues) == 0, issues


# ---------------------------------------------------------------------------
# Exit event (unified replay record)
# ---------------------------------------------------------------------------
EXIT_EVENT_REQUIRED = ["trade_id", "symbol", "entry_ts", "exit_ts", "exit_reason_code"]


def validate_exit_event(rec: Dict[str, Any]) -> Tuple[bool, List[str]]:
    issues = []
    if not _is_dict(rec):
        return False, ["record is not a dict"]
    for k in EXIT_EVENT_REQUIRED:
        if k not in rec:
            issues.append(f"missing required '{k}'")
    embed = rec.get("direction_intel_embed")
    if embed is not None and not _is_dict(embed):
        issues.append("direction_intel_embed must be dict")
    return len(issues) == 0, issues


# ---------------------------------------------------------------------------
# Intel snapshot (entry/exit) — must have enough for direction_readiness
# ---------------------------------------------------------------------------
INTEL_SNAPSHOT_ENTRY_CONTENT_KEYS = ["premarket_intel", "timestamp", "futures_intel", "volatility_intel"]


def validate_intel_snapshot_entry(rec: Dict[str, Any]) -> Tuple[bool, List[str]]:
    issues = []
    if not _is_dict(rec):
        return False, ["record is not a dict"]
    has_content = any(rec.get(k) for k in INTEL_SNAPSHOT_ENTRY_CONTENT_KEYS)
    if not has_content:
        issues.append("missing content: at least one of premarket_intel, timestamp, futures_intel, volatility_intel")
    return len(issues) == 0, issues


def validate_intel_snapshot_exit(rec: Dict[str, Any]) -> Tuple[bool, List[str]]:
    # Same content expectation as entry for consistency
    return validate_intel_snapshot_entry(rec)


# ---------------------------------------------------------------------------
# Direction event
# ---------------------------------------------------------------------------
DIRECTION_EVENT_REQUIRED = ["timestamp", "event_type", "direction_components"]


def validate_direction_event(rec: Dict[str, Any]) -> Tuple[bool, List[str]]:
    issues = []
    if not _is_dict(rec):
        return False, ["record is not a dict"]
    for k in DIRECTION_EVENT_REQUIRED:
        if k not in rec:
            issues.append(f"missing required '{k}'")
    if rec.get("direction_components") is not None and not _is_dict(rec["direction_components"]):
        issues.append("direction_components must be dict")
    return len(issues) == 0, issues


# ---------------------------------------------------------------------------
# Canonical field names (for writers: prefer these at top level)
# ---------------------------------------------------------------------------
CANONICAL_FIELDS = {
    "direction": "bullish | bearish or long | short",
    "side": "buy | sell",
    "position_side": "long | short",
    "regime": "e.g. NEUTRAL, RISK_OFF",
    "entry_ts": "ISO timestamp",
    "exit_ts": "ISO timestamp",
}


def check_canonical_fields(rec: Dict[str, Any], log_name: str) -> List[str]:
    """Report missing canonical top-level fields (advisory)."""
    missing = []
    if log_name in ("attribution", "exit_attribution", "exit_event"):
        for f in ("direction", "side", "position_side"):
            if f not in rec and not (f == "direction" and "position_side" in rec):
                missing.append(f)
    return missing
