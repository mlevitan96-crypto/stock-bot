"""
Chief Strategy Auditor (CSA) verdict contract — fixed, versioned.

Verdict: PROCEED | HOLD | ESCALATE | ROLLBACK
Confidence: LOW | MED | HIGH
Required fields for every CSA verdict payload.
Additive only; do not remove fields without deprecation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

CSA_VERDICT_SCHEMA_VERSION = "1.0"

VERDICT_VALUES = frozenset({"PROCEED", "HOLD", "ESCALATE", "ROLLBACK"})
CONFIDENCE_VALUES = frozenset({"LOW", "MED", "HIGH"})

CSA_VERDICT_REQUIRED = [
    "verdict",
    "confidence",
    "assumptions",
    "missing_data",
    "counterfactuals_not_tested",
    "value_leaks",
    "risk_asymmetry",
    "recommendation",
    "escalation_triggers",
    "required_next_experiments",
    "override_allowed",
    "override_requirements",
    "mission_id",
    "schema_version",
]


def validate_csa_verdict(payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a CSA verdict payload against the contract. Returns (ok, issues)."""
    issues: List[str] = []
    if not isinstance(payload, dict):
        return False, ["payload must be a dict"]

    for k in CSA_VERDICT_REQUIRED:
        if k not in payload:
            issues.append(f"missing required '{k}'")

    v = payload.get("verdict")
    if v is not None and v not in VERDICT_VALUES:
        issues.append(f"verdict must be one of {sorted(VERDICT_VALUES)}; got {v!r}")

    c = payload.get("confidence")
    if c is not None and c not in CONFIDENCE_VALUES:
        issues.append(f"confidence must be one of {sorted(CONFIDENCE_VALUES)}; got {c!r}")

    for list_field in (
        "assumptions",
        "missing_data",
        "counterfactuals_not_tested",
        "value_leaks",
        "escalation_triggers",
        "required_next_experiments",
        "override_requirements",
    ):
        val = payload.get(list_field)
        if val is not None and not isinstance(val, list):
            issues.append(f"'{list_field}' must be a list")

    ob = payload.get("override_allowed")
    if ob is not None and not isinstance(ob, bool):
        issues.append("override_allowed must be a boolean")

    return len(issues) == 0, issues


def build_verdict(
    verdict: str,
    confidence: str,
    assumptions: List[str],
    missing_data: List[str],
    counterfactuals_not_tested: List[str],
    value_leaks: List[str],
    risk_asymmetry: str,
    recommendation: str,
    escalation_triggers: List[str],
    required_next_experiments: List[str],
    override_allowed: bool = True,
    override_requirements: List[str] | None = None,
    mission_id: str = "",
    **extra: Any,
) -> Dict[str, Any]:
    """Build a contract-compliant CSA verdict dict."""
    override_requirements = override_requirements or [
        "reports/audit/CSA_RISK_ACCEPTANCE_<mission-id>.md"
    ]
    payload = {
        "schema_version": CSA_VERDICT_SCHEMA_VERSION,
        "mission_id": mission_id,
        "verdict": verdict,
        "confidence": confidence,
        "assumptions": list(assumptions),
        "missing_data": list(missing_data),
        "counterfactuals_not_tested": list(counterfactuals_not_tested),
        "value_leaks": list(value_leaks),
        "risk_asymmetry": risk_asymmetry,
        "recommendation": recommendation,
        "escalation_triggers": list(escalation_triggers),
        "required_next_experiments": list(required_next_experiments),
        "override_allowed": override_allowed,
        "override_requirements": [
            r.replace("<mission-id>", mission_id) for r in override_requirements
        ],
        **extra,
    }
    return payload
