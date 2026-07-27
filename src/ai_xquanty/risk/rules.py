import math

from ai_xquanty.domain.models import PositionSnapshot, TargetPortfolio


def apply_risk_rules(
    target: TargetPortfolio,
    current_positions: dict[str, PositionSnapshot],
    current_drawdown: float,
    max_single_weight: float,
    min_cash_weight: float,
    drawdown_stop: float,
) -> TargetPortfolio:
    """Return a target portfolio constrained by the account-level guardrails."""
    del current_positions
    if current_drawdown >= drawdown_stop:
        return TargetPortfolio(strategy_name=target.strategy_name, weights={"CASH": 1.0})

    clamped = {
        symbol: min(weight, max_single_weight)
        for symbol, weight in target.weights.items()
        if symbol != "CASH"
    }
    required_cash_weight = math.ceil(min_cash_weight * 1_000_000) / 1_000_000
    max_non_cash_weight = 1.0 - required_cash_weight
    total_non_cash_weight = sum(clamped.values())
    if total_non_cash_weight > max_non_cash_weight and total_non_cash_weight > 0:
        scale = max_non_cash_weight / total_non_cash_weight
        clamped = {
            symbol: round(weight * scale, 6) for symbol, weight in clamped.items()
        }
        overflow = round(sum(clamped.values()) - max_non_cash_weight, 6)
        if overflow > 0:
            largest_symbol = max(clamped, key=clamped.get)
            clamped[largest_symbol] = round(clamped[largest_symbol] - overflow, 6)
    cash_weight = round(1.0 - sum(clamped.values()), 6)
    clamped["CASH"] = round(cash_weight, 6)
    return TargetPortfolio(strategy_name=target.strategy_name, weights=clamped)
