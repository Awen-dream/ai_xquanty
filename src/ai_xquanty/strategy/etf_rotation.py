import numpy as np
import pandas as pd

from ai_xquanty.domain.models import MarketDataBundle, SignalSnapshot


def compute_etf_signals(
    bundle: MarketDataBundle,
    as_of: pd.Timestamp,
    lookback_days: int,
    top_n: int,
) -> list[SignalSnapshot]:
    closes = bundle.bars["close"].unstack("symbol").sort_index()
    window = closes.loc[:as_of].tail(lookback_days + 1)
    if len(window) < lookback_days + 1:
        raise ValueError("Insufficient history for the requested lookback")
    close_values = window.to_numpy(dtype=float)
    if not np.isfinite(close_values).all() or (close_values <= 0).any():
        raise ValueError("Lookback window contains invalid close prices")
    trailing_returns = window.iloc[-1] / window.iloc[0] - 1.0
    ranked = trailing_returns.sort_values(ascending=False).head(top_n)
    return [
        SignalSnapshot(
            trade_date=as_of.date(),
            strategy_name="etf_rotation",
            symbol=symbol,
            score=float(score),
        )
        for symbol, score in ranked.items()
    ]
