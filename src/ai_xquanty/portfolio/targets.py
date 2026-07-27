from ai_xquanty.domain.models import SignalSnapshot, TargetPortfolio


def build_target_portfolio(
    signals: list[SignalSnapshot],
    cash_buffer: float,
    max_positions: int,
) -> TargetPortfolio:
    selected = signals[:max_positions]
    equity_weight = (1.0 - cash_buffer) / len(selected) if selected else 0.0
    weights = {signal.symbol: round(equity_weight, 6) for signal in selected}
    weights["CASH"] = round(1.0 - sum(weights.values()), 6)
    return TargetPortfolio(strategy_name="etf_rotation", weights=weights)
