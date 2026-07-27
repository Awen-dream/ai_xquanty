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
    cash_weight = max(min_cash_weight, 1.0 - sum(clamped.values()))
    clamped["CASH"] = round(cash_weight, 6)
    return TargetPortfolio(strategy_name=target.strategy_name, weights=clamped)
