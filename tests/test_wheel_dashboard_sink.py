"""Wheel HUD sink rows: CSP → assignment (CC_STOCK) → CC leg visibility."""

from __future__ import annotations

from src.wheel_dashboard_sink import build_wheel_hud_rows


def test_mock_assignment_shows_cc_stock_and_cc_rows():
    state = {
        "open_csps": {},
        "assigned_shares": {
            "AAPL": [
                {
                    "qty": 100,
                    "cost_basis": 180.0,
                    "assigned_at": "2026-04-01T12:00:00+00:00",
                }
            ],
        },
        "open_ccs": {
            "AAPL": [
                {
                    "strike": 190.0,
                    "symbol": "AAPL260515C00190000",
                    "expiry": "2026-05-15",
                    "opened_at": "2026-04-02T12:00:00+00:00",
                }
            ],
        },
        "csp_history": [
            {
                "underlying_symbol": "AAPL",
                "open_credit": 2.5,
            }
        ],
        "cc_history": [],
    }
    rows = build_wheel_hud_rows(state, spot_by_underlying={"AAPL": 185.0})
    stages = {r["ticker"]: r["stage"] for r in rows}
    assert "AAPL" in stages
    assert any(r["stage"] == "CC_STOCK" for r in rows)
    assert any(r["stage"] == "CC" for r in rows)
    prem = next(r["realized_premium_usd"] for r in rows if r["ticker"] == "AAPL" and r["stage"] == "CC_STOCK")
    assert prem == 2.5
