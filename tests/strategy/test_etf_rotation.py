import pandas as pd
import pytest

from ai_xquanty.strategy.etf_rotation import compute_etf_signals


def test_compute_etf_signals_ranks_by_trailing_return(sample_bundle) -> None:
    signals = compute_etf_signals(
        sample_bundle,
        as_of=pd.Timestamp("2024-01-08"),
        lookback_days=3,
        top_n=2,
    )

    assert [signal.symbol for signal in signals] == ["510300.SH", "510500.SH"]


def test_compute_etf_signals_rejects_insufficient_history(sample_bundle) -> None:
    with pytest.raises(ValueError, match="lookback"):
        compute_etf_signals(
            sample_bundle,
            as_of=pd.Timestamp("2024-01-03"),
            lookback_days=3,
            top_n=2,
        )


def test_compute_etf_signals_rejects_missing_close(sample_bundle) -> None:
    sample_bundle.bars.loc[("2024-01-08", "510300.SH"), "close"] = float("nan")

    with pytest.raises(ValueError, match="close"):
        compute_etf_signals(
            sample_bundle,
            as_of=pd.Timestamp("2024-01-08"),
            lookback_days=3,
            top_n=2,
        )


def test_compute_etf_signals_rejects_zero_close(sample_bundle) -> None:
    sample_bundle.bars.loc[("2024-01-08", "510300.SH"), "close"] = 0.0

    with pytest.raises(ValueError, match="close"):
        compute_etf_signals(
            sample_bundle,
            as_of=pd.Timestamp("2024-01-08"),
            lookback_days=3,
            top_n=2,
        )
