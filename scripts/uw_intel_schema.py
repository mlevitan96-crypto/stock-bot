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

