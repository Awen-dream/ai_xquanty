import pandas as pd

from ai_xquanty.domain.models import PositionSnapshot, TargetPortfolio
from ai_xquanty.execution.paper import build_order_intents, simulate_next_day_fills


def test_build_order_intents_uses_full_lots_and_skips_cash() -> None:
    intents = build_order_intents(
        current_positions={},
        target=TargetPortfolio(
            strategy_name="etf_rotation", weights={"510300.SH": 0.90, "CASH": 0.10}
        ),
        prices=pd.Series({"510300.SH": 3.51}),
        trade_date=pd.Timestamp("2024-01-05"),
        portfolio_value=1_000_000.0,
    )

    assert [(intent.symbol, intent.side, intent.quantity) for intent in intents] == [
        ("510300.SH", "BUY", 256_400)
    ]


def test_build_order_intents_generates_sell_intents_with_t1_available_quantity() -> None:
    intents = build_order_intents(
        current_positions={
            "510300.SH": PositionSnapshot(
                symbol="510300.SH",
                quantity=500,
                available_quantity=200,
                average_cost=3.50,
            )
        },
        target=TargetPortfolio(strategy_name="etf_rotation", weights={"CASH": 1.0}),
        prices=pd.Series({"510300.SH": 3.51}),
        trade_date=pd.Timestamp("2024-01-05"),
        portfolio_value=1_000_000.0,
    )

    assert [(intent.symbol, intent.side, intent.quantity) for intent in intents] == [
        ("510300.SH", "SELL", 200)
    ]


def test_simulate_next_day_fills_marks_limit_up_buy_as_unfilled(sample_bundle) -> None:
    intents = build_order_intents(
        current_positions={},
        target=TargetPortfolio(
            strategy_name="etf_rotation", weights={"510300.SH": 0.90, "CASH": 0.10}
        ),
        prices=pd.Series({"510300.SH": 3.51}),
        trade_date=pd.Timestamp("2024-01-05"),
        portfolio_value=1_000_000.0,
    )

    fills = simulate_next_day_fills(
        intents,
        sample_bundle,
        trade_date=pd.Timestamp("2024-01-08"),
        commission_rate=0.0003,
        stamp_duty_rate=0.0,
        transfer_fee_rate=0.00001,
        slippage_bps=5.0,
    )

    assert fills[0].status == "rejected_limit_up"


def test_simulate_next_day_fills_applies_slippage_and_fees(sample_bundle) -> None:
    intents = build_order_intents(
        current_positions={},
        target=TargetPortfolio(
            strategy_name="etf_rotation", weights={"510300.SH": 0.01, "CASH": 0.99}
        ),
        prices=pd.Series({"510300.SH": 3.51}),
        trade_date=pd.Timestamp("2024-01-05"),
        portfolio_value=1_000_000.0,
    )

    fills = simulate_next_day_fills(
        intents,
        sample_bundle,
        trade_date=pd.Timestamp("2024-01-05"),
        commission_rate=0.0003,
        stamp_duty_rate=0.0,
        transfer_fee_rate=0.00001,
        slippage_bps=5.0,
    )

    assert fills[0].status == "filled"
    assert fills[0].price == 3.57 * 1.0005
    assert fills[0].fees == fills[0].price * fills[0].quantity * 0.00031


def test_simulate_next_day_fills_rejects_limit_down_sell(sample_bundle) -> None:
    intents = [
        type(
            "Intent",
            (),
            {
                "symbol": "510300.SH",
                "side": "SELL",
                "quantity": 100,
            },
        )()
    ]
    bundle = sample_bundle
    bundle.bars.loc[(pd.Timestamp("2024-01-08"), "510300.SH"), "is_limit_down"] = 1

    fills = simulate_next_day_fills(
        intents,
        bundle,
        trade_date=pd.Timestamp("2024-01-08"),
        commission_rate=0.0003,
        stamp_duty_rate=0.001,
        transfer_fee_rate=0.00001,
        slippage_bps=5.0,
    )

    assert fills[0].status == "rejected_limit_down"
