"""
Telemetry computed artifact schema validation (regression-only)
=============================================================

These validators are intentionally strict and are used by:
- scripts/run_regression_checks.py

Contract:
- Fail fast on missing/malformed critical fields.
- Numeric fields must be real numbers (not None/NaN/Inf).
- Parity classifications must be one of the allowed values.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


def _is_num(x: Any) -> bool:
    try:
        f = float(x)
        return not (math.isnan(f) or math.isinf(f))
    except Exception:
        return False


def _req(d: Dict[str, Any], key: str) -> Any:
    if key not in d:
        raise AssertionError(f"missing key: {key}")
    return d[key]


def _req_dict(x: Any, name: str) -> Dict[str, Any]:
    if not isinstance(x, dict):
        raise AssertionError(f"{name} must be dict")
    return x


def _req_list(x: Any, name: str, *, non_empty: bool = True) -> List[Any]:
    if not isinstance(x, list):
        raise AssertionError(f"{name} must be list")
    if non_empty and len(x) == 0:
        raise AssertionError(f"{name} must be non-empty")
    return x


def validate_shadow_vs_live_parity(doc: Any) -> Tuple[bool, str]:
    try:
        d = _req_dict(doc, "shadow_vs_live_parity")
        _req_dict(_req(d, "_meta"), "_meta")
        entry_parity = _req_dict(_req(d, "entry_parity"), "entry_parity")
        rows = _req_list(_req(entry_parity, "rows"), "entry_parity.rows", non_empty=True)
        allowed = set(_req_list(_req(entry_parity, "allowed_classifications"), "entry_parity.allowed_classifications", non_empty=True))
        for cls in ["perfect_match", "near_match", "divergent", "missing_in_v1", "missing_in_v2"]:
            if cls not in allowed:
                raise AssertionError(f"allowed_classifications missing {cls}")
        agg = _req_dict(_req(d, "aggregate_metrics"), "aggregate_metrics")
        for k in ["mean_entry_ts_delta_seconds", "mean_score_delta", "mean_price_delta_usd", "match_rate", "matched_pairs"]:
            if k not in agg:
                raise AssertionError(f"aggregate_metrics missing {k}")
        if not _is_num(agg.get("match_rate")):
            raise AssertionError("aggregate_metrics.match_rate must be numeric")

        for r in rows[:2000]:  # cap validation work
            rr = _req_dict(r, "entry_parity.row")
            cls = str(_req(rr, "classification"))
            if cls not in allowed:
                raise AssertionError(f"unknown parity classification: {cls}")
            for nk in [
                "entry_ts_delta_seconds",
                "v1_score_at_entry",
                "v2_score_at_entry",
                "score_delta",
                "v1_price_at_entry",
                "v2_price_at_entry",
                "price_delta_usd",
            ]:
                if not _is_num(_req(rr, nk)):
                    raise AssertionError(f"parity row numeric invalid: {nk}")
        return True, "ok"
    except Exception as e:
        return False, str(e)


def validate_entry_parity_details(doc: Any) -> Tuple[bool, str]:
    try:
        d = _req_dict(doc, "entry_parity_details")
        rows = _req_list(_req(d, "rows"), "rows", non_empty=True)
        # Reuse row schema rules from parity
        allowed = {"perfect_match", "near_match", "divergent", "missing_in_v1", "missing_in_v2"}
        for r in rows[:2000]:
            rr = _req_dict(r, "row")
            cls = str(_req(rr, "classification"))
            if cls not in allowed:
                raise AssertionError(f"unknown classification: {cls}")
            for nk in [
                "entry_ts_delta_seconds",
                "v1_score_at_entry",
                "v2_score_at_entry",
                "score_delta",
                "v1_price_at_entry",
                "v2_price_at_entry",
                "price_delta_usd",
            ]:
                if not _is_num(_req(rr, nk)):
                    raise AssertionError(f"row numeric invalid: {nk}")
        return True, "ok"
    except Exception as e:
        return False, str(e)


def validate_score_distribution_curves(doc: Any) -> Tuple[bool, str]:
    try:
        d = _req_dict(doc, "score_distribution_curves")
        families = _req_dict(_req(d, "families"), "families")
        if not families:
            raise AssertionError("families must be non-empty")
        for fam, fam_block in list(families.items())[:50]:
            fb = _req_dict(fam_block, f"families[{fam}]")
            for grp in ["overall", "long", "short"]:
                gb = _req_dict(_req(fb, grp), f"{fam}.{grp}")
                for hk in ["v1_score_hist", "v2_score_hist", "score_delta_hist"]:
                    h = _req_dict(_req(gb, hk), f"{fam}.{grp}.{hk}")
                    edges = _req_list(_req(h, "edges"), f"{fam}.{grp}.{hk}.edges", non_empty=True)
                    counts = _req_list(_req(h, "counts"), f"{fam}.{grp}.{hk}.counts", non_empty=True)
                    if len(edges) < 2:
                        raise AssertionError(f"{fam}.{grp}.{hk}.edges must have >=2")
                    if len(counts) != len(edges) - 1:
                        raise AssertionError(f"{fam}.{grp}.{hk} counts length mismatch")
                    for v in edges[:50]:
                        if not _is_num(v):
                            raise AssertionError("hist edges must be numeric")
                    for v in counts[:50]:
                        if not _is_num(v):
                            raise AssertionError("hist counts must be numeric")
        return True, "ok"
    except Exception as e:
        return False, str(e)


def validate_regime_timeline(doc: Any) -> Tuple[bool, str]:
    try:
        d = _req_dict(doc, "regime_timeline")
        hourly = _req_list(_req(d, "hourly"), "hourly", non_empty=True)
        if len(hourly) != 24:
            raise AssertionError("hourly must have exactly 24 entries")
        for r in hourly:
            rr = _req_dict(r, "hourly row")
            h = int(_req(rr, "hour_utc"))
            if h < 0 or h > 23:
                raise AssertionError("hour_utc out of range")
            cnts = _req_dict(_req(rr, "counts"), "counts")
            for _, v in list(cnts.items())[:20]:
                if not _is_num(v):
                    raise AssertionError("counts values must be numeric")
        return True, "ok"
    except Exception as e:
        return False, str(e)


def validate_feature_family_summary(doc: Any) -> Tuple[bool, str]:
    try:
        d = _req_dict(doc, "feature_family_summary")
        fams = _req_dict(_req(d, "families"), "families")
        if not fams:
            raise AssertionError("families must be non-empty")
        for fam, row in list(fams.items())[:100]:
            rr = _req_dict(row, f"families[{fam}]")
            _req_dict(_req(rr, "counts"), "counts")
            for k in ["mean_value", "variance", "long_short_skew", "ev_contribution", "stability_score"]:
                if not _is_num(_req(rr, k)):
                    raise AssertionError(f"{fam}.{k} must be numeric")
        return True, "ok"
    except Exception as e:
        return False, str(e)


def validate_replacement_telemetry_expanded(doc: Any) -> Tuple[bool, str]:
    try:
        d = _req_dict(doc, "replacement_telemetry_expanded")
        cnts = _req_dict(_req(d, "counts"), "counts")
        for k in ["realized_trades", "replacement_trades", "replacement_rate"]:
            if not _is_num(_req(cnts, k)):
                raise AssertionError(f"counts.{k} must be numeric")
        _req_dict(_req(d, "per_feature_replacement_rate"), "per_feature_replacement_rate")
        _req_dict(_req(d, "per_family_replacement_rate"), "per_family_replacement_rate")
        rh = _req_dict(_req(d, "replacement_cause_histogram"), "replacement_cause_histogram")
        if not rh:
            raise AssertionError("replacement_cause_histogram must be non-empty")
        return True, "ok"
    except Exception as e:
        return False, str(e)


def validate_long_short_analysis(doc: Any) -> Tuple[bool, str]:
    try:
        d = _req_dict(doc, "long_short_analysis")
        for grp in ["overall", "long", "short"]:
            g = _req_dict(_req(d, grp), grp)
            for k in ["count", "win_count", "loss_count", "win_rate", "avg_pnl_usd", "avg_win_usd", "avg_loss_usd", "expectancy_usd", "total_pnl_usd"]:
                if not _is_num(_req(g, k)):
                    raise AssertionError(f"{grp}.{k} must be numeric")
        return True, "ok"
    except Exception as e:
        return False, str(e)


def validate_exit_intel_completeness(doc: Any) -> Tuple[bool, str]:
    try:
        d = _req_dict(doc, "exit_intel_completeness")
        cnts = _req_dict(_req(d, "counts"), "counts")
        for k in ["exit_attribution_records", "complete_records", "complete_rate"]:
            if not _is_num(_req(cnts, k)):
                raise AssertionError(f"counts.{k} must be numeric")
        _req_list(_req(d, "required_top_level_keys"), "required_top_level_keys", non_empty=True)
        _req_list(_req(d, "required_exit_component_keys"), "required_exit_component_keys", non_empty=True)
        return True, "ok"
    except Exception as e:
        return False, str(e)


def validate_feature_value_curves(doc: Any) -> Tuple[bool, str]:
    try:
        d = _req_dict(doc, "feature_value_curves")
        feats = _req_dict(_req(d, "features"), "features")
        if not feats:
            raise AssertionError("features must be non-empty")
        for feat, fb in list(feats.items())[:50]:
            fbd = _req_dict(fb, f"features[{feat}]")
            for grp in ["overall", "long", "short"]:
                arr = _req_list(_req(fbd, grp), f"{feat}.{grp}", non_empty=True)
                for row in arr[:50]:
                    rr = _req_dict(row, "bin")
                    for nk in ["x_lo", "x_hi", "count", "avg_pnl_usd", "total_pnl_usd"]:
                        if not _is_num(_req(rr, nk)):
                            raise AssertionError(f"{feat}.{grp}.{nk} must be numeric")
        return True, "ok"
    except Exception as e:
        return False, str(e)


def validate_regime_sector_feature_matrix(doc: Any) -> Tuple[bool, str]:
    try:
        d = _req_dict(doc, "regime_sector_feature_matrix")
        m = _req_dict(_req(d, "matrix"), "matrix")
        # matrix can be empty on quiet days, but must be a dict.
        for reg, sectors in list(m.items())[:20]:
            sd = _req_dict(sectors, f"matrix[{reg}]")
            for sec, cell in list(sd.items())[:20]:
                cd = _req_dict(cell, f"cell[{reg}][{sec}]")
                ccell = _req_dict(_req(cd, "_cell"), "_cell")
                for nk in ["count", "total_pnl_usd", "avg_pnl_usd"]:
                    if not _is_num(_req(ccell, nk)):
                        raise AssertionError(f"_cell.{nk} must be numeric")
                feats = _req_dict(_req(cd, "features"), "features")
                for feat, st in list(feats.items())[:50]:
                    fd = _req_dict(st, f"features[{feat}]")
                    for nk in ["count", "total_pnl_usd", "avg_pnl_usd", "avg_input"]:
                        if not _is_num(_req(fd, nk)):
                            raise AssertionError(f"{feat}.{nk} must be numeric")
        return True, "ok"
    except Exception as e:
        return False, str(e)


def validate_live_vs_shadow_pnl(doc: Any) -> Tuple[bool, str]:
    try:
        d = _req_dict(doc, "live_vs_shadow_pnl")
        _req(d, "as_of_ts")
        wins = _req_dict(_req(d, "windows"), "windows")
        for wn in ["24h", "48h", "5d"]:
            w = _req_dict(_req(wins, wn), f"windows[{wn}]")
            for side in ["live", "shadow", "delta"]:
                s = _req_dict(_req(w, side), f"{wn}.{side}")
                for k in ["pnl_usd", "expectancy_usd", "trade_count", "win_rate"]:
                    if not _is_num(_req(s, k)):
                        raise AssertionError(f"{wn}.{side}.{k} must be numeric")
            # insufficient_data must exist (bool-ish), but do not over-validate type here.
            if "insufficient_data" not in w:
                raise AssertionError(f"{wn}.insufficient_data missing")
        _req_list(_req(d, "per_symbol"), "per_symbol", non_empty=False)
        return True, "ok"
    except Exception as e:
        return False, str(e)


def validate_signal_performance(doc: Any) -> Tuple[bool, str]:
    try:
        d = _req_dict(doc, "signal_performance")
        _req(d, "as_of_ts")
        sigs = _req_list(_req(d, "signals"), "signals", non_empty=False)
        for r in sigs[:500]:
            rr = _req_dict(r, "signal")
            _req(rr, "name")
            for k in ["win_rate", "avg_pnl_usd", "expectancy_usd", "trade_count", "contribution_to_total_pnl"]:
                if not _is_num(_req(rr, k)):
                    raise AssertionError(f"signal.{k} must be numeric")
            lsb = _req_dict(_req(rr, "long_short_breakdown"), "long_short_breakdown")
            for side in ["long", "short"]:
                sb = _req_dict(_req(lsb, side), f"long_short_breakdown.{side}")
                for k in ["win_rate", "expectancy_usd", "trade_count"]:
                    if not _is_num(_req(sb, k)):
                        raise AssertionError(f"{side}.{k} must be numeric")
            _req_list(_req(rr, "regime_breakdown"), "regime_breakdown", non_empty=False)
        return True, "ok"
    except Exception as e:
        return False, str(e)


def validate_signal_weight_recommendations(doc: Any) -> Tuple[bool, str]:
    try:
        d = _req_dict(doc, "signal_weight_recommendations")
        _req(d, "as_of_ts")
        recs = _req_list(_req(d, "recommendations"), "recommendations", non_empty=False)
        allowed = {"low", "medium", "high"}
        for r in recs[:500]:
            rr = _req_dict(r, "recommendation")
            _req(rr, "signal")
            if not _is_num(_req(rr, "suggested_delta_weight")):
                raise AssertionError("suggested_delta_weight must be numeric")
            conf = str(_req(rr, "confidence") or "").lower()
            if conf not in allowed:
                raise AssertionError(f"confidence must be one of {sorted(allowed)}")
            _req(rr, "rationale")
        return True, "ok"
    except Exception as e:
        return False, str(e)

