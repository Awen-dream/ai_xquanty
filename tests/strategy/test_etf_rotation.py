import pandas as pd

from ai_xquanty.strategy.etf_rotation import compute_etf_signals


def test_compute_etf_signals_ranks_by_trailing_return(sample_bundle) -> None:
    signals = compute_etf_signals(
        sample_bundle,
        as_of=pd.Timestamp("2024-01-08"),
        lookback_days=3,
        top_n=2,
    )

    assert [signal.symbol for signal in signals] == ["510300.SH", "510500.SH"]
