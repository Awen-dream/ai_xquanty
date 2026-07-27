from pathlib import Path

from ai_xquanty.config import BacktestConfig
from ai_xquanty.backtest.engine import run_backtest
from ai_xquanty.reporting.render import write_backtest_artifacts


def test_write_backtest_artifacts_writes_equity_curve(
    tmp_path: Path, repo_root: Path
) -> None:
    result = run_backtest(BacktestConfig.from_sample_data(repo_root))

    write_backtest_artifacts(result, tmp_path)

    assert (tmp_path / "equity_curve.csv").exists()
