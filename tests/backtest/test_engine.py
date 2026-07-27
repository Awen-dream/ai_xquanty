from pathlib import Path

import pandas as pd

from ai_xquanty.config import BacktestConfig
from ai_xquanty.backtest.engine import run_backtest, select_weekly_rebalance_dates
from ai_xquanty.reporting.render import write_backtest_artifacts


def test_run_backtest_returns_deterministic_summary(
    repo_root: Path, tmp_path: Path
) -> None:
    result = run_backtest(BacktestConfig.from_sample_data(repo_root))

    assert result.summary["final_nav"] > 0.0
    assert result.summary["max_drawdown"] <= 0.10
    write_backtest_artifacts(result, tmp_path)
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "fills.csv").exists()


def test_write_backtest_artifacts_writes_equity_curve(
    tmp_path: Path, repo_root: Path
) -> None:
    result = run_backtest(BacktestConfig.from_sample_data(repo_root))

    write_backtest_artifacts(result, tmp_path)

    assert (tmp_path / "equity_curve.csv").exists()


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
