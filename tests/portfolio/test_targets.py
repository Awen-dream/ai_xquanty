from datetime import date

import pytest

from ai_xquanty.domain.models import SignalSnapshot
from ai_xquanty.portfolio.targets import build_target_portfolio


def test_build_target_portfolio_reserves_cash_buffer() -> None:
    signals = [
        SignalSnapshot(
            trade_date=date(2024, 1, 8),
            strategy_name="etf_rotation",
            symbol="510300.SH",
            score=0.06,
        ),
        SignalSnapshot(
            trade_date=date(2024, 1, 8),
            strategy_name="etf_rotation",
            symbol="510500.SH",
            score=0.04,
        ),
    ]

    target = build_target_portfolio(signals, cash_buffer=0.10, max_positions=2)

    assert target.weights == {"510300.SH": 0.45, "510500.SH": 0.45, "CASH": 0.10}


@pytest.mark.parametrize("cash_buffer", [-0.01, 1.01])
def test_build_target_portfolio_rejects_out_of_range_cash_buffer(cash_buffer: float) -> None:
    with pytest.raises(ValueError, match="cash_buffer"):
        build_target_portfolio([], cash_buffer=cash_buffer, max_positions=1)


@pytest.mark.parametrize("max_positions", [0, -1])
def test_build_target_portfolio_rejects_non_positive_max_positions(max_positions: int) -> None:
    with pytest.raises(ValueError, match="max_positions"):
        build_target_portfolio([], cash_buffer=0.10, max_positions=max_positions)


def test_build_target_portfolio_rejects_duplicate_symbols() -> None:
    duplicate = SignalSnapshot(
        trade_date=date(2024, 1, 8),
        strategy_name="etf_rotation",
        symbol="510300.SH",
        score=0.06,
    )

    with pytest.raises(ValueError, match="duplicate"):
        build_target_portfolio([duplicate, duplicate], cash_buffer=0.10, max_positions=2)
