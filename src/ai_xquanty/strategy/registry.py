from collections.abc import Callable

import pandas as pd

from ai_xquanty.domain.models import MarketDataBundle, SignalSnapshot
from ai_xquanty.strategy.etf_rotation import compute_etf_signals
from ai_xquanty.strategy.etf_trend_filter import compute_trend_filter_signals


def resolve_signal_fn(
    strategy_name: str,
) -> Callable[[MarketDataBundle, pd.Timestamp], list[SignalSnapshot]]:
    if strategy_name == "rotation":
        return lambda bundle, as_of: compute_etf_signals(
            bundle, as_of, lookback_days=3, top_n=2
        )
    if strategy_name == "trend_filter":
        return lambda bundle, as_of: compute_trend_filter_signals(
            bundle,
            as_of,
            lookback_days=3,
            short_window=2,
            long_window=4,
            top_n=2,
        )
    raise ValueError(f"Unsupported strategy: {strategy_name}")
