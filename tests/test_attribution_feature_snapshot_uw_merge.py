"""UW cache merge into shared feature snapshot (telemetry / ML gate parity)."""
from __future__ import annotations

from telemetry.attribution_feature_snapshot import build_shared_feature_snapshot, merge_uw_cache_into_enriched_signal


def test_merge_uw_cache_fills_sparse_enriched():
    cache = {
        "NVDA": {
            "flow_strength": 0.42,
            "conviction": 0.55,
            "dark_pool": {"total_notional": 2_500_000.0, "sentiment": "BULLISH", "print_count": 12},
            "iv_skew": -0.08,
        }
    }
    en = {"symbol": "NVDA", "score": 5.0, "composite_score": 5.0}
    out = merge_uw_cache_into_enriched_signal(en, "NVDA", uw_cache=cache)
    assert out.get("flow_strength") == 0.42
    assert out.get("dark_pool_notional") == 2_500_000.0
    assert out.get("iv_skew") == -0.08


def test_build_shared_feature_snapshot_includes_uw_proxies(monkeypatch):
    cache = {
        "AAPL": {
            "flow_strength": 0.33,
            "dark_pool": {"total_premium": 800_000.0, "sentiment": "NEUTRAL"},
        }
    }

    def fake_read_json(path, default=None):
        return cache

    import config.registry as _reg

    monkeypatch.setattr(_reg, "read_json", fake_read_json)
    snap = build_shared_feature_snapshot(
        {"symbol": "AAPL", "score": 4.0},
        {},
        {},
        snapshot_stage="blocked",
    )
    assert snap.get("uw_flow_strength") == 0.33
    assert snap.get("symbol") == "AAPL"


def test_learn_from_trade_close_accepts_why_explanation(monkeypatch):
    calls = []

    def fake_record_trade(*a, **k):
        calls.append("record")

    class Opt:
        def record_trade(self, *a, **k):
            fake_record_trade(*a, **k)

    def fake_get_optimizer():
        return Opt()

    monkeypatch.setattr("comprehensive_learning_orchestrator_v2.get_optimizer", fake_get_optimizer)
    from comprehensive_learning_orchestrator_v2 import learn_from_trade_close

    learn_from_trade_close(
        "X",
        1.0,
        {"options_flow": 0.5},
        "mixed",
        "Technology",
        why_explanation="Exited X because: signal_decay(0.7).",
    )
    assert calls == ["record"]
