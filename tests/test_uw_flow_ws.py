from uw_flow_ws import extract_flow_symbol


def test_extract_flow_symbol_common_keys():
    assert extract_flow_symbol({"symbol": "nvda"}) == "NVDA"
    assert extract_flow_symbol({"underlying_symbol": "AAPL"}) == "AAPL"
    assert extract_flow_symbol({"ticker": " SPY "}) == "SPY"
    assert extract_flow_symbol({}) is None
    assert extract_flow_symbol("not-a-dict") is None
