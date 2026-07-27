from datetime import date

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
