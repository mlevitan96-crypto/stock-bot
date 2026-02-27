"""
Canonical Trade Intelligence Attribution Schema (v1)
====================================================

Principles:
- Every score is the sum of named components (no opaque totals).
- Every component can have sub-components (tree).
- Every component has: name, source, raw_value(s), normalized_value(s), weight(s),
  contribution_to_score (signed), confidence/quality flags, timestamp(s), lifecycle_stage.
- Supports multiple time snapshots: signal evaluation, entry fill, periodic during trade, exit decision.
- Reason codes for entry and exit reference the same component keys.

Schema version: 1.0.0
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

# Pydantic optional for backward compatibility when not installed
try:
    from pydantic import BaseModel, Field
except ImportError:
    BaseModel = object  # type: ignore
    def Field(default=..., **kwargs):  # type: ignore
        return default


SCHEMA_VERSION = "1.0.0"


class LifecycleStage(str, Enum):
    """When this snapshot was taken in the trade lifecycle."""
    PRE_ENTRY = "pre_entry"       # at signal evaluation time
    ENTRY = "entry"               # at entry fill time
    POST_ENTRY = "post_entry"     # periodic during trade (optional)
    EXIT_DECISION = "exit_decision"  # at exit decision time
    EXIT_FILL = "exit_fill"       # at exit fill time


class ComponentSource(str, Enum):
    """Origin of the component."""
    UW = "uw"
    INTERNAL = "internal"
    DERIVED = "derived"


def _base_model_config():
    try:
        from pydantic import ConfigDict
        return {"extra": "forbid"} if hasattr(ConfigDict, "extra") else {}
    except Exception:
        return {}


if BaseModel is not object and hasattr(BaseModel, "model_validate"):

    class ScoreComponent(BaseModel):
        """A single score component (leaf or node with children)."""
        name: str = Field(..., description="Stable key for the component")
        source: ComponentSource = Field(..., description="uw | internal | derived")
        raw_value: Optional[Any] = Field(None, description="Raw value(s) from source")
        normalized_value: Optional[float] = Field(None, description="Normalized value used in score")
        weight: Optional[float] = Field(None, description="Weight applied")
        contribution_to_score: float = Field(0.0, description="Signed contribution to total score")
        confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence or quality [0,1]")
        quality_flags: Optional[List[str]] = Field(None, description="e.g. stale, missing, conflicting, low_liquidity")
        timestamp_utc: Optional[str] = Field(None, description="ISO timestamp when computed")
        lifecycle_stage: Optional[LifecycleStage] = None
        sub_components: Optional[List[Any]] = Field(None, description="Child components (tree)")
        missing_reason: Optional[str] = Field(None, description="If absent: why (explicit null + reason)")

        model_config = {"extra": "forbid", "use_enum_values": True}


    class AttributionSnapshot(BaseModel):
        """One snapshot of the full component tree + totals at a point in time."""
        snapshot_id: Optional[str] = Field(None, description="Unique id for this snapshot")
        trade_id: str = Field(..., description="Links to trade")
        symbol: str = Field(..., description="Symbol")
        lifecycle_stage: LifecycleStage = Field(...)
        timestamp_utc: str = Field(..., description="ISO timestamp")
        total_score: float = Field(..., description="Must equal sum(component contributions)")
        components: List[ScoreComponent] = Field(..., description="Top-level component tree")
        entry_reason_codes: Optional[List[str]] = Field(None, description="If entry: reason codes referencing component keys")
        exit_reason_code: Optional[str] = Field(None, description="If exit: stable exit reason code")
        schema_version: str = Field(default=SCHEMA_VERSION)

        model_config = {"extra": "forbid", "use_enum_values": True}


    class TradeAttributionRecord(BaseModel):
        """Full attribution for one trade: entry snapshot + exit snapshot + metadata."""
        trade_id: str = Field(...)
        symbol: str = Field(...)
        attribution_id: Optional[str] = Field(None, description="Stable id for this attribution record")
        entry_snapshot: Optional[AttributionSnapshot] = Field(None, description="At entry fill")
        exit_snapshot: Optional[AttributionSnapshot] = Field(None, description="At exit decision/fill")
        exit_reason_code: Optional[str] = Field(None, description="Stable exit reason code")
        schema_version: str = Field(default=SCHEMA_VERSION)

        model_config = {"extra": "forbid", "use_enum_values": True}

else:
    # Fallback: dataclass-like dict contracts (no pydantic)
    ScoreComponent = dict  # type: ignore
    AttributionSnapshot = dict  # type: ignore
    TradeAttributionRecord = dict  # type: ignore


# --- Dict-based constructors for use without Pydantic ---

def score_component_dict(
    name: str,
    source: str,
    contribution_to_score: float,
    *,
    raw_value: Any = None,
    normalized_value: Optional[float] = None,
    weight: Optional[float] = None,
    confidence: Optional[float] = None,
    quality_flags: Optional[List[str]] = None,
    timestamp_utc: Optional[str] = None,
    lifecycle_stage: Optional[str] = None,
    sub_components: Optional[List[Dict[str, Any]]] = None,
    missing_reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a ScoreComponent as a dict (schema v1)."""
    return {
        "name": name,
        "source": source,
        "raw_value": raw_value,
        "normalized_value": normalized_value,
        "weight": weight,
        "contribution_to_score": contribution_to_score,
        "confidence": confidence,
        "quality_flags": quality_flags or [],
        "timestamp_utc": timestamp_utc,
        "lifecycle_stage": lifecycle_stage,
        "sub_components": sub_components or [],
        "missing_reason": missing_reason,
    }


def attribution_snapshot_dict(
    trade_id: str,
    symbol: str,
    lifecycle_stage: str,
    timestamp_utc: str,
    total_score: float,
    components: List[Dict[str, Any]],
    *,
    snapshot_id: Optional[str] = None,
    entry_reason_codes: Optional[List[str]] = None,
    exit_reason_code: Optional[str] = None,
) -> Dict[str, Any]:
    """Build an AttributionSnapshot as a dict (schema v1)."""
    return {
        "snapshot_id": snapshot_id,
        "trade_id": trade_id,
        "symbol": symbol,
        "lifecycle_stage": lifecycle_stage,
        "timestamp_utc": timestamp_utc,
        "total_score": total_score,
        "components": components,
        "entry_reason_codes": entry_reason_codes,
        "exit_reason_code": exit_reason_code,
        "schema_version": SCHEMA_VERSION,
    }


def trade_attribution_record_dict(
    trade_id: str,
    symbol: str,
    *,
    attribution_id: Optional[str] = None,
    entry_snapshot: Optional[Dict[str, Any]] = None,
    exit_snapshot: Optional[Dict[str, Any]] = None,
    exit_reason_code: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a TradeAttributionRecord as a dict (schema v1)."""
    return {
        "trade_id": trade_id,
        "symbol": symbol,
        "attribution_id": attribution_id,
        "entry_snapshot": entry_snapshot,
        "exit_snapshot": exit_snapshot,
        "exit_reason_code": exit_reason_code,
        "schema_version": SCHEMA_VERSION,
    }
