"""
Shadow experiment matrix: multi-variant experiments, no live orders.

Contract:
- run_shadow_variants(live_context, candidates, positions) -> None
- Writes only to logs/shadow.jsonl (shadow_variant_decision, shadow_variant_summary).
- DOES NOT place orders. Uses same enrichment caches.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SHADOW_LOG = _REPO_ROOT / "logs" / "shadow.jsonl"


def _append_shadow(record: Dict[str, Any]) -> None:
    _SHADOW_LOG.parent.mkdir(parents=True, exist_ok=True)
    rec = {"ts": datetime.now(timezone.utc).isoformat(), **record}
    with _SHADOW_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=str) + "\n")


def run_shadow_variants(
    live_context: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    positions: Dict[str, Any],
    *,
    experiments: Optional[List[Dict[str, Any]]] = None,
    max_variants_per_cycle: int = 4,
) -> Dict[str, Any]:
    """
    Run shadow variants for candidates. Emit shadow_variant_decision and shadow_variant_summary.
    Does NOT place orders. Returns {"variants_run": [...], "decisions_count": N}.
    """
    try:
        from config.registry import LogFiles, append_jsonl, read_json
        shadow_path = getattr(LogFiles, "SHADOW", None) or _SHADOW_LOG
    except Exception:
        shadow_path = _SHADOW_LOG

    out: Dict[str, Any] = {"variants_run": [], "decisions_count": 0}
    experiments = experiments or []
    if not experiments:
        try:
            from main import Config
            experiments = getattr(Config, "SHADOW_EXPERIMENTS", []) or []
            max_variants_per_cycle = getattr(Config, "SHADOW_MAX_VARIANTS_PER_CYCLE", 4) or 4
        except Exception:
            return out

    variants = experiments[: max_variants_per_cycle]
    out["variants_run"] = [v.get("name") or "?" for v in variants]
    regime = live_context.get("market_regime") or live_context.get("regime") or "mixed"
    engine = live_context.get("engine")

    for v in variants:
        name = v.get("name") or "unknown"
        overrides = {k: v[k] for k in v if k != "name"}
        would_enter_count = 0
        would_exit_count = 0
        blocked_by_reason: Dict[str, int] = defaultdict(int)

        for c in candidates:
            symbol = c.get("ticker") or c.get("symbol") or ""
            if not symbol:
                continue
            score = float(c.get("composite_score") or c.get("score") or 0.0)
            direction = (c.get("direction") or "bullish").lower()
            side = "buy" if direction == "bullish" else "sell"

            # Simple variant score override (placeholder)
            v2_score_variant = score
            if overrides.get("uw_flow_weight"):
                v2_score_variant = score * 1.1  # placeholder
            elif overrides.get("dark_pool_weight"):
                v2_score_variant = score * 1.05
            elif overrides.get("volatility_weight"):
                v2_score_variant = score * 1.05
            elif overrides.get("regime_multiplier") and regime not in ("mixed", "unknown"):
                v2_score_variant = score * 1.05

            if overrides.get("displacement_disabled"):
                pass  # no displacement effect in shadow
            if overrides.get("DISPLACEMENT_MIN_DELTA_SCORE") is not None:
                pass  # would affect displace logic; we don't model here

            in_pos = symbol in (positions or {})
            would_enter = v2_score_variant >= 3.0 and not in_pos
            would_exit = False  # we don't model per-variant exits here
            blocked_reason = None
            if not would_enter:
                if in_pos:
                    blocked_reason = "already_in_position"
                elif v2_score_variant < 3.0:
                    blocked_reason = "score_below_threshold"
                else:
                    blocked_reason = "other"
            if blocked_reason:
                blocked_by_reason[blocked_reason] += 1
            if would_enter:
                would_enter_count += 1
            if would_exit:
                would_exit_count += 1

            try:
                from telemetry.feature_snapshot import build_feature_snapshot
                from telemetry.thesis_tags import derive_thesis_tags
            except Exception:
                build_feature_snapshot = None
                derive_thesis_tags = None

            snap = tags = None
            if build_feature_snapshot and derive_thesis_tags and engine is not None:
                enriched = {"symbol": symbol, "score": v2_score_variant, "composite_score": v2_score_variant}
                enriched.update(c.get("features_for_learning") or c.get("components") or {})
                mc = getattr(engine, "market_context_v2", None) or {}
                rs = getattr(engine, "regime_posture_v2", None) or {}
                snap = build_feature_snapshot(enriched, mc if isinstance(mc, dict) else {}, rs if isinstance(rs, dict) else {})
                tags = derive_thesis_tags(snap or {})

            rec = {
                "event_type": "shadow_variant_decision",
                "variant_name": name,
                "symbol": symbol,
                "side": side,
                "would_enter": would_enter,
                "would_exit": would_exit,
                "blocked_reason": blocked_reason,
                "v2_score_variant": round(v2_score_variant, 4),
                "regime_label": regime,
                "feature_snapshot": snap,
                "thesis_tags": tags,
            }
            try:
                append_jsonl(shadow_path, rec)
            except Exception:
                _append_shadow(rec)
            out["decisions_count"] = out.get("decisions_count", 0) + 1

        sum_rec = {
            "event_type": "shadow_variant_summary",
            "variant_name": name,
            "candidates_considered": len(candidates),
            "would_enter_count": would_enter_count,
            "would_exit_count": would_exit_count,
            "blocked_counts_by_reason": dict(blocked_by_reason),
        }
        try:
            append_jsonl(shadow_path, sum_rec)
        except Exception:
            _append_shadow(sum_rec)
    return out
