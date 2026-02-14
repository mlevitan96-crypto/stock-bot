"""
Entry constraints: UW and survivorship overrides for paper-mode friendly behavior.
- UW override: if uw_signal_quality_score > 0.75, bypass score_floor_breach.
- Survivorship override: if survivorship_score > 0.1, bypass displacement (allow displacement for high-survivorship challengers).
"""
from __future__ import annotations

UW_QUALITY_BYPASS_SCORE_FLOOR_THRESHOLD = 0.75
SURVIVORSHIP_BYPASS_DISPLACEMENT_THRESHOLD = 0.1


def check_uw_override_bypass_score_floor(uw_signal_quality_score: float | None) -> bool:
    """True if UW quality > 0.75, allowing bypass of score_floor_breach for high-UW candidates."""
    if uw_signal_quality_score is None:
        return False
    try:
        return float(uw_signal_quality_score) > UW_QUALITY_BYPASS_SCORE_FLOOR_THRESHOLD
    except (TypeError, ValueError):
        return False


def check_survivorship_override_bypass_displacement(survivorship_score: float | None) -> bool:
    """True if survivorship_score > 0.1, allowing displacement bypass for strong survivorship challengers."""
    if survivorship_score is None:
        return False
    try:
        return float(survivorship_score) > SURVIVORSHIP_BYPASS_DISPLACEMENT_THRESHOLD
    except (TypeError, ValueError):
        return False
