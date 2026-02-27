#!/usr/bin/env python3
"""
Run on droplet: load uw_flow_cache, run compute_composite_score_v2 for sample symbols,
collect component values, weights, composite scores. Output JSON to stdout for signal_audit.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

MAX_SYMBOLS = 50


def _to_num(x):
    try:
        if x is None:
            return 0.0
        if isinstance(x, (int, float)) and not math.isnan(x):
            return float(x)
        return float(x) if x else 0.0
    except (TypeError, ValueError):
        return 0.0


def main():
    out = {
        "signal_inventory": [],
        "execution": {},
        "value_audit": {},
        "weight_audit": {},
        "composite_contribution": {},
        "composite_distribution": {},
        "dead_or_muted": [],
        "sample_size": 0,
        "symbols": [],
        "error": None,
    }
    try:
        cache_path = REPO / "data" / "uw_flow_cache.json"
        if not cache_path.exists():
            out["error"] = "data/uw_flow_cache.json not found"
            print(json.dumps(out))
            return 0
        with open(cache_path, "r", encoding="utf-8") as f:
            cache = json.load(f)
        if not isinstance(cache, dict):
            out["error"] = "cache not a dict"
            print(json.dumps(out))
            return 0
        symbols = [s for s in list(cache.keys())[:MAX_SYMBOLS] if isinstance(cache.get(s), dict)]
        if not symbols:
            out["error"] = "no symbol entries in cache"
            print(json.dumps(out))
            return 0

        import uw_composite_v2 as uw

        weights_v3 = getattr(uw, "WEIGHTS_V3", {})
        effective_weights = {}
        try:
            effective_weights = uw.get_all_current_weights()
        except Exception:
            effective_weights = dict(weights_v3)

        component_names = [
            "flow", "dark_pool", "insider", "iv_skew", "smile", "whale", "event", "motif_bonus",
            "toxicity_penalty", "regime", "congress", "shorts_squeeze", "institutional", "market_tide",
            "calendar", "greeks_gamma", "ftd_pressure", "iv_rank", "oi_change", "etf_flow", "squeeze_score", "freshness_factor"
        ]
        weight_key = {
            "flow": "options_flow", "dark_pool": "dark_pool", "insider": "insider",
            "iv_skew": "iv_term_skew", "smile": "smile_slope", "whale": "whale_persistence",
            "event": "event_alignment", "motif_bonus": "temporal_motif", "toxicity_penalty": "toxicity_penalty",
            "regime": "regime_modifier", "congress": "congress", "shorts_squeeze": "shorts_squeeze",
            "institutional": "institutional", "market_tide": "market_tide", "calendar": "calendar_catalyst",
            "greeks_gamma": "greeks_gamma", "ftd_pressure": "ftd_pressure", "iv_rank": "iv_rank",
            "oi_change": "oi_change", "etf_flow": "etf_flow", "squeeze_score": "squeeze_score",
        }
        for name in component_names:
            wkey = weight_key.get(name, name)
            w = effective_weights.get(wkey, weights_v3.get(wkey, 0))
            out["signal_inventory"].append({
                "name": name,
                "source": "uw_composite_v2.py",
                "weight": _to_num(w),
                "expected_range": "0-1 or scaled",
            })
        out["weight_audit"] = {k: _to_num(effective_weights.get(weight_key.get(k, k), weights_v3.get(weight_key.get(k, k), 0))) for k in component_names if k != "freshness_factor"}

        # Run scoring for each symbol
        scores = []
        per_component_values = {c: [] for c in component_names}
        execution_ok = {c: 0 for c in component_names}
        # Use same enrichment path as main.py (enrich_signal then compute_composite_score_v2)
        try:
            import uw_enrichment_v2 as uw_enrich
            use_enrich = True
        except Exception:
            use_enrich = False
        for sym in symbols:
            raw = cache.get(sym, {})
            enriched = uw_enrich.enrich_signal(sym, cache, "mixed") if use_enrich and raw else raw
            if not enriched:
                enriched = raw
            try:
                res = uw.compute_composite_score_v2(sym, enriched, regime="mixed")
            except Exception as e:
                out["error"] = str(e)
                break
            comps = res.get("components") or {}
            score = _to_num(res.get("score", 0))
            scores.append(score)
            for c in component_names:
                v = comps.get(c)
                if v is not None:
                    execution_ok[c] = execution_ok.get(c, 0) + 1
                    val = _to_num(v)
                    per_component_values.setdefault(c, []).append(val)
        out["sample_size"] = len(scores)
        out["symbols"] = symbols[:20]
        out["execution"] = execution_ok
        # Per-symbol components + sources for key symbols (SPY, QQQ, COIN, NVDA, TSLA)
        focus = ["SPY", "QQQ", "COIN", "NVDA", "TSLA"]
        out["per_symbol"] = {}
        for sym in focus:
            if sym not in cache or not isinstance(cache.get(sym), dict):
                out["per_symbol"][sym] = {"error": "not in cache"}
                continue
            raw = cache.get(sym, {})
            enriched = uw_enrich.enrich_signal(sym, cache, "mixed") if use_enrich and raw else raw
            if not enriched:
                enriched = raw
            try:
                res = uw.compute_composite_score_v2(sym, enriched, regime="mixed")
                comps = res.get("components") or {}
                sources = res.get("component_sources") or {}
                missing = res.get("missing_components") or []
                out["per_symbol"][sym] = {
                    "score": _to_num(res.get("score", 0)),
                    "components": comps,
                    "component_sources": sources,
                    "missing_components": missing,
                    "notes": (res.get("notes") or "")[:500],
                }
            except Exception as e:
                out["per_symbol"][sym] = {"error": str(e)}

        # Value audit
        for c in component_names:
            vals = per_component_values.get(c) or []
            n = len(vals)
            if n == 0:
                out["value_audit"][c] = {"min": None, "max": None, "mean": None, "pct_zero": 100.0, "pct_nan": 0, "constant": True}
                continue
            vals_clean = [_to_num(x) for x in vals if x is not None and not (isinstance(x, float) and math.isnan(x))]
            n_clean = len(vals_clean)
            n_zero = sum(1 for x in vals_clean if abs(x) < 1e-9)
            n_nan = n - n_clean
            mn = min(vals_clean) if vals_clean else None
            mx = max(vals_clean) if vals_clean else None
            mu = sum(vals_clean) / n_clean if n_clean else None
            out["value_audit"][c] = {
                "min": round(mn, 4) if mn is not None else None,
                "max": round(mx, 4) if mx is not None else None,
                "mean": round(mu, 4) if mu is not None else None,
                "pct_zero": round(100.0 * n_zero / n_clean, 1) if n_clean else 100.0,
                "pct_nan": round(100.0 * n_nan / n, 1) if n else 0,
                "constant": (mn is not None and mx is not None and abs(mx - mn) < 1e-9),
            }

        # Composite contribution (contribution = component value; already weighted in scorer)
        total_abs = {}
        for c in component_names:
            vals = per_component_values.get(c) or []
            total_abs[c] = sum(abs(_to_num(x)) for x in vals)
        sum_total = sum(total_abs.values()) or 1
        out["composite_contribution"] = {
            c: {"sum_abs": round(total_abs.get(c, 0), 4), "share_pct": round(100.0 * total_abs.get(c, 0) / sum_total, 2)}
            for c in component_names
        }

        # Distribution
        if scores:
            out["composite_distribution"] = {
                "min": round(min(scores), 3),
                "max": round(max(scores), 3),
                "mean": round(sum(scores) / len(scores), 3),
                "count": len(scores),
                "pct_below_2": round(100.0 * sum(1 for s in scores if s < 2) / len(scores), 1),
                "pct_below_3": round(100.0 * sum(1 for s in scores if s < 3) / len(scores), 1),
            }

        # Dead/muted
        for c in component_names:
            va = out["value_audit"].get(c) or {}
            contrib = out["composite_contribution"].get(c) or {}
            w = out["weight_audit"].get(c, 0)
            failure = None
            cause = None
            conf = "low"
            if va.get("constant") and va.get("mean") == 0:
                failure = "zeroed"
                cause = "All values zero or constant zero"
                conf = "high"
            elif va.get("pct_zero", 0) >= 99:
                failure = "zeroed"
                cause = ">99% zeros"
                conf = "medium"
            elif w is not None and abs(_to_num(w)) < 0.01:
                failure = "unweighted"
                cause = "Effective weight near zero"
                conf = "high"
            elif contrib.get("share_pct", 0) == 0 and (va.get("mean") or 0) == 0:
                failure = "no_contribution"
                cause = "~0 contribution across samples"
                conf = "medium"
            if failure:
                out["dead_or_muted"].append({"signal_name": c, "failure_mode": failure, "suspected_root_cause": cause, "confidence": conf})

    except Exception as e:
        out["error"] = str(e)
        import traceback
        out["traceback"] = traceback.format_exc()

    print(json.dumps(out))


if __name__ == "__main__":
    main()
