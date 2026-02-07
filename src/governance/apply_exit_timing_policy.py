"""
Non-breaking enforcement shim for exit timing scenarios.

Design:
- Called from runtime at decision time (entry/exit evaluation).
- If governance config missing or scenario unset, returns original inputs unchanged.
- Applies:
  - min_hold_seconds_floor
  - signal_decay_sensitivity_mult
  - displacement_sensitivity_mult
  - optional regime overrides
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

try:
    from src.governance.governance_loader import resolve_policy
except Exception:  # pragma: no cover
    resolve_policy = None  # type: ignore


@dataclass
class ExitTimingPolicy:
    min_hold_seconds_floor: Optional[int] = None
    signal_decay_sensitivity_mult: Optional[float] = None
    displacement_sensitivity_mult: Optional[float] = None


def _get(d: Dict[str, Any], k: str, default=None):
    v = d.get(k, default)
    return default if v is None else v


def get_exit_timing_policy(*, mode: str, strategy: str, regime: str, scenario: str) -> ExitTimingPolicy:
    if resolve_policy is None:
        return ExitTimingPolicy()

    rp = resolve_policy(mode=mode, strategy=strategy, regime=regime, scenario=scenario) or {}
    base = rp.get("exit_timing_params", {}) or {}
    ov = rp.get("exit_timing_regime_overrides", {}) or {}

    merged = dict(base)
    merged.update(ov)

    return ExitTimingPolicy(
        min_hold_seconds_floor=_get(merged, "min_hold_seconds_floor"),
        signal_decay_sensitivity_mult=_get(merged, "signal_decay_sensitivity_mult"),
        displacement_sensitivity_mult=_get(merged, "displacement_sensitivity_mult"),
    )


def apply_exit_timing_to_exit_config(
    *,
    exit_cfg: Dict[str, Any],
    mode: str,
    strategy: str,
    regime: str,
    scenario: str,
) -> Dict[str, Any]:
    """
    Returns a patched copy of exit_cfg.
    Expected (optional) keys in exit_cfg:
      - min_hold_seconds
      - signal_decay_sensitivity
      - displacement_sensitivity
    """
    pol = get_exit_timing_policy(mode=mode, strategy=strategy, regime=regime, scenario=scenario)
    out = dict(exit_cfg or {})

    if pol.min_hold_seconds_floor is not None:
        prev = out.get("min_hold_seconds")
        if prev is None or pol.min_hold_seconds_floor > prev:
            out["min_hold_seconds"] = int(pol.min_hold_seconds_floor)

    if pol.signal_decay_sensitivity_mult is not None and "signal_decay_sensitivity" in out:
        out["signal_decay_sensitivity"] = (
            float(out["signal_decay_sensitivity"]) * float(pol.signal_decay_sensitivity_mult)
        )

    if pol.displacement_sensitivity_mult is not None and "displacement_sensitivity" in out:
        out["displacement_sensitivity"] = (
            float(out["displacement_sensitivity"]) * float(pol.displacement_sensitivity_mult)
        )

    return out
