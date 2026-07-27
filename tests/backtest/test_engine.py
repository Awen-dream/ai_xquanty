import pandas as pd
import pytest

from ai_xquanty.config import BacktestConfig
from ai_xquanty.backtest.engine import run_backtest, select_weekly_rebalance_dates


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
