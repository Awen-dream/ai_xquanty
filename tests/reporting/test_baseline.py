from pathlib import Path

import pandas as pd

from ai_xquanty.backtest.engine import BacktestResult
from ai_xquanty.reporting.baseline import compute_baseline_comparison
from ai_xquanty.reporting.render import write_backtest_artifacts


def test_compute_baseline_comparison_reports_strategy_and_baseline_returns(
    sample_bundle,
) -> None:
    """The comparison report exposes every strategy-versus-baseline metric."""
    equity_curve = pd.DataFrame(
        [
            {
                "trade_date": "2024-01-02",
                "cash": 1_000_000.0,
                "holdings_value": 0.0,
                "nav": 1_000_000.0,
            },
            {
                "trade_date": "2024-01-08",
                "cash": 550_000.0,
                "holdings_value": 460_000.0,
                "nav": 1_010_000.0,
            },
        ]
    )
    result = BacktestResult(
        equity_curve=equity_curve,
        fills=pd.DataFrame([{"status": "filled"}]),
        summary={
            "final_nav": 1_010_000.0,
            "max_drawdown": 0.0,
            "num_observations": 2.0,
        },
        baseline_comparison=None,
    )

    comparison = compute_baseline_comparison(
        result, sample_bundle, initial_cash=1_000_000.0
    )

    assert set(comparison) == {
        "strategy_total_return",
        "baseline_total_return",
        "excess_return",
        "strategy_max_drawdown",
        "baseline_max_drawdown",
        "num_filled_orders",
    }


def test_write_backtest_artifacts_writes_baseline_comparison_json(tmp_path: Path) -> None:
    """A result with a baseline comparison persists it as a separate JSON artifact."""
    result = BacktestResult(
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
        summary={"final_nav": 1.0, "max_drawdown": 0.0, "num_observations": 1.0},
        baseline_comparison={"strategy_total_return": 0.01},
    )

    write_backtest_artifacts(result, tmp_path)

    assert (tmp_path / "baseline_comparison.json").exists()
