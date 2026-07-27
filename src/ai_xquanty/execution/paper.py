import pandas as pd

from ai_xquanty.domain.models import (
    FillRecord,
    MarketDataBundle,
    OrderIntent,
    PositionSnapshot,
    TargetPortfolio,
)


def build_order_intents(
    current_positions: dict[str, PositionSnapshot],
    target: TargetPortfolio,
    prices: pd.Series,
    trade_date: pd.Timestamp,
    portfolio_value: float,
) -> list[OrderIntent]:
    """Build buy and sell intents with buy quantities rounded down to trading lots."""
    intents: list[OrderIntent] = []
    symbols = {
        symbol for symbol in target.weights if symbol != "CASH"
    } | set(current_positions.keys())
    for symbol in sorted(symbols):
        target_weight = target.weights.get(symbol, 0.0)
        target_quantity = int((portfolio_value * target_weight) / prices[symbol] / 100) * 100
        current_quantity = current_positions.get(symbol).quantity if symbol in current_positions else 0
        delta = target_quantity - current_quantity
        if delta > 0:
            buy_quantity = (delta // 100) * 100
            if buy_quantity == 0:
                continue
            intents.append(
                OrderIntent(
                    trade_date=trade_date.date(),
                    symbol=symbol,
                    side="BUY",
                    quantity=buy_quantity,
                )
            )
        elif delta < 0:
            position = current_positions[symbol]
            available_quantity = (
                position.available_quantity
                if position.available_quantity is not None
                else position.quantity
            )
            sell_quantity = min(abs(delta), available_quantity)
            if sell_quantity > 0:
                intents.append(
                    OrderIntent(
                        trade_date=trade_date.date(),
                        symbol=symbol,
                        side="SELL",
                        quantity=sell_quantity,
                    )
                )
    return intents


def simulate_next_day_fills(
    order_intents: list[OrderIntent],
    bundle: MarketDataBundle,
    trade_date: pd.Timestamp,
    commission_rate: float,
    stamp_duty_rate: float,
    transfer_fee_rate: float,
    slippage_bps: float,
) -> list[FillRecord]:
    """Fill tradable intents at the given session's opening price."""
    fills: list[FillRecord] = []
    for intent in order_intents:
        row = bundle.bars.loc[(trade_date, intent.symbol)]
        if bool(row["is_suspended"]):
            fills.append(
                FillRecord(
                    symbol=intent.symbol,
                    status="rejected_suspended",
                    quantity=0,
                    price=0.0,
                    fees=0.0,
                )
            )
            continue
        if intent.side == "BUY" and bool(row["is_limit_up"]):
            fills.append(
                FillRecord(
                    symbol=intent.symbol,
                    status="rejected_limit_up",
                    quantity=0,
                    price=0.0,
                    fees=0.0,
                )
            )
            continue
        if intent.side == "SELL" and bool(row["is_limit_down"]):
            fills.append(
                FillRecord(
                    symbol=intent.symbol,
                    status="rejected_limit_down",
                    quantity=0,
                    price=0.0,
                    fees=0.0,
                )
            )
            continue
        open_price = float(row["open"])
        if not pd.notna(open_price) or open_price <= 0:
            fills.append(
                FillRecord(
                    symbol=intent.symbol,
                    status="rejected_invalid_open_price",
                    quantity=0,
                    price=0.0,
                    fees=0.0,
                )
            )
            continue
        slippage_multiplier = 1.0 + slippage_bps / 10_000.0
        if intent.side == "SELL":
            slippage_multiplier = 1.0 - slippage_bps / 10_000.0
        price = open_price * slippage_multiplier
        fees = price * intent.quantity * (
            commission_rate
            + transfer_fee_rate
            + (stamp_duty_rate if intent.side == "SELL" else 0.0)
        )
        fills.append(
            FillRecord(
                symbol=intent.symbol,
                status="filled",
                quantity=intent.quantity,
                price=price,
                fees=fees,
            )
        )
    return fills
