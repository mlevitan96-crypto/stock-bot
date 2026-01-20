#!/usr/bin/env python3
"""
UW Attribution Engine (v2, shadow-only)
======================================

Contract:
- Additive: does not affect scoring decisions or v1 behavior.
- Append-only output: logs/uw_attribution.jsonl
- Must never raise (safe for scoring pipeline).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


UW_ATTRIBUTION_LOG = Path("logs/uw_attribution.jsonl")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_jsonl(path: Path, rec: Dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception:
        return


def emit_uw_attribution(
    *,
    symbol: str,
    direction: str,
    composite_version: str,
    uw_intel_version: str,
    uw_features: Dict[str, Any],
    uw_contribution: Dict[str, Any],
    timestamp: Optional[str] = None,
) -> None:
    """
    Write one attribution record (append-only). Never raises.
    """
    rec = {
        "symbol": str(symbol).upper(),
        "timestamp": timestamp or _now_iso(),
        "direction": str(direction),
        "uw_features": dict(uw_features or {}),
        "uw_contribution": dict(uw_contribution or {}),
        "composite_version": str(composite_version),
        "uw_intel_version": str(uw_intel_version or ""),
    }
    _append_jsonl(UW_ATTRIBUTION_LOG, rec)

