from ai_xquanty.config import BacktestConfig
from ai_xquanty.data.loaders import load_market_data


def test_load_market_data_builds_sorted_bundle(repo_root) -> None:
    config = BacktestConfig.from_sample_data(repo_root)

    bundle = load_market_data(config)

    assert bundle.calendar[0].strftime("%Y-%m-%d") == "2024-01-02"
    assert bundle.bars.index.names == ["trade_date", "symbol"]
    assert float(bundle.bars.loc[("2024-01-02", "510300.SH"), "close"]) == 3.51
