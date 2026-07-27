from dataclasses import dataclass
import math

import pandas as pd

from ai_xquanty.config import BacktestConfig
from ai_xquanty.data.loaders import load_market_data
from ai_xquanty.domain.models import FillRecord, OrderIntent, PositionSnapshot
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


def _make_positions_available(
    positions: dict[str, PositionSnapshot],
) -> dict[str, PositionSnapshot]:
    """Release positions bought on a prior session for T+1 selling."""
    return {
        symbol: PositionSnapshot(
            symbol=position.symbol,
            quantity=position.quantity,
            average_cost=position.average_cost,
            available_quantity=position.quantity,
        )
        for symbol, position in positions.items()
    }


def _apply_fill(
    cash: float,
    positions: dict[str, PositionSnapshot],
    intent: OrderIntent,
    fill: FillRecord,
) -> tuple[float, dict[str, PositionSnapshot]]:
    """Apply a filled order to cash and positions; rejected orders are no-ops."""
    if fill.status != "filled":
        return cash, positions

    gross_value = fill.price * fill.quantity
    updated = dict(positions)
    if intent.side == "BUY":
        existing = updated.get(intent.symbol)
        prior_quantity = existing.quantity if existing else 0
        prior_cost = existing.average_cost * prior_quantity if existing else 0.0
        total_quantity = prior_quantity + fill.quantity
        updated[intent.symbol] = PositionSnapshot(
            symbol=intent.symbol,
            quantity=total_quantity,
            average_cost=(prior_cost + gross_value + fill.fees) / total_quantity,
            available_quantity=existing.available_quantity if existing else 0,
        )
        return cash - gross_value - fill.fees, updated

    existing = updated[intent.symbol]
    remaining_quantity = existing.quantity - fill.quantity
    if remaining_quantity:
        available_quantity = max((existing.available_quantity or 0) - fill.quantity, 0)
        updated[intent.symbol] = PositionSnapshot(
            symbol=intent.symbol,
            quantity=remaining_quantity,
            average_cost=existing.average_cost,
            available_quantity=available_quantity,
        )
    else:
        del updated[intent.symbol]
    return cash + gross_value - fill.fees, updated


def _mark_holdings_to_market(
    positions: dict[str, PositionSnapshot], bars: pd.DataFrame
) -> float:
    """Value every open position at the session close."""
    value = 0.0
    for symbol, position in positions.items():
        price = float(bars.loc[symbol, "close"])
        if not math.isfinite(price) or price <= 0:
            raise ValueError(f"Invalid close price for {symbol}")
        value += position.quantity * price
    return value


def run_backtest(config: BacktestConfig) -> BacktestResult:
    """Run weekly rebalances, next-session fills, and daily mark-to-market NAV."""
    bundle = load_market_data(config)
    nav_rows: list[dict[str, float | str]] = []
    fill_rows: list[dict[str, float | int | str]] = []
    scheduled_fills: dict[pd.Timestamp, list[tuple[OrderIntent, FillRecord]]] = {}
    positions: dict[str, PositionSnapshot] = {}
    cash = config.initial_cash
    peak_nav = config.initial_cash
    rebalance_dates = set(select_weekly_rebalance_dates(bundle.calendar))

    for date_index, trade_date in enumerate(bundle.calendar):
        positions = _make_positions_available(positions)
        for intent, fill in scheduled_fills.pop(trade_date, []):
            cash, positions = _apply_fill(cash, positions, intent, fill)

        session_bars = bundle.bars.xs(trade_date, level="trade_date")
        holdings_value = _mark_holdings_to_market(positions, session_bars)
        portfolio_value = cash + holdings_value
        peak_nav = max(peak_nav, portfolio_value)
        current_drawdown = 1.0 - portfolio_value / peak_nav
        nav_rows.append(
            {
                "trade_date": trade_date.strftime("%Y-%m-%d"),
                "cash": cash,
                "holdings_value": holdings_value,
                "nav": portfolio_value,
            }
        )

        if trade_date not in rebalance_dates:
            continue

        signals = compute_etf_signals(bundle, trade_date, lookback_days=3, top_n=2)
        target = build_target_portfolio(signals, cash_buffer=0.10, max_positions=2)
        protected = apply_risk_rules(
            target,
            current_positions=positions,
            current_drawdown=current_drawdown,
            max_single_weight=0.50,
            min_cash_weight=0.10,
            drawdown_stop=0.10,
        )
        prices = session_bars["close"]
        intents = build_order_intents(
            positions, protected, prices, trade_date, portfolio_value
        )
        next_trade_date = bundle.calendar[date_index + 1]
        fills = simulate_next_day_fills(
            intents,
            bundle,
            next_trade_date,
            commission_rate=0.0003,
            stamp_duty_rate=0.0,
            transfer_fee_rate=0.00001,
            slippage_bps=5.0,
        )
        scheduled_fills[next_trade_date] = list(zip(intents, fills, strict=True))
        fill_rows.extend(
            {
                "trade_date": next_trade_date.strftime("%Y-%m-%d"),
                "symbol": intent.symbol,
                "side": intent.side,
                **fill.__dict__,
            }
            for intent, fill in zip(intents, fills, strict=True)
        )

    equity_curve = pd.DataFrame(nav_rows)
    fills_df = pd.DataFrame(
        fill_rows,
        columns=["trade_date", "symbol", "side", "status", "quantity", "price", "fees"],
    )
    return BacktestResult(
        equity_curve=equity_curve,
        fills=fills_df,
        summary=compute_summary_metrics(equity_curve),
    )
