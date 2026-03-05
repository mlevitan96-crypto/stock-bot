"""
SRE anomaly event schema — versioned, fixed.

event_type: RATE_ANOMALY | DISTRIBUTION_DRIFT | SILENCE_ANOMALY | ASYMMETRY_FLAG | EXPECTATION_VIOLATION
confidence: LOW | MED | HIGH
Additive only; do not remove fields without deprecation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

SRE_EVENT_SCHEMA_VERSION = "1.0"

EVENT_TYPES = frozenset({
    "RATE_ANOMALY",
    "DISTRIBUTION_DRIFT",
    "SILENCE_ANOMALY",
    "ASYMMETRY_FLAG",
    "EXPECTATION_VIOLATION",
})
CONFIDENCE_VALUES = frozenset({"LOW", "MED", "HIGH"})

SRE_EVENT_REQUIRED = [
    "event_type",
    "metric_name",
    "baseline_window",
    "observed_window",
    "baseline_value",
    "observed_value",
    "delta",
    "confidence",
    "timestamp",
    "notes",
    "event_id",
    "schema_version",
]


def validate_sre_event(payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a single SRE event against the contract. Returns (ok, issues)."""
    issues: List[str] = []
    if not isinstance(payload, dict):
        return False, ["event must be a dict"]

    for k in SRE_EVENT_REQUIRED:
        if k not in payload:
            issues.append(f"missing required '{k}'")

    et = payload.get("event_type")
    if et is not None and et not in EVENT_TYPES:
        issues.append(f"event_type must be one of {sorted(EVENT_TYPES)}; got {et!r}")

    conf = payload.get("confidence")
    if conf is not None and conf not in CONFIDENCE_VALUES:
        issues.append(f"confidence must be one of {sorted(CONFIDENCE_VALUES)}; got {conf!r}")

    return len(issues) == 0, issues


def build_sre_event(
    event_type: str,
    metric_name: str,
    baseline_window: str,
    observed_window: str,
    baseline_value: Any,
    observed_value: Any,
    delta: Any,
    confidence: str,
    timestamp: str,
    notes: str,
    event_id: str = "",
    **extra: Any,
) -> Dict[str, Any]:
    """Build a contract-compliant SRE event dict."""
    import uuid
    payload = {
        "schema_version": SRE_EVENT_SCHEMA_VERSION,
        "event_id": event_id or f"sre_{uuid.uuid4().hex[:12]}",
        "event_type": event_type,
        "metric_name": metric_name,
        "baseline_window": baseline_window,
        "observed_window": observed_window,
        "baseline_value": baseline_value,
        "observed_value": observed_value,
        "delta": delta,
        "confidence": confidence,
        "timestamp": timestamp,
        "notes": notes,
        **extra,
    }
    return payload


def has_economic_impact(event: Dict[str, Any]) -> bool:
    """True if event is tagged or inferred as having PnL/risk/learning impact."""
    if event.get("economic_impact") is True:
        return True
    et = (event.get("event_type") or "").upper()
    # Rate/silence/asymmetry/expectation can imply economic impact when HIGH confidence
    return et in ("RATE_ANOMALY", "ASYMMETRY_FLAG", "EXPECTATION_VIOLATION", "SILENCE_ANOMALY")
