import json
from pathlib import Path

import pandas as pd

from ai_xquanty.config import BacktestConfig
from ai_xquanty.backtest.engine import run_backtest
from ai_xquanty.reporting.render import write_backtest_artifacts


def test_write_backtest_artifacts_preserves_computed_result_contents(
    tmp_path: Path, repo_root: Path
) -> None:
    result = run_backtest(BacktestConfig.from_sample_data(repo_root))

    write_backtest_artifacts(result, tmp_path)

    written_equity_curve = pd.read_csv(tmp_path / "equity_curve.csv")
    written_fills = pd.read_csv(tmp_path / "fills.csv")
    with (tmp_path / "summary.json").open(encoding="utf-8") as handle:
        written_summary = json.load(handle)

    pd.testing.assert_frame_equal(written_equity_curve, result.equity_curve)
    pd.testing.assert_frame_equal(written_fills, result.fills)
    assert written_summary == result.summary
