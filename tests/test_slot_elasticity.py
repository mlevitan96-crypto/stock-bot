from __future__ import annotations

from trading.slot_elasticity import resolve_effective_max_slots


def test_elasticity_disabled_returns_base() -> None:
    assert (
        resolve_effective_max_slots(
            base_cap=32,
            enabled=False,
            chop_max=25,
            neutral_max=32,
            trend_max=44,
            crash_max=20,
            ladder_conf=0.55,
            regime_posture={"regime_label": "chop"},
        )
        == 32
    )


def test_chop_consolidates() -> None:
    v = resolve_effective_max_slots(
        base_cap=32,
        enabled=True,
        chop_max=25,
        neutral_max=32,
        trend_max=44,
        crash_max=20,
        ladder_conf=0.55,
        regime_posture={"regime_label": "chop", "regime_confidence": 0.9, "posture": "neutral"},
    )
    assert v == 25


def test_bull_long_expands_within_cap() -> None:
    v = resolve_effective_max_slots(
        base_cap=16,
        enabled=True,
        chop_max=25,
        neutral_max=32,
        trend_max=44,
        crash_max=20,
        ladder_conf=0.55,
        regime_posture={"regime_label": "bull", "regime_confidence": 0.7, "posture": "long"},
    )
    assert v == 44


def test_crash_min_slots() -> None:
    v = resolve_effective_max_slots(
        base_cap=32,
        enabled=True,
        chop_max=25,
        neutral_max=32,
        trend_max=44,
        crash_max=20,
        ladder_conf=0.55,
        regime_posture={"regime_label": "crash", "regime_confidence": 0.9, "posture": "short"},
    )
    assert v == 20
