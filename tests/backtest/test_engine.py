import pandas as pd
import pytest
from pathlib import Path

from ai_xquanty.config import BacktestConfig, RealBacktestConfig
from ai_xquanty.backtest.engine import (
    run_backtest,
    run_backtest_on_bundle,
    select_weekly_rebalance_dates,
)
from ai_xquanty.domain.models import MarketDataBundle


def test_run_backtest_uses_trend_filter_strategy_when_selected(
    repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    used_names: list[str] = []

    def fake_resolve_signal_fn(strategy_name: str):
        used_names.append(strategy_name)

        def _fake_signal_fn(bundle, as_of):
            return []

        return _fake_signal_fn

    monkeypatch.setattr("ai_xquanty.backtest.engine.resolve_signal_fn", fake_resolve_signal_fn)

    config = BacktestConfig.from_sample_data(repo_root, strategy_name="trend_filter")
    result = run_backtest(config)

    assert used_names == ["trend_filter"]
    assert result.equity_curve["nav"].tolist()[0] == 1_000_000.0


def test_run_backtest_applies_filled_trade_costs_to_cash_holdings_and_nav(
    repo_root
) -> None:
    result = run_backtest(BacktestConfig.from_sample_data(repo_root))

    filled = result.fills[result.fills["status"] == "filled"]
    assert filled.to_dict("records") == [
        {
            "trade_date": "2024-01-08",
            "symbol": "510500.SH",
            "side": "BUY",
            "status": "filled",
            "quantity": 85300,
            "price": 5.272634999999999,
            "fees": 139.42428730499998,
        }
    ]

    jan_8 = result.equity_curve.iloc[-1]
    assert jan_8["trade_date"] == "2024-01-08"
    assert jan_8["cash"] == pytest.approx(550104.810212695)
    assert jan_8["holdings_value"] == pytest.approx(452943.0)
    assert jan_8["nav"] == pytest.approx(1003047.810212695)
    assert result.summary == {
        "final_nav": 1003047.810212695,
        "max_drawdown": 0.0,
        "num_observations": 5.0,
    }


def test_select_weekly_rebalance_dates_uses_last_trading_day_of_week() -> None:
    calendar = pd.DatetimeIndex(
        [
            "2024-01-02",
            "2024-01-03",
            "2024-01-04",
            "2024-01-05",
            "2024-01-08",
        ]
    )

    assert select_weekly_rebalance_dates(calendar) == [pd.Timestamp("2024-01-05")]


def test_trend_filter_skips_first_weekly_rebalance_without_required_history(
    tmp_path: Path,
) -> None:
    calendar = pd.to_datetime(["2021-07-28", "2021-07-29", "2021-07-30", "2021-08-02"])
    bars = pd.DataFrame(
        {"close": [3.50, 3.55, 3.60, 3.65]},
        index=pd.MultiIndex.from_product(
            [calendar, ["510300.SS"]], names=["trade_date", "symbol"]
        ),
    )
    bundle = MarketDataBundle(calendar=calendar, instruments={}, bars=bars)
    config = RealBacktestConfig(
        start="2021-07-28",
        end="2021-08-02",
        symbols=("510300.SS",),
        cache_dir=tmp_path,
        strategy_name="trend_filter",
    )

    result = run_backtest_on_bundle(config, bundle)

    assert result.fills.empty
    assert result.equity_curve["nav"].tolist() == [1_000_000.0] * 4
