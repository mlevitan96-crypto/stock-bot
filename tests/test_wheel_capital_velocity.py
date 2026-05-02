"""Capital velocity premium capture ratio."""

from __future__ import annotations

from src.wheel_capital_velocity import _csp_premium_capture_ratio


def test_quick_exit_ratio_at_threshold():
    # Sold at 2.00/share credit = $200; buy back at 0.20/share = $20 -> captured 180/200 = 0.9
    r = _csp_premium_capture_ratio(200.0, 0.20)
    assert r is not None
    assert abs(r - 0.9) < 1e-6


def test_capture_ratio_none_without_credit():
    assert _csp_premium_capture_ratio(0, 0.5) is None
