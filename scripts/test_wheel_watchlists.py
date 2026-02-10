#!/usr/bin/env python3
"""
Tests for Board watchlists derived from signal trends and correlation (review-only).
- Weakening watchlist from signal_strength_cache (trend=weakening, delta <= threshold).
- Correlation watchlist from signal_correlation_cache (max_corr >= threshold).
- Validation that Board output must address each watchlist symbol.
- Artifact wheel_watchlists_<date>.json structure.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def test_weakening_watchlist_generated_from_trends():
    """Weakening watchlist includes only open positions with trend=weakening and delta <= -0.50."""
    from board.eod.run_stock_quant_officer_eod import build_weakening_watchlist

    # Empty cache -> empty list
    assert build_weakening_watchlist({}) == []

    # Weakening with delta <= -0.50 included
    cache = {
        "AAPL": {
            "signal_strength": 0.4,
            "prev_signal_strength": 0.9,
            "signal_delta": -0.55,
            "signal_trend": "weakening",
            "evaluated_at": "2025-02-09T12:00:00",
            "position_side": "LONG",
        },
        "MSFT": {
            "signal_strength": 0.7,
            "prev_signal_strength": 0.75,
            "signal_delta": -0.05,
            "signal_trend": "weakening",
            "evaluated_at": "2025-02-09T12:00:00",
            "position_side": "LONG",
        },
        "GOOG": {
            "signal_strength": 0.3,
            "prev_signal_strength": 0.8,
            "signal_delta": -0.60,
            "signal_trend": "strengthening",  # wrong trend
            "evaluated_at": "2025-02-09T12:00:00",
            "position_side": "LONG",
        },
    }
    out = build_weakening_watchlist(cache)
    assert len(out) == 1
    assert out[0]["symbol"] == "AAPL"
    assert out[0]["side"] == "LONG"
    assert out[0]["current_signal"] == 0.4
    assert out[0]["prev_signal"] == 0.9
    assert out[0]["signal_delta"] <= -0.5
    assert "evaluated_at" in out[0]

    # Exactly at threshold -0.50 included
    cache2 = {"X": {"signal_strength": 0.5, "prev_signal_strength": 1.0, "signal_delta": -0.50, "signal_trend": "weakening", "evaluated_at": "", "position_side": "LONG"}}
    out2 = build_weakening_watchlist(cache2)
    assert len(out2) == 1 and out2[0]["symbol"] == "X"


def test_correlation_watchlist_generated_from_cache():
    """Correlation watchlist includes symbols with max_corr >= 0.80."""
    from board.eod.run_stock_quant_officer_eod import build_correlation_watchlist

    assert build_correlation_watchlist({}) == []
    assert build_correlation_watchlist({"top_symbols": {}}) == []

    corr_cache = {
        "top_symbols": {
            "AAPL": {"max_corr": 0.92, "most_correlated_with": "MSFT", "avg_corr_topk": 0.85},
            "MSFT": {"max_corr": 0.92, "most_correlated_with": "AAPL", "avg_corr_topk": 0.88},
            "GOOG": {"max_corr": 0.65, "most_correlated_with": "META", "avg_corr_topk": 0.50},
            "META": {"max_corr": None, "most_correlated_with": None, "avg_corr_topk": None},
        },
    }
    out = build_correlation_watchlist(corr_cache)
    assert len(out) == 2
    symbols = {e["symbol"] for e in out}
    assert symbols == {"AAPL", "MSFT"}
    for e in out:
        assert e["max_corr"] >= 0.80
        assert "most_correlated_with" in e
        assert "avg_corr_topk" in e or e.get("avg_corr_topk") is None

    # At threshold 0.80 included
    corr_cache2 = {"top_symbols": {"Y": {"max_corr": 0.80, "most_correlated_with": "Z", "avg_corr_topk": 0.75}}}
    out2 = build_correlation_watchlist(corr_cache2)
    assert len(out2) == 1 and out2[0]["symbol"] == "Y"


def test_board_fails_when_watchlist_not_addressed():
    """validate_watchlist_responses returns (False, errors) when Board output omits or has empty rationales."""
    from board.eod.run_stock_quant_officer_eod import validate_watchlist_responses

    weakening = [{"symbol": "AAPL", "side": "LONG", "current_signal": 0.4, "prev_signal": 0.9, "signal_delta": -0.55, "evaluated_at": ""}]
    correlation = [{"symbol": "MSFT", "max_corr": 0.9, "most_correlated_with": "AAPL", "avg_corr_topk": 0.85}]

    # Empty Board output -> errors
    ok, errs = validate_watchlist_responses({"wheel_watchlists": {}}, weakening, correlation)
    assert ok is False
    assert any("AAPL" in e for e in errs)
    assert any("MSFT" in e or "correlation" in e for e in errs)

    # Missing one symbol in Board output
    ok2, errs2 = validate_watchlist_responses({
        "wheel_watchlists": {
            "weakening_signals": [{"symbol": "AAPL", "board_rationale": "Holding for theta.", "exit_review_condition": "If delta < -0.7"}],
            "correlation_concentration": [],  # missing MSFT
        },
    }, weakening, correlation)
    assert ok2 is False
    assert any("MSFT" in e or "correlation" in e for e in errs2)

    # Empty board_rationale -> error
    ok3, errs3 = validate_watchlist_responses({
        "wheel_watchlists": {
            "weakening_signals": [{"symbol": "AAPL", "board_rationale": "", "exit_review_condition": "N/A"}],
            "correlation_concentration": [{"symbol": "MSFT", "board_rationale": "Acceptable.", "mitigation_considered": "None"}],
        },
    }, weakening, correlation)
    assert ok3 is False
    assert any("board_rationale" in e or "AAPL" in e for e in errs3)

    # All present and non-empty -> ok
    ok4, errs4 = validate_watchlist_responses({
        "wheel_watchlists": {
            "weakening_signals": [{"symbol": "AAPL", "board_rationale": "Holding.", "exit_review_condition": "N/A"}],
            "correlation_concentration": [{"symbol": "MSFT", "board_rationale": "Acceptable.", "mitigation_considered": "None"}],
        },
    }, weakening, correlation)
    assert ok4 is True
    assert len(errs4) == 0

    # Empty watchlists -> no requirement on Board output
    ok5, _ = validate_watchlist_responses({"wheel_watchlists": {}}, [], [])
    assert ok5 is True


def test_watchlist_artifact_written():
    """write_wheel_watchlists produces reports/wheel_watchlists_<date>.json with date, thresholds, and merged entries."""
    from board.eod.run_stock_quant_officer_eod import write_wheel_watchlists

    weakening_input = [
        {"symbol": "AAPL", "side": "LONG", "current_signal": 0.4, "prev_signal": 0.9, "signal_delta": -0.55, "evaluated_at": "2025-02-09T12:00:00"},
    ]
    correlation_input = [
        {"symbol": "MSFT", "max_corr": 0.9, "most_correlated_with": "AAPL", "avg_corr_topk": 0.85},
    ]
    obj = {
        "wheel_watchlists": {
            "weakening_signals": [
                {"symbol": "AAPL", "board_rationale": "Holding for theta.", "exit_review_condition": "If delta < -0.7"},
            ],
            "correlation_concentration": [
                {"symbol": "MSFT", "board_rationale": "Acceptable.", "mitigation_considered": "None"},
            ],
        },
    }

    with tempfile.TemporaryDirectory() as tmp:
        reports_dir = Path(tmp) / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        with open(Path(__file__).resolve().parents[1] / "board" / "eod" / "run_stock_quant_officer_eod.py", encoding="utf-8") as f:
            # We need to patch REPORTS_DIR so write_wheel_watchlists writes to tmp
            pass
        # Import after potential patch; run in a subprocess or patch REPORTS_DIR
        import board.eod.run_stock_quant_officer_eod as board_eod
        board_eod.REPORTS_DIR = reports_dir
        write_wheel_watchlists("2025-02-09", weakening_input, correlation_input, obj)
        path = reports_dir / "wheel_watchlists_2025-02-09.json"
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["date"] == "2025-02-09"
        assert data["thresholds"]["signal_weakening"] == -0.50
        assert data["thresholds"]["correlation_concentration"] == 0.80
        assert len(data["weakening_signals"]) == 1
        assert data["weakening_signals"][0]["symbol"] == "AAPL"
        assert data["weakening_signals"][0]["board_rationale"] == "Holding for theta."
        assert data["weakening_signals"][0]["exit_review_condition"] == "If delta < -0.7"
        assert len(data["correlation_concentration"]) == 1
        assert data["correlation_concentration"][0]["symbol"] == "MSFT"
        assert data["correlation_concentration"][0]["board_rationale"] == "Acceptable."
        assert data["correlation_concentration"][0]["mitigation_considered"] == "None"


if __name__ == "__main__":
    test_weakening_watchlist_generated_from_trends()
    test_correlation_watchlist_generated_from_cache()
    test_board_fails_when_watchlist_not_addressed()
    test_watchlist_artifact_written()
    print("All watchlist tests passed.")
