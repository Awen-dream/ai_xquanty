from ai_xquanty.domain.models import SignalSnapshot, TargetPortfolio


def build_target_portfolio(
    signals: list[SignalSnapshot],
    cash_buffer: float,
    max_positions: int,
) -> TargetPortfolio:
    if not 0 <= cash_buffer <= 1:
        raise ValueError("cash_buffer must be between 0 and 1")
    if max_positions <= 0:
        raise ValueError("max_positions must be positive")
    symbols = [signal.symbol for signal in signals]
    if len(symbols) != len(set(symbols)):
        raise ValueError("duplicate symbols are not supported")
    selected = signals[:max_positions]
    equity_weight = (1.0 - cash_buffer) / len(selected) if selected else 0.0
    weights = {signal.symbol: round(equity_weight, 6) for signal in selected}
    weights["CASH"] = round(1.0 - sum(weights.values()), 6)
    return TargetPortfolio(strategy_name="etf_rotation", weights=weights)
