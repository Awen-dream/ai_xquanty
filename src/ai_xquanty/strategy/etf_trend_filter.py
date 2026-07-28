import numpy as np
import pandas as pd

from ai_xquanty.domain.models import MarketDataBundle, SignalSnapshot


def compute_trend_filter_signals(
    bundle: MarketDataBundle,
    as_of: pd.Timestamp,
    lookback_days: int,
    short_window: int,
    long_window: int,
    top_n: int,
) -> list[SignalSnapshot]:
    if lookback_days < 1:
        raise ValueError("lookback_days must be positive")
    if short_window < 1 or long_window < 1:
        raise ValueError("moving-average windows must be positive")
    if short_window > long_window:
        raise ValueError("short_window cannot exceed long_window")
    if top_n < 1:
        raise ValueError("top_n must be positive")

    closes = bundle.bars["close"].unstack("symbol").sort_index()
    required_history = max(lookback_days + 1, long_window)
    window = closes.loc[:as_of].tail(required_history)
    if len(window) < required_history:
        raise ValueError("Insufficient history for trend filter")

    close_values = window.to_numpy(dtype=float)
    if not np.isfinite(close_values).all() or (close_values <= 0).any():
        raise ValueError("Trend filter history contains invalid close prices")

    trailing_returns = window.iloc[-1] / window.iloc[-(lookback_days + 1)] - 1.0
    short_ma = window.tail(short_window).mean()
    long_ma = window.tail(long_window).mean()
    latest_close = window.iloc[-1]
    eligible = (latest_close > long_ma) & (short_ma > long_ma)
    ranked = trailing_returns[eligible].sort_values(ascending=False).head(top_n)
    return [
        SignalSnapshot(
            trade_date=as_of.date(),
            strategy_name="etf_trend_filter",
            symbol=symbol,
            score=float(score),
        )
        for symbol, score in ranked.items()
    ]
