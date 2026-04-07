"""Singleton AlpacaStreamManager: one WS per process."""
from __future__ import annotations

import src.alpaca.stream_manager as sm
from src.alpaca.stream_manager import ensure_alpaca_stream_manager, register_stream_symbol_provider


def test_ensure_singleton_second_engine_does_not_restart(monkeypatch):
    sm._reset_stream_manager_for_tests()
    starts: list[str] = []

    def track_start(self):
        starts.append(self.stream_id)

    monkeypatch.setattr(sm.AlpacaStreamManager, "start", track_start)

    register_stream_symbol_provider(lambda: ["SPY"])
    m1 = ensure_alpaca_stream_manager("k", "s", paper=True)
    register_stream_symbol_provider(lambda: ["QQQ"])
    m2 = ensure_alpaca_stream_manager("k", "s", paper=True)

    assert m1 is not None and m2 is not None
    assert m1 is m2
    assert len(starts) == 1
    assert m1.stream_id == starts[0]

    sm._reset_stream_manager_for_tests()
