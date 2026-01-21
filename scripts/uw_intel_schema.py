#!/usr/bin/env python3
"""
UW Intelligence Schema Validators (local + droplet sync)
=======================================================

Contract:
- Validators must be deterministic and side-effect free.
- Used by regression suite and droplet sync scripts.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _is_iso_ts(x: Any) -> bool:
    try:
        s = str(x)
        return "T" in s and ("+" in s or s.endswith("Z"))
    except Exception:
        return False


def validate_daily_universe(doc: Any) -> Tuple[bool, str]:
    if not isinstance(doc, dict):
        return False, "daily_universe: not a dict"
    meta = doc.get("_meta")
    if not isinstance(meta, dict):
        return False, "daily_universe: missing _meta"
    if not _is_iso_ts(meta.get("ts")):
        return False, "daily_universe: _meta.ts invalid"
    syms = doc.get("symbols")
    if not isinstance(syms, list):
        return False, "daily_universe: symbols not a list"
    for r in syms[:20]:
        if not isinstance(r, dict) or not r.get("symbol"):
            return False, "daily_universe: invalid symbol entry"
    return True, "ok"


def validate_core_universe(doc: Any) -> Tuple[bool, str]:
    # same schema as daily_universe
    return validate_daily_universe(doc)


def validate_premarket_intel(doc: Any) -> Tuple[bool, str]:
    if not isinstance(doc, dict):
        return False, "premarket_intel: not a dict"
    meta = doc.get("_meta")
    if not isinstance(meta, dict):
        return False, "premarket_intel: missing _meta"
    if not _is_iso_ts(meta.get("ts")):
        return False, "premarket_intel: _meta.ts invalid"
    if "uw_intel_version" not in meta:
        return False, "premarket_intel: missing _meta.uw_intel_version"
    syms = doc.get("symbols")
    if not isinstance(syms, dict):
        return False, "premarket_intel: symbols not dict"
    # validate a few entries
    for k in list(syms.keys())[:10]:
        v = syms.get(k)
        if not isinstance(v, dict):
            return False, "premarket_intel: symbol entry not dict"
        for req in ("flow_strength", "darkpool_bias", "sentiment"):
            if req not in v:
                return False, f"premarket_intel: missing {req}"
    return True, "ok"


def validate_postmarket_intel(doc: Any) -> Tuple[bool, str]:
    # same basic shape as premarket
    if not isinstance(doc, dict):
        return False, "postmarket_intel: not a dict"
    meta = doc.get("_meta")
    if not isinstance(meta, dict):
        return False, "postmarket_intel: missing _meta"
    if not _is_iso_ts(meta.get("ts")):
        return False, "postmarket_intel: _meta.ts invalid"
    if "uw_intel_version" not in meta:
        return False, "postmarket_intel: missing _meta.uw_intel_version"
    syms = doc.get("symbols")
    if not isinstance(syms, dict):
        return False, "postmarket_intel: symbols not dict"
    for k in list(syms.keys())[:10]:
        v = syms.get(k)
        if not isinstance(v, dict):
            return False, "postmarket_intel: symbol entry not dict"
        for req in ("sentiment",):
            if req not in v:
                return False, f"postmarket_intel: missing {req}"
    return True, "ok"


def validate_uw_usage_state(doc: Any) -> Tuple[bool, str]:
    if not isinstance(doc, dict):
        return False, "uw_usage_state: not a dict"
    if "date" not in doc or "calls_today" not in doc:
        return False, "uw_usage_state: missing date/calls_today"
    if not isinstance(doc.get("calls_today"), int):
        return False, "uw_usage_state: calls_today not int"
    if not isinstance(doc.get("minute_window"), list):
        return False, "uw_usage_state: minute_window not list"
    if not isinstance(doc.get("by_endpoint"), dict):
        return False, "uw_usage_state: by_endpoint not dict"
    return True, "ok"


def validate_daily_universe_v2(doc: Any) -> Tuple[bool, str]:
    # Same top-level shape, plus optional v2 context fields.
    ok, msg = validate_daily_universe(doc)
    if not ok:
        return False, f"daily_universe_v2: {msg}"
    meta = doc.get("_meta") if isinstance(doc, dict) else {}
    if not isinstance(meta, dict):
        return False, "daily_universe_v2: missing _meta"
    # v2 version should exist (may be empty during early rollout)
    if "version" not in meta:
        return False, "daily_universe_v2: missing _meta.version"
    return True, "ok"


def validate_regime_state(doc: Any) -> Tuple[bool, str]:
    if not isinstance(doc, dict):
        return False, "regime_state: not a dict"
    meta = doc.get("_meta")
    if not isinstance(meta, dict):
        return False, "regime_state: missing _meta"
    if not _is_iso_ts(meta.get("ts")):
        return False, "regime_state: _meta.ts invalid"
    if not isinstance(doc.get("regime_label"), str):
        return False, "regime_state: regime_label not str"
    try:
        float(doc.get("regime_confidence", 0.0))
    except Exception:
        return False, "regime_state: regime_confidence not numeric"
    return True, "ok"


def validate_uw_intel_pnl_summary(doc: Any) -> Tuple[bool, str]:
    if not isinstance(doc, dict):
        return False, "uw_intel_pnl_summary: not a dict"
    meta = doc.get("_meta")
    if not isinstance(meta, dict):
        return False, "uw_intel_pnl_summary: missing _meta"
    if not _is_iso_ts(meta.get("ts")):
        return False, "uw_intel_pnl_summary: _meta.ts invalid"
    if not isinstance(doc.get("by_feature"), dict):
        return False, "uw_intel_pnl_summary: by_feature not dict"
    return True, "ok"


def validate_intel_health_state(doc: Any) -> Tuple[bool, str]:
    if not isinstance(doc, dict):
        return False, "intel_health_state: not a dict"
    meta = doc.get("_meta")
    if not isinstance(meta, dict):
        return False, "intel_health_state: missing _meta"
    if not _is_iso_ts(meta.get("ts")):
        return False, "intel_health_state: _meta.ts invalid"
    if not isinstance(doc.get("checks"), list):
        return False, "intel_health_state: checks not list"
    return True, "ok"


def validate_uw_daemon_health_state(doc: Any) -> Tuple[bool, str]:
    if not isinstance(doc, dict):
        return False, "uw_daemon_health_state: not a dict"
    ts = doc.get("timestamp")
    if not _is_iso_ts(ts):
        return False, "uw_daemon_health_state: timestamp invalid"
    for k in ("pid_ok", "lock_ok", "poll_fresh", "crash_loop", "endpoint_errors"):
        if k not in doc:
            return False, f"uw_daemon_health_state: missing {k}"
        if not isinstance(doc.get(k), bool):
            return False, f"uw_daemon_health_state: {k} not bool"
    status = doc.get("status")
    if str(status) not in ("healthy", "warning", "critical"):
        return False, "uw_daemon_health_state: status invalid"
    det = doc.get("details")
    if not isinstance(det, dict):
        return False, "uw_daemon_health_state: details not dict"
    return True, "ok"


def validate_shadow_trade_log_entry(doc: Any) -> Tuple[bool, str]:
    if not isinstance(doc, dict):
        return False, "shadow_trade: not a dict"
    if not _is_iso_ts(doc.get("ts")):
        return False, "shadow_trade: ts invalid"
    if "event_type" not in doc or "symbol" not in doc:
        return False, "shadow_trade: missing event_type/symbol"
    if "v2_score" not in doc:
        return False, "shadow_trade: missing v2_score"
    return True, "ok"


def validate_exit_attribution(doc: Any) -> Tuple[bool, str]:
    if not isinstance(doc, dict):
        return False, "exit_attribution: not dict"
    if not doc.get("symbol"):
        return False, "exit_attribution: missing symbol"
    if not _is_iso_ts(doc.get("timestamp")):
        return False, "exit_attribution: timestamp invalid"
    if not doc.get("entry_timestamp"):
        return False, "exit_attribution: missing entry_timestamp"
    if not isinstance(doc.get("exit_reason"), str):
        return False, "exit_attribution: exit_reason not str"
    if "v2_exit_score" not in doc:
        return False, "exit_attribution: missing v2_exit_score"
    if not isinstance(doc.get("v2_exit_components"), dict):
        return False, "exit_attribution: v2_exit_components not dict"
    return True, "ok"


def validate_exit_intel_pnl_summary(doc: Any) -> Tuple[bool, str]:
    if not isinstance(doc, dict):
        return False, "exit_intel_pnl_summary: not dict"
    meta = doc.get("_meta")
    if not isinstance(meta, dict):
        return False, "exit_intel_pnl_summary: missing _meta"
    if not _is_iso_ts(meta.get("ts")):
        return False, "exit_intel_pnl_summary: _meta.ts invalid"
    if not isinstance(doc.get("by_exit_reason"), dict):
        return False, "exit_intel_pnl_summary: by_exit_reason not dict"
    return True, "ok"


def validate_exit_intel_state(doc: Any, *, kind: str) -> Tuple[bool, str]:
    if not isinstance(doc, dict):
        return False, f"{kind}: not dict"
    meta = doc.get("_meta")
    if not isinstance(meta, dict):
        return False, f"{kind}: missing _meta"
    if not _is_iso_ts(meta.get("ts")):
        return False, f"{kind}: _meta.ts invalid"
    sy = doc.get("symbols")
    if not isinstance(sy, dict):
        return False, f"{kind}: symbols not dict"
    return True, "ok"

