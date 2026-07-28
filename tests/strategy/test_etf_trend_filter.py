import pandas as pd
import pytest

from ai_xquanty.strategy.etf_trend_filter import compute_trend_filter_signals


def test_compute_trend_filter_signals_ranks_only_symbols_above_long_trend(
    sample_bundle,
) -> None:
    signals = compute_trend_filter_signals(
        sample_bundle,
        as_of=pd.Timestamp("2024-01-08"),
        lookback_days=3,
        short_window=2,
        long_window=4,
        top_n=2,
    )

    assert [signal.symbol for signal in signals] == ["510300.SH", "510500.SH"]
    assert all(signal.strategy_name == "etf_trend_filter" for signal in signals)


def test_compute_trend_filter_signals_returns_empty_when_no_symbol_passes_filter(
    sample_bundle,
) -> None:
    sample_bundle.bars.loc[(pd.Timestamp("2024-01-08"), slice(None)), "close"] = 1.0

    signals = compute_trend_filter_signals(
        sample_bundle,
        as_of=pd.Timestamp("2024-01-08"),
        lookback_days=3,
        short_window=2,
        long_window=4,
        top_n=2,
    )

    assert signals == []


def test_compute_trend_filter_signals_rejects_insufficient_history(sample_bundle) -> None:
    with pytest.raises(ValueError, match="history"):
        compute_trend_filter_signals(
            sample_bundle,
            as_of=pd.Timestamp("2024-01-03"),
            lookback_days=3,
            short_window=2,
            long_window=4,
            top_n=2,
        )


def test_compute_trend_filter_signals_rejects_invalid_close(sample_bundle) -> None:
    sample_bundle.bars.loc[(pd.Timestamp("2024-01-08"), "510300.SH"), "close"] = float(
        "nan"
    )

    with pytest.raises(ValueError, match="close"):
        compute_trend_filter_signals(
            sample_bundle,
            as_of=pd.Timestamp("2024-01-08"),
            lookback_days=3,
            short_window=2,
            long_window=4,
            top_n=2,
        )
