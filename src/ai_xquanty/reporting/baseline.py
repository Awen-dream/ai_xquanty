from typing import TYPE_CHECKING

import pandas as pd

from ai_xquanty.domain.models import MarketDataBundle
from ai_xquanty.reporting.metrics import compute_summary_metrics

if TYPE_CHECKING:
    from ai_xquanty.backtest.engine import BacktestResult


def compute_equal_weight_buy_and_hold(
    bundle: MarketDataBundle, initial_cash: float
) -> pd.DataFrame:
    """Value a portfolio equally allocated across all bundle instruments on day one."""
    symbols = list(bundle.instruments)
    first_date = bundle.calendar[0]
    first_closes = bundle.bars.xs(first_date, level="trade_date").loc[symbols, "close"]
    shares = initial_cash / len(symbols) / first_closes.astype(float)

    rows: list[dict[str, float | str]] = []
    for trade_date in bundle.calendar:
        closes = bundle.bars.xs(trade_date, level="trade_date").loc[symbols, "close"]
        nav = float((shares * closes.astype(float)).sum())
        rows.append(
            {
                "trade_date": trade_date.strftime("%Y-%m-%d"),
                "cash": 0.0,
                "holdings_value": nav,
                "nav": nav,
            }
        )
    return pd.DataFrame(rows)


def compute_baseline_comparison(
    result: "BacktestResult", bundle: MarketDataBundle, initial_cash: float
) -> dict[str, float]:
    """Compare a strategy result against an equal-weight buy-and-hold benchmark."""
    baseline_curve = compute_equal_weight_buy_and_hold(bundle, initial_cash)
    strategy_total_return = result.equity_curve["nav"].iloc[-1] / initial_cash - 1.0
    baseline_total_return = baseline_curve["nav"].iloc[-1] / initial_cash - 1.0
    return {
        "strategy_total_return": float(strategy_total_return),
        "baseline_total_return": float(baseline_total_return),
        "excess_return": float(strategy_total_return - baseline_total_return),
        "strategy_max_drawdown": float(
            compute_summary_metrics(result.equity_curve)["max_drawdown"]
        ),
        "baseline_max_drawdown": float(
            compute_summary_metrics(baseline_curve)["max_drawdown"]
        ),
        "num_filled_orders": float((result.fills["status"] == "filled").sum()),
    }
