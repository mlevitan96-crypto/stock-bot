"""
Canonical SRE repair playbook registry: strict-chain failure classes → additive actions.

All repairs delegate to strict_backfill_* JSONL only (see alpaca_strict_six_trade_additive_repair).
"""
from __future__ import annotations

from typing import Any, Dict, FrozenSet, List, Optional, Set

MISSING_ENTRY_LEG = "MISSING_ENTRY_LEG"
MISSING_EXIT_INTENT = "MISSING_EXIT_INTENT"
JOIN_KEY_DRIFT = "JOIN_KEY_DRIFT"
TEMPORAL_ORDER_VIOLATION = "TEMPORAL_ORDER_VIOLATION"
EMITTER_REGRESSION = "EMITTER_REGRESSION"
UNKNOWN = "UNKNOWN"

ALL_CLASSES = (
    MISSING_ENTRY_LEG,
    MISSING_EXIT_INTENT,
    JOIN_KEY_DRIFT,
    TEMPORAL_ORDER_VIOLATION,
    EMITTER_REGRESSION,
    UNKNOWN,
)

# Gate reason strings that cannot be fixed by additive sidecars alone → escalate / UNKNOWN.
REASONS_ESCALATE_ADDITIVE: FrozenSet[str] = frozenset(
    {
        "missing_unified_exit_attribution_terminal",
        "missing_pnl_economic_closure",
        "exit_attribution_missing_positive_exit_price",
        "trade_id_schema_unexpected",
    }
)

# Primary mapping: single gate reason → playbook class (first match wins in classifier).
REASON_TO_CLASS: Dict[str, str] = {
    "entry_decision_not_joinable_by_canonical_trade_id": MISSING_ENTRY_LEG,
    "missing_unified_entry_attribution": MISSING_ENTRY_LEG,
    "missing_exit_intent_for_canonical_trade_id": MISSING_EXIT_INTENT,
    "no_orders_rows_with_canonical_trade_id": JOIN_KEY_DRIFT,
    "cannot_resolve_join_aliases": JOIN_KEY_DRIFT,
    "cannot_derive_trade_key": JOIN_KEY_DRIFT,
    "temporal_exit_before_entry": TEMPORAL_ORDER_VIOLATION,
}


def reasons_for_trade_id(gate_json: Dict[str, Any], trade_id: str) -> List[str]:
    out: List[str] = []
    for reason, ids in (gate_json.get("incomplete_trade_ids_by_reason") or {}).items():
        if trade_id in (ids or []):
            out.append(str(reason))
    return sorted(out)


def classify_trade(reasons: List[str]) -> str:
    """Return one failure class per trade (strict-chain)."""
    rs = set(reasons)
    if not rs:
        return UNKNOWN
    if rs & REASONS_ESCALATE_ADDITIVE:
        return UNKNOWN
    if "temporal_exit_before_entry" in rs:
        return TEMPORAL_ORDER_VIOLATION
    if "missing_exit_intent_for_canonical_trade_id" in rs:
        return MISSING_EXIT_INTENT
    if "entry_decision_not_joinable_by_canonical_trade_id" in rs or "missing_unified_entry_attribution" in rs:
        return MISSING_ENTRY_LEG
    if "no_orders_rows_with_canonical_trade_id" in rs or "cannot_resolve_join_aliases" in rs or "cannot_derive_trade_key" in rs:
        return JOIN_KEY_DRIFT
    return UNKNOWN


def classify_emitter_regression(gate_json: Dict[str, Any]) -> bool:
    return bool(gate_json.get("code_structural_trade_intent_no_canonical_on_entered"))


def playbook_meta(class_name: str) -> Dict[str, Any]:
    """Documentation / safety registry (no I/O)."""
    base = {
        "additive_only": True,
        "primary_logs_mutated": False,
        "sidecars": [
            "logs/strict_backfill_run.jsonl",
            "logs/strict_backfill_orders.jsonl",
            "logs/strict_backfill_alpaca_unified_events.jsonl",
        ],
    }
    recipes: Dict[str, Dict[str, Any]] = {
        MISSING_ENTRY_LEG: {
            "preconditions": ["exit_attribution + terminal unified exit exist for trade_id", "build_lines_for_trade non-empty"],
            "repair_action": "Synthesize trade_intent(entered) + alpaca_entry_attribution keyed to exit trade_key family",
            "safety_bounds": "strict_backfilled:true; ts at entry; no primary mutation",
            "verification": "telemetry.alpaca_strict_completeness_gate.evaluate_completeness audit=True",
        },
        MISSING_EXIT_INTENT: {
            "preconditions": ["same as MISSING_ENTRY_LEG"],
            "repair_action": "Synthesize exit_intent with ts before terminal close",
            "safety_bounds": "Clamp between entry+30s and exit−2s when timestamps known",
            "verification": "strict gate exit_intent_keyed_present",
        },
        JOIN_KEY_DRIFT: {
            "preconditions": ["unified exit provides authoritative trade_key"],
            "repair_action": "Synthetic orders row canonical_trade_id aligned to exit trade_key; intents use same family",
            "safety_bounds": "id=strict_backfill_order:<trade_id>; no copying full foreign order blobs",
            "verification": "orders_rows_canonical_trade_id_present in matrix",
        },
        TEMPORAL_ORDER_VIOLATION: {
            "preconditions": ["econ timestamps parseable"],
            "repair_action": "Same additive rows; timestamps ordered via build_lines_for_trade clamps",
            "safety_bounds": "Never place exit_intent after unified terminal close",
            "verification": "reason temporal_exit_before_entry cleared after primary data fix or backfill ordering",
        },
        EMITTER_REGRESSION: {
            "preconditions": ["Detected via main.py structural probe"],
            "repair_action": "None in sidecar layer — code change required",
            "safety_bounds": "N/A",
            "verification": "code path fix in main.py",
        },
        UNKNOWN: {
            "preconditions": ["Escalation reasons present or unclassified"],
            "repair_action": "No automatic playbook; human / emitter fix",
            "safety_bounds": "Do not mutate primary logs",
            "verification": "INCIDENT artifact",
        },
    }
    return {**base, **recipes.get(class_name, recipes[UNKNOWN])}


def registry_summary() -> Dict[str, Any]:
    return {
        "classes": list(ALL_CLASSES),
        "reasons_escalate_additive": sorted(REASONS_ESCALATE_ADDITIVE),
        "reason_to_class": dict(REASON_TO_CLASS),
    }
