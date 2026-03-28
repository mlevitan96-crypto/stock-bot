"""
Live `entry_decision_made` rows for Alpaca learning truth (telemetry-only).

Emitted to logs/run.jsonl at the same decision moment as trade_intent(entered) after a fill.
Never raises in hot paths.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

ENTRY_EVENT_TYPE = "entry_decision_made"
ENTRY_INTENT_STATUS_OK = "OK"
ENTRY_INTENT_STATUS_BLOCKER = "MISSING_INTENT_BLOCKER"


def _policy_anchor(cluster: Optional[dict], composite_meta: Optional[dict]) -> str:
    meta = composite_meta if isinstance(composite_meta, dict) else {}
    for key in ("policy_id", "attribution_policy", "strategy_tier", "schema_version"):
        v = meta.get(key)
        if v is not None and str(v).strip():
            return str(v).strip()[:200]
    c = cluster if isinstance(cluster, dict) else {}
    for key in ("strategy_id", "strategy", "signal_pack"):
        v = c.get(key)
        if v is not None and str(v).strip():
            return str(v).strip()[:200]
    return "alpaca_equity_default"


def _entry_score_components_from_context(
    comps: Optional[dict],
    composite_meta: Optional[dict],
    score: Optional[float],
) -> Dict[str, Any]:
    meta = composite_meta if isinstance(composite_meta, dict) else {}
    cc = meta.get("component_contributions")
    if isinstance(cc, dict) and cc:
        out: Dict[str, Any] = {}
        for k, v in cc.items():
            try:
                out[str(k)] = float(v) if isinstance(v, (int, float)) else float(v)
            except (TypeError, ValueError):
                continue
        if out:
            return out
    raw = meta.get("components") if isinstance(meta.get("components"), dict) else None
    src = raw if isinstance(raw, dict) else (comps if isinstance(comps, dict) else {})
    if isinstance(src, dict) and src:
        out = {}
        for k, v in src.items():
            try:
                if isinstance(v, (int, float)):
                    out[str(k)] = float(v)
                elif v is not None and str(v).strip() != "":
                    out[str(k)] = float(v)
            except (TypeError, ValueError):
                out[str(k)] = v
        if out:
            return out
    if isinstance(score, (int, float)):
        return {"_no_breakdown": True, "entry_score_total_echo": float(score)}
    return {}


def build_entry_decision_made_record(
    *,
    symbol: str,
    side: str,
    score: Optional[float],
    comps: Optional[dict],
    cluster: Optional[dict],
    intelligence_trace: Optional[dict],
    canonical_trade_id: Optional[str],
    trade_id_open: str,
    decision_event_id: Optional[str],
    time_bucket_id: Optional[str],
    symbol_normalized: Optional[str],
) -> Dict[str, Any]:
    """
    Build one entry_decision_made payload (not yet written).
    Either OK (full learning economics) or MISSING_INTENT_BLOCKER (stay-live audit fail).
    """
    c = cluster if isinstance(cluster, dict) else {}
    meta = c.get("composite_meta") if isinstance(c.get("composite_meta"), dict) else {}
    pa = _policy_anchor(c, meta)
    comps_d = comps if isinstance(comps, dict) else {}

    score_f: Optional[float] = None
    if isinstance(score, (int, float)):
        score_f = float(score)

    components = _entry_score_components_from_context(comps_d, meta, score_f)

    trace_ok = isinstance(intelligence_trace, dict) and bool(intelligence_trace)
    trace_layers_ok = bool(trace_ok and intelligence_trace.get("signal_layers"))

    def _blocker(reason: str) -> Dict[str, Any]:
        return {
            "event_type": ENTRY_EVENT_TYPE,
            "entry_intent_synthetic": False,
            "entry_intent_source": "live_runtime",
            "entry_intent_status": ENTRY_INTENT_STATUS_BLOCKER,
            "entry_intent_error": reason,
            "symbol": str(symbol).upper(),
            "side": str(side),
            "canonical_trade_id": canonical_trade_id,
            "trade_id": str(trade_id_open),
            "trade_key": str(canonical_trade_id) if canonical_trade_id else None,
            "decision_event_id": decision_event_id,
            "time_bucket_id": time_bucket_id,
            "symbol_normalized": symbol_normalized,
            "signal_trace": {"policy_anchor": pa, "_blocker": True, "reason": reason},
            "entry_score_total": score_f,
            "entry_score_components": {"_blocked": True, "reason": reason},
        }

    if score_f is None:
        return _blocker("entry_score_total_non_numeric")

    if not components:
        return _blocker("entry_score_components_empty")

    if trace_layers_ok:
        signal_trace: Dict[str, Any] = {"policy_anchor": pa, "intelligence_trace": intelligence_trace}
    elif trace_ok and comps_d:
        signal_trace = {
            "policy_anchor": pa,
            "intelligence_trace": intelligence_trace,
            "source": "intelligence_trace_without_layers_components_fallback",
            "component_keys": sorted(str(k) for k in comps_d.keys())[:48],
        }
    elif comps_d:
        signal_trace = {
            "policy_anchor": pa,
            "source": "equalizer_components_only",
            "side_intended": side,
            "cluster_direction": c.get("direction"),
            "component_keys": sorted(str(k) for k in comps_d.keys())[:48],
        }
    else:
        return _blocker("intelligence_trace_unavailable")

    return {
        "event_type": ENTRY_EVENT_TYPE,
        "entry_intent_synthetic": False,
        "entry_intent_source": "live_runtime",
        "entry_intent_status": ENTRY_INTENT_STATUS_OK,
        "entry_intent_error": None,
        "symbol": str(symbol).upper(),
        "side": str(side),
        "canonical_trade_id": canonical_trade_id,
        "trade_id": str(trade_id_open),
        "trade_key": str(canonical_trade_id) if canonical_trade_id else None,
        "decision_event_id": decision_event_id,
        "time_bucket_id": time_bucket_id,
        "symbol_normalized": symbol_normalized,
        "signal_trace": signal_trace,
        "entry_score_total": score_f,
        "entry_score_components": components,
    }


def emit_entry_decision_made(
    write_run: Callable[[str, Dict[str, Any]], None],
    *,
    symbol: str,
    side: str,
    score: Optional[float],
    comps: Optional[dict],
    cluster: Optional[dict],
    intelligence_trace: Optional[dict],
    canonical_trade_id: Optional[str],
    trade_id_open: str,
    decision_event_id: Optional[str],
    time_bucket_id: Optional[str],
    symbol_normalized: Optional[str],
    phase2_enabled: bool = True,
) -> None:
    """Append one entry_decision_made line via write_run('run', record)."""
    if not phase2_enabled:
        return
    try:
        rec = build_entry_decision_made_record(
            symbol=symbol,
            side=side,
            score=score,
            comps=comps,
            cluster=cluster,
            intelligence_trace=intelligence_trace,
            canonical_trade_id=canonical_trade_id,
            trade_id_open=trade_id_open,
            decision_event_id=decision_event_id,
            time_bucket_id=time_bucket_id,
            symbol_normalized=symbol_normalized,
        )
        write_run("run", rec)
    except Exception as ex:
        try:
            from telemetry.learning_blocker_emit import emit_learning_blocker

            emit_learning_blocker(
                "entry_decision_made_emit_failed",
                str(symbol),
                error=str(ex)[:500],
            )
        except Exception:
            pass


def audit_entry_decision_made_row_live_truth_present(row: Optional[dict]) -> bool:
    """LIVE learning truth: full OK contract OR explicit non-synthetic MISSING_INTENT_BLOCKER (stay-live)."""
    if audit_entry_decision_made_row_ok(row):
        return True
    if not row or not isinstance(row, dict):
        return False
    if row.get("event_type") != ENTRY_EVENT_TYPE:
        return False
    if row.get("strict_backfilled") or row.get("strict_backfill_trade_id"):
        return False
    if row.get("entry_intent_synthetic") is True:
        return False
    if str(row.get("entry_intent_status") or "") != ENTRY_INTENT_STATUS_BLOCKER:
        return False
    comp = row.get("entry_score_components")
    if not isinstance(comp, dict) or comp.get("_blocked") is not True:
        return False
    return True


def audit_entry_decision_made_row_ok(row: Optional[dict]) -> bool:
    """True only for LIVE, OK status, full contract (used by audits/tests)."""
    if not row or not isinstance(row, dict):
        return False
    if row.get("event_type") != ENTRY_EVENT_TYPE:
        return False
    if row.get("strict_backfilled") or row.get("strict_backfill_trade_id"):
        return False
    if row.get("entry_intent_synthetic") is True:
        return False
    if str(row.get("entry_intent_status") or "") != ENTRY_INTENT_STATUS_OK:
        return False
    st = row.get("signal_trace")
    if not isinstance(st, dict) or not st:
        return False
    if not str(st.get("policy_anchor") or "").strip():
        return False
    if st.get("_blocker") is True:
        return False
    tot = row.get("entry_score_total")
    if not isinstance(tot, (int, float)):
        return False
    comp = row.get("entry_score_components")
    if not isinstance(comp, dict) or not comp:
        return False
    if comp.get("_blocked") is True:
        return False
    return True


def score_entry_decision_made_row(row: dict) -> tuple:
    """Higher tuple = better for de-duplication (live OK > live blocker > synthetic)."""
    if not isinstance(row, dict) or row.get("event_type") != ENTRY_EVENT_TYPE:
        return (0, 0, 0)
    synth = 1 if (row.get("strict_backfilled") or row.get("strict_backfill_trade_id") or row.get("entry_intent_synthetic") is True) else 0
    if audit_entry_decision_made_row_ok(row):
        tier = 2
    elif audit_entry_decision_made_row_live_truth_present(row):
        tier = 1
    else:
        tier = 0
    layers = 0
    st = row.get("signal_trace")
    if isinstance(st, dict) and isinstance(st.get("intelligence_trace"), dict):
        layers = len((st["intelligence_trace"].get("signal_layers") or {}) or {})
    return (synth == 0, tier, layers)
