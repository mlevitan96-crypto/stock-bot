"""
Grand Unified Theory (GUT) confluence product for live entry gating.

Operator definition (multiplicative hull on composite contributions + UW flow strength):

    Score = Flow_Strength × (1+DarkPool) × (1+IV_Skew) × ((1+ToxicityPenalty) × (1+Regime))

``Flow_Strength`` is Alpha-11 style UW strength from ``src.alpha11_gate._extract_flow_strength``;
fallback: ``components.flow`` when strength is missing (fail-soft for telemetry).

Threshold resolution (first non-empty wins):
  1. ``GUT_CONFLUENCE_MIN`` env (float > 0)
  2. ``artifacts/ml/gut_threshold.json`` key ``min_confluence`` (repo root from caller file)

When ``GUT_GATE_ENABLED`` is true but no threshold is configured, the gate **fails open**
(allows entry, logs once) so partial telemetry cannot brick the book.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[1]
_THRESHOLD_WARNED = False


def _float(x: Any, default: float = 0.0) -> float:
    try:
        v = float(x)
        return v if math.isfinite(v) else default
    except (TypeError, ValueError):
        return default


def _pos_hull(v: float) -> float:
    """Map typical composite contributions into a strictly positive multiplicative factor."""
    return max(1e-12, 1.0 + float(v))


def load_gut_threshold_min(repo_root: Optional[Path] = None) -> Optional[float]:
    """Return minimum confluence product from env or ``artifacts/ml/gut_threshold.json``."""
    raw = (os.environ.get("GUT_CONFLUENCE_MIN") or "").strip()
    if raw:
        try:
            m = float(raw)
            if math.isfinite(m) and m > 0:
                return m
        except ValueError:
            pass
    root = repo_root or _REPO_ROOT
    for rel in (
        root / "artifacts" / "ml" / "gut_threshold.json",
        root / "config" / "gut_threshold.json",
    ):
        if not rel.is_file():
            continue
        try:
            o = json.loads(rel.read_text(encoding="utf-8"))
            if isinstance(o, dict) and o.get("min_confluence") is not None:
                m = float(o["min_confluence"])
                if math.isfinite(m) and m > 0:
                    return m
        except Exception:
            continue
    return None


def gut_confluence_product(
    *,
    cluster: Mapping[str, Any],
    comps: Optional[Mapping[str, Any]],
) -> Tuple[float, Dict[str, float]]:
    """
    Returns (score, detail) using the operator's multiplicative recipe on shifted components.
    """
    comps = dict(comps or {})
    try:
        from src.alpha11_gate import _extract_flow_strength

        cm = cluster.get("composite_meta") if isinstance(cluster.get("composite_meta"), dict) else {}
        # ``v2_uw_inputs`` lives on composite_meta (same object scanned twice in Alpha 11).
        fs = _extract_flow_strength(cm, cm) if cm else _extract_flow_strength(cluster, {})  # type: ignore[arg-type]
    except Exception:
        fs = None
    if fs is None:
        fs = _float(comps.get("flow"), 0.25)
    else:
        fs = _float(fs, 0.25)

    dp = _float(comps.get("dark_pool"), 0.0)
    iv = _float(comps.get("iv_skew"), 0.0)
    tox = _float(comps.get("toxicity_penalty"), 0.0)
    reg = _float(comps.get("regime"), 0.0)

    inner = _pos_hull(tox) * _pos_hull(reg)
    s = _pos_hull(fs) * _pos_hull(dp) * _pos_hull(iv) * inner
    detail = {
        "flow_strength": float(fs),
        "dark_pool": float(dp),
        "iv_skew": float(iv),
        "toxicity_penalty": float(tox),
        "regime": float(reg),
        "inner_toxicity_x_regime": float(inner),
        "confluence_product": float(s),
    }
    return float(s), detail


def gut_gate_enabled() -> bool:
    return os.environ.get("GUT_GATE_ENABLED", "0").strip().lower() in ("1", "true", "yes", "on")


def evaluate_gut_gate(
    *,
    cluster: Mapping[str, Any],
    comps: Optional[Mapping[str, Any]],
    repo_root: Optional[Path] = None,
) -> Tuple[bool, str, float, Dict[str, float]]:
    """
    Returns (allowed, reason_code, confluence_score, detail).

    If gate disabled → allowed.
    If enabled and no threshold → allowed (fail-open) with reason ``gut_no_threshold_fail_open``.
    If enabled and score < threshold → blocked.
    """
    global _THRESHOLD_WARNED
    score, detail = gut_confluence_product(cluster=cluster, comps=comps)
    if not gut_gate_enabled():
        return True, "gut_gate_disabled", score, detail

    thr = load_gut_threshold_min(repo_root)
    if thr is None or thr <= 0:
        if not _THRESHOLD_WARNED:
            _THRESHOLD_WARNED = True
            try:
                import sys

                print(
                    "[gut_confluence_gate] GUT_GATE_ENABLED=1 but no positive threshold "
                    "(set GUT_CONFLUENCE_MIN or config/gut_threshold.json) — failing OPEN.",
                    file=sys.stderr,
                    flush=True,
                )
            except Exception:
                pass
        return True, "gut_no_threshold_fail_open", score, detail

    ok = score >= float(thr)
    reason = "gut_ok" if ok else "gut_confluence_below_threshold"
    detail["threshold_min"] = float(thr)
    return ok, reason, score, detail
