from pathlib import Path

import pandas as pd
import pytest

from ai_xquanty.backtest.engine import BacktestResult
from ai_xquanty.cli import main
from ai_xquanty.config import BacktestConfig
from ai_xquanty.data.loaders import load_market_data


def test_backtest_config_points_to_bundled_sample_data(repo_root: Path) -> None:
    config = BacktestConfig.from_sample_data(repo_root)
    assert config.calendar_path.name == "calendar.csv"
    assert config.instruments_path.name == "instruments.csv"
    assert config.bars_path.name == "bars.csv"


def test_cli_without_subcommand_returns_zero() -> None:
    assert main([]) == 0


def test_cli_run_sample_backtest_writes_outputs(tmp_path: Path) -> None:
    exit_code = main(["run-sample-backtest", "--output-dir", str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "equity_curve.csv").exists()


def test_cli_run_real_backtest_writes_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = load_market_data(
        BacktestConfig.from_sample_data(Path(__file__).resolve().parents[1])
    )

    monkeypatch.setattr(
        "ai_xquanty.cli.prepare_real_market_data",
        lambda config, refresh=False: bundle,
    )
    monkeypatch.setattr(
        "ai_xquanty.cli.run_backtest_on_bundle",
        lambda config, bundle: BacktestResult(
            equity_curve=pd.DataFrame(
                [
                    {
                        "trade_date": "2024-01-02",
                        "cash": 1.0,
                        "holdings_value": 0.0,
                        "nav": 1.0,
                    }
                ]
            ),
            fills=pd.DataFrame(
                columns=[
                    "trade_date",
                    "symbol",
                    "side",
                    "status",
                    "quantity",
                    "price",
                    "fees",
                ]
            ),
            summary={
                "final_nav": 1.0,
                "max_drawdown": 0.0,
                "num_observations": 1.0,
            },
            baseline_comparison=None,
        ),
    )
    monkeypatch.setattr(
        "ai_xquanty.cli.compute_baseline_comparison",
        lambda result, bundle, initial_cash: {"strategy_total_return": 0.0},
    )

    exit_code = main(
        [
            "run-real-backtest",
            "--strategy",
            "trend_filter",
            "--start",
            "2021-07-28",
            "--end",
            "2026-07-27",
            "--symbols",
            "510300.SS,510500.SS,159915.SZ,159949.SZ",
            "--cache-dir",
            str(tmp_path / "cache"),
            "--output-dir",
            str(tmp_path / "report"),
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "report" / "summary.json").exists()
    assert (tmp_path / "report" / "baseline_comparison.json").exists()
