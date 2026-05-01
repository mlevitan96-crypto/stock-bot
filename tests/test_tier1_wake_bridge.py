from __future__ import annotations

import json
import time

import pytest


def test_signal_tier1_wake_updates_mtime(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.telemetry import tier1_wake_bridge as tw

    p = tmp_path / "tier1_wake.json"
    monkeypatch.setenv("TIER1_WAKE_JSON_PATH", str(p))
    assert tw.tier1_wake_mtime() == 0.0
    tw.signal_tier1_wake("test", "AAPL")
    assert p.is_file()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data.get("source") == "test"
    assert data.get("symbol") == "AAPL"
    assert tw.tier1_wake_mtime() > 0


def test_tier1_wake_poll_seconds_clamped(monkeypatch: pytest.MonkeyPatch) -> None:
    """Module reads TIER1_WAKE_POLL_SEC at import; smoke default is sane."""
    from src.telemetry.tier1_wake_bridge import tier1_wake_poll_seconds

    p = tier1_wake_poll_seconds()
    assert 0.05 <= p <= 5.0
