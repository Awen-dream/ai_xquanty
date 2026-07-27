from pathlib import Path

from ai_xquanty.cli import main
from ai_xquanty.config import BacktestConfig


def test_backtest_config_points_to_bundled_sample_data(repo_root: Path) -> None:
    config = BacktestConfig.from_sample_data(repo_root)
    assert config.calendar_path.name == "calendar.csv"
    assert config.instruments_path.name == "instruments.csv"
    assert config.bars_path.name == "bars.csv"


def test_cli_without_subcommand_returns_zero() -> None:
    assert main([]) == 0
