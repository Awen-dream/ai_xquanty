import json
from pathlib import Path

from ai_xquanty.backtest.engine import BacktestResult


def write_backtest_artifacts(result: BacktestResult, output_dir: Path) -> None:
    """Write the tabular and JSON artifacts for a backtest result."""
    output_dir.mkdir(parents=True, exist_ok=True)
    result.equity_curve.to_csv(output_dir / "equity_curve.csv", index=False)
    result.fills.to_csv(output_dir / "fills.csv", index=False)
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(result.summary, handle, indent=2, ensure_ascii=False)
