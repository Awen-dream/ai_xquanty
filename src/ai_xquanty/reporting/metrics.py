import pandas as pd


def compute_summary_metrics(equity_curve: pd.DataFrame) -> dict[str, float]:
    """Compute the summary fields emitted with every backtest report."""
    nav = equity_curve["nav"].astype(float)
    running_peak = nav.cummax()
    drawdown = (nav / running_peak - 1.0).fillna(0.0)
    return {
        "final_nav": float(nav.iloc[-1]),
        "max_drawdown": float(abs(drawdown.min())),
        "num_observations": float(len(equity_curve)),
    }
