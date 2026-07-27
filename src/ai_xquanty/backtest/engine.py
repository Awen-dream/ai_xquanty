from dataclasses import dataclass

import pandas as pd

from ai_xquanty.config import BacktestConfig
from ai_xquanty.data.loaders import load_market_data
from ai_xquanty.execution.paper import build_order_intents, simulate_next_day_fills
from ai_xquanty.portfolio.targets import build_target_portfolio
from ai_xquanty.reporting.metrics import compute_summary_metrics
from ai_xquanty.risk.rules import apply_risk_rules
from ai_xquanty.strategy.etf_rotation import compute_etf_signals


@dataclass(frozen=True)
class BacktestResult:
    equity_curve: pd.DataFrame
    fills: pd.DataFrame
    summary: dict[str, float]


def select_weekly_rebalance_dates(calendar: pd.DatetimeIndex) -> list[pd.Timestamp]:
    """Return each completed week's final trading session."""
    weeks = pd.Series(calendar, index=calendar).groupby(calendar.to_period("W-FRI")).max()
    return [pd.Timestamp(value) for value in weeks.tolist()[:-1]]


def run_backtest(config: BacktestConfig) -> BacktestResult:
    """Run deterministic weekly rebalances while recording NAV every session."""
    bundle = load_market_data(config)
    nav_rows: list[dict[str, float | str]] = []
    fill_rows: list[dict[str, float | int | str]] = []
    portfolio_value = config.initial_cash
    rebalance_dates = select_weekly_rebalance_dates(bundle.calendar)

    for rebalance_date in rebalance_dates:
        signals = compute_etf_signals(bundle, rebalance_date, lookback_days=3, top_n=2)
        target = build_target_portfolio(signals, cash_buffer=0.10, max_positions=2)
        protected = apply_risk_rules(
            target,
            current_positions={},
            current_drawdown=0.0,
            max_single_weight=0.50,
            min_cash_weight=0.10,
            drawdown_stop=0.10,
        )
        prices = bundle.bars.xs(rebalance_date, level="trade_date")["close"]
        intents = build_order_intents(
            {}, protected, prices, rebalance_date, portfolio_value
        )
        next_trade_date = bundle.calendar[
            bundle.calendar.get_loc(rebalance_date) + 1
        ]
        fills = simulate_next_day_fills(
            intents,
            bundle,
            next_trade_date,
            commission_rate=0.0003,
            stamp_duty_rate=0.0,
            transfer_fee_rate=0.00001,
            slippage_bps=5.0,
        )
        fill_rows.extend(fill.__dict__ for fill in fills)

    for trade_date in bundle.calendar:
        nav_rows.append(
            {"trade_date": trade_date.strftime("%Y-%m-%d"), "nav": portfolio_value}
        )

    equity_curve = pd.DataFrame(nav_rows)
    fills_df = pd.DataFrame(fill_rows)
    return BacktestResult(
        equity_curve=equity_curve,
        fills=fills_df,
        summary=compute_summary_metrics(equity_curve),
    )
