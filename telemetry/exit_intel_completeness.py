#!/usr/bin/env python3
"""
Exit intel completeness (v2, read-only)
=====================================

Computes best-effort completeness metrics for v2 exit attribution telemetry.

Inputs (best-effort):
- exit attribution records (dicts) from logs/exit_attribution.jsonl

Output:
- A JSON-serializable dict suitable for bundling into telemetry/YYYY-MM-DD/computed/.

Contract:
- Read-only, side-effect free.
- Never raises on malformed input.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple


REQUIRED_EXIT_COMPONENT_KEYS = [
    "vol_expansion",
    "regime_shift",
    "sector_shift",
    "flow_deterioration",
    "darkpool_deterioration",
    "sentiment_deterioration",
    "score_deterioration",
]

REQUIRED_TOP_LEVEL_KEYS = [
    "pnl",
    "pnl_pct",
    "entry_price",
    "exit_price",
    "qty",
    "time_in_trade_minutes",
    "entry_regime",
    "exit_regime",
    "entry_sector_profile",
    "exit_sector_profile",
    "v2_exit_score",
    "v2_exit_components",
]


def _is_number(x: Any) -> bool:
    try:
        if x is None:
            return False
        float(x)
        return True
    except Exception:
        return False


def build_exit_intel_completeness(*, day: str, exit_attrib_recs: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        total = int(len(exit_attrib_recs or []))
        top_missing = Counter()
        comp_missing = Counter()
        comp_present = Counter()
        by_exit_reason_missing: Dict[str, Counter] = defaultdict(Counter)

        for r in exit_attrib_recs or []:
            if not isinstance(r, dict):
                continue
            reason = str(r.get("exit_reason", "") or "")

            for k in REQUIRED_TOP_LEVEL_KEYS:
                if k not in r:
                    top_missing[k] += 1
                    by_exit_reason_missing[reason][f"top:{k}"] += 1

            comps = r.get("v2_exit_components")
            comps = comps if isinstance(comps, dict) else {}
            for k in REQUIRED_EXIT_COMPONENT_KEYS:
                if k in comps:
                    comp_present[k] += 1
                else:
                    comp_missing[k] += 1
                    by_exit_reason_missing[reason][f"comp:{k}"] += 1

            # Soft validation: these should be numeric when present
            for k in ("v2_exit_score", "score_deterioration", "relative_strength_deterioration"):
                if k in r and r.get(k) is not None and not _is_number(r.get(k)):
                    by_exit_reason_missing[reason][f"type_non_numeric:{k}"] += 1

        top_level_completeness = {}
        for k in REQUIRED_TOP_LEVEL_KEYS:
            missing_n = int(top_missing.get(k, 0))
            present_n = max(0, total - missing_n)
            top_level_completeness[k] = {
                "present": present_n,
                "missing": missing_n,
                "present_rate": (present_n / float(total)) if total else 0.0,
            }

        component_completeness = {}
        for k in REQUIRED_EXIT_COMPONENT_KEYS:
            present_n = int(comp_present.get(k, 0))
            missing_n = int(comp_missing.get(k, 0))
            component_completeness[k] = {
                "present": present_n,
                "missing": missing_n,
                "present_rate": (present_n / float(total)) if total else 0.0,
            }

        # Overall completeness: count record as complete if all required components present
        complete_records = 0
        for r in exit_attrib_recs or []:
            if not isinstance(r, dict):
                continue
            comps = r.get("v2_exit_components")
            comps = comps if isinstance(comps, dict) else {}
            if all(k in comps for k in REQUIRED_EXIT_COMPONENT_KEYS):
                complete_records += 1

        return {
            "_meta": {
                "date": str(day),
                "kind": "exit_intel_completeness",
                "version": "2026-01-22_v1",
            },
            "counts": {
                "exit_attribution_records": total,
                "complete_records": int(complete_records),
                "complete_rate": (complete_records / float(total)) if total else 0.0,
            },
            "required_top_level_keys": list(REQUIRED_TOP_LEVEL_KEYS),
            "required_exit_component_keys": list(REQUIRED_EXIT_COMPONENT_KEYS),
            "top_level_completeness": top_level_completeness,
            "exit_component_completeness": component_completeness,
            "missing_top_level_counts": dict(top_missing),
            "missing_component_counts": dict(comp_missing),
            "by_exit_reason_missing_counts": {k: dict(v) for k, v in by_exit_reason_missing.items()},
        }
    except Exception as e:
        return {
            "_meta": {"date": str(day), "kind": "exit_intel_completeness", "version": "2026-01-22_v1"},
            "error": str(e),
        }

