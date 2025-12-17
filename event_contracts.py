#!/usr/bin/env python3
"""
Event contracts (schema + terminology) for observability + learning.

Goal:
- Avoid mismatched labels and "random JSON" across the codebase
- Provide stable, versioned event types and required fields
- Keep this lightweight so it can be imported from main/dashboard/rollups
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional


SCHEMA_VERSION = 1


class EventType:
    # Decision journal
    DECISION_CANDIDATE = "DECISION_CANDIDATE"
    DECISION_BLOCKED = "DECISION_BLOCKED"
    DECISION_TAKEN = "DECISION_TAKEN"

    # Counterfactual / shadow lab
    SHADOW_INTENT = "SHADOW_INTENT"
    SHADOW_OUTCOME = "SHADOW_OUTCOME"


BASE_REQUIRED_FIELDS = ("event", "schema_version", "symbol")

REQUIRED_FIELDS_BY_EVENT = {
    EventType.DECISION_CANDIDATE: (*BASE_REQUIRED_FIELDS, "run_id", "cycle_ts", "rank"),
    EventType.DECISION_BLOCKED: (*BASE_REQUIRED_FIELDS, "run_id", "cycle_ts", "reason"),
    EventType.DECISION_TAKEN: (*BASE_REQUIRED_FIELDS, "run_id", "cycle_ts", "side", "qty"),
    EventType.SHADOW_INTENT: (*BASE_REQUIRED_FIELDS, "run_id", "intent_id", "entry_ts", "entry_price"),
    EventType.SHADOW_OUTCOME: (*BASE_REQUIRED_FIELDS, "run_id", "intent_id", "horizon_min", "ret_pct"),
}


@dataclass(frozen=True)
class ContractError(Exception):
    message: str

    def __str__(self) -> str:  # pragma: no cover
        return self.message


def make_event(event_type: str, symbol: str, **fields: Any) -> Dict[str, Any]:
    rec: Dict[str, Any] = {
        "event": event_type,
        "schema_version": SCHEMA_VERSION,
        "symbol": symbol,
    }
    rec.update(fields)
    return rec


def validate_event(rec: Dict[str, Any], raise_on_error: bool = True) -> bool:
    et = rec.get("event")
    if not et or not isinstance(et, str):
        if raise_on_error:
            raise ContractError("missing/invalid event")
        return False

    req = REQUIRED_FIELDS_BY_EVENT.get(et, BASE_REQUIRED_FIELDS)
    missing = [k for k in req if k not in rec]
    if missing:
        if raise_on_error:
            raise ContractError(f"{et}: missing required fields: {missing}")
        return False

    if rec.get("schema_version") != SCHEMA_VERSION:
        if raise_on_error:
            raise ContractError(f"{et}: schema_version mismatch: {rec.get('schema_version')} != {SCHEMA_VERSION}")
        return False

    return True


def validate_events(records: Iterable[Dict[str, Any]]) -> bool:
    for r in records:
        validate_event(r, raise_on_error=True)
    return True


def safe_get(d: Dict[str, Any], key: str, default: Any = None) -> Any:
    v = d.get(key, default)
    return v if v is not None else default

