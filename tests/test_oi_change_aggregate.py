from src.uw.oi_change_aggregate import aggregate_uw_stock_oi_change_list


def test_aggregate_splits_call_put_and_net():
    rows = [
        {
            "option_symbol": "NVDA250620C00140000",
            "oi_diff_plain": 100,
        },
        {
            "option_symbol": "NVDA250620P00140000",
            "oi_diff_plain": -30,
        },
    ]
    out = aggregate_uw_stock_oi_change_list(rows)
    assert out["net_oi_change"] == 70.0
    assert out["call_oi_change"] == 100.0
    assert out["put_oi_change"] == -30.0
    assert out["aggregated_contracts"] == 2


def test_empty_list():
    assert aggregate_uw_stock_oi_change_list([]) == {}
    assert aggregate_uw_stock_oi_change_list(None) == {}  # type: ignore[arg-type]
