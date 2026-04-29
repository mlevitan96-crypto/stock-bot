from src.uw.uw_flow_trade_normalize import normalize_ws_flow_alert_to_rest_trade


def test_normalize_ws_flow_maps_uw_doc_example():
    payload = {
        "rule_id": "5ce5ec11-087c-4c00-b164-08106b015856",
        "ticker": "DIA",
        "option_chain": "DIA241018C00415000",
        "total_premium": 36466,
        "has_sweep": False,
        "executed_at": 1726670212748,
    }
    out = normalize_ws_flow_alert_to_rest_trade("DIA", payload)
    assert out["type"] == "CALL"
    assert out["premium"] == 36466.0
    assert out["total_premium"] == 36466.0
    assert out["timestamp"] == 1726670212
    assert out["_ingest_source"] == "uw_ws_flow_alerts"


def test_normalize_ws_flow_sweep_flags():
    out = normalize_ws_flow_alert_to_rest_trade("SPY", {"ticker": "SPY", "has_sweep": True, "total_premium": 1})
    assert out.get("is_sweep") is True
    assert out.get("sweep") is True
