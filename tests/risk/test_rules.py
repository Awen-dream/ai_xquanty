from ai_xquanty.domain.models import TargetPortfolio
from ai_xquanty.risk.rules import apply_risk_rules


def test_apply_risk_rules_forces_cash_when_drawdown_limit_is_breached() -> None:
    target = TargetPortfolio(
        strategy_name="etf_rotation", weights={"510300.SH": 0.90, "CASH": 0.10}
    )

    protected = apply_risk_rules(
        target,
        current_positions={},
        current_drawdown=0.11,
        max_single_weight=0.50,
        min_cash_weight=0.10,
        drawdown_stop=0.10,
    )

    assert protected.weights == {"CASH": 1.0}


def test_apply_risk_rules_clamps_weights_and_preserves_minimum_cash() -> None:
    target = TargetPortfolio(
        strategy_name="etf_rotation",
        weights={"510300.SH": 0.80, "510500.SH": 0.40, "CASH": 0.10},
    )

    protected = apply_risk_rules(
        target,
        current_positions={},
        current_drawdown=0.05,
        max_single_weight=0.50,
        min_cash_weight=0.20,
        drawdown_stop=0.10,
    )

    assert protected.weights == {"510300.SH": 0.50, "510500.SH": 0.40, "CASH": 0.20}
