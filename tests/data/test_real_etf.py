from pathlib import Path

import pandas as pd
import pytest

from ai_xquanty.config import RealBacktestConfig
from ai_xquanty.data.real_etf import prepare_real_market_data


def test_prepare_real_market_data_builds_bundle_from_downloaded_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_download(symbol, start, end, auto_adjust, multi_level_index, progress):
        index = pd.to_datetime(["2021-07-28", "2021-07-29"])
        return pd.DataFrame(
            {
                "Open": [3.50, 3.55],
                "High": [3.52, 3.57],
                "Low": [3.48, 3.54],
                "Close": [3.51, 3.56],
                "Volume": [1000, 1200],
            },
            index=index,
        )

    monkeypatch.setattr("ai_xquanty.data.real_etf.yf.download", fake_download)
    config = RealBacktestConfig(
        start="2021-07-28",
        end="2021-07-29",
        symbols=("510300.SS",),
        cache_dir=tmp_path,
        initial_cash=1_000_000.0,
        strategy_name="trend_filter",
    )

    bundle = prepare_real_market_data(config, refresh=True)

    assert list(bundle.instruments) == ["510300.SS"]
    assert bundle.calendar.tolist() == [
        pd.Timestamp("2021-07-28"),
        pd.Timestamp("2021-07-29"),
    ]
    assert float(bundle.bars.loc[(pd.Timestamp("2021-07-28"), "510300.SS"), "close"]) == 3.51
    assert (tmp_path / "510300.SS.csv").exists()


def test_prepare_real_market_data_rejects_empty_download(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "ai_xquanty.data.real_etf.yf.download",
        lambda *args, **kwargs: pd.DataFrame(),
    )
    config = RealBacktestConfig(
        start="2021-07-28",
        end="2021-07-29",
        symbols=("510300.SS",),
        cache_dir=tmp_path,
        initial_cash=1_000_000.0,
        strategy_name="trend_filter",
    )

    with pytest.raises(ValueError, match="empty"):
        prepare_real_market_data(config, refresh=True)


def test_prepare_real_market_data_uses_cache_when_refresh_is_false(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache_file = tmp_path / "510300.SS.csv"
    pd.DataFrame(
        {
            "trade_date": ["2021-07-28", "2021-07-29"],
            "symbol": ["510300.SS", "510300.SS"],
            "open": [3.50, 3.55],
            "high": [3.52, 3.57],
            "low": [3.48, 3.54],
            "close": [3.51, 3.56],
            "volume": [1000, 1200],
        }
    ).to_csv(cache_file, index=False)

    def fail_download(*args, **kwargs):
        raise AssertionError("download should not run")

    monkeypatch.setattr("ai_xquanty.data.real_etf.yf.download", fail_download)
    config = RealBacktestConfig(
        start="2021-07-28",
        end="2021-07-29",
        symbols=("510300.SS",),
        cache_dir=tmp_path,
        initial_cash=1_000_000.0,
        strategy_name="trend_filter",
    )

    bundle = prepare_real_market_data(config, refresh=False)

    assert len(bundle.calendar) == 2


def test_prepare_real_market_data_redownloads_when_cache_does_not_cover_requested_range(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache_file = tmp_path / "510300.SS.csv"
    pd.DataFrame(
        {
            "trade_date": ["2021-07-28", "2021-07-29"],
            "symbol": ["510300.SS", "510300.SS"],
            "open": [3.50, 3.55],
            "high": [3.52, 3.57],
            "low": [3.48, 3.54],
            "close": [3.51, 3.56],
            "volume": [1000, 1200],
        }
    ).to_csv(cache_file, index=False)

    calls: list[tuple[str, str, str]] = []

    def fake_download(symbol, start, end, auto_adjust, multi_level_index, progress):
        calls.append((symbol, start, end))
        return pd.DataFrame(
            {
                "Open": [3.50, 3.55, 3.60],
                "High": [3.52, 3.57, 3.62],
                "Low": [3.48, 3.54, 3.58],
                "Close": [3.51, 3.56, 3.61],
                "Volume": [1000, 1200, 1300],
            },
            index=pd.to_datetime(["2021-07-28", "2021-07-29", "2021-07-30"]),
        )

    monkeypatch.setattr("ai_xquanty.data.real_etf.yf.download", fake_download)
    config = RealBacktestConfig(
        start="2021-07-28",
        end="2021-07-30",
        symbols=("510300.SS",),
        cache_dir=tmp_path,
    )

    bundle = prepare_real_market_data(config, refresh=False)

    assert calls == [("510300.SS", "2021-07-28", "2021-07-31")]
    assert bundle.calendar.tolist() == [
        pd.Timestamp("2021-07-28"),
        pd.Timestamp("2021-07-29"),
        pd.Timestamp("2021-07-30"),
    ]


def test_prepare_real_market_data_reuses_fresh_cache_for_same_inclusive_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def fake_download(symbol, start, end, auto_adjust, multi_level_index, progress):
        calls.append(end)
        if end == "2021-07-30":
            index = pd.to_datetime(["2021-07-28", "2021-07-29"])
        else:
            index = pd.to_datetime(["2021-07-28", "2021-07-29", "2021-07-30"])
        return pd.DataFrame(
            {
                "Open": [3.50, 3.55, 3.60][: len(index)],
                "High": [3.52, 3.57, 3.62][: len(index)],
                "Low": [3.48, 3.54, 3.58][: len(index)],
                "Close": [3.51, 3.56, 3.61][: len(index)],
                "Volume": [1000, 1200, 1300][: len(index)],
            },
            index=index,
        )

    monkeypatch.setattr("ai_xquanty.data.real_etf.yf.download", fake_download)
    config = RealBacktestConfig(
        start="2021-07-28",
        end="2021-07-30",
        symbols=("510300.SS",),
        cache_dir=tmp_path,
    )

    first_bundle = prepare_real_market_data(config, refresh=True)
    second_bundle = prepare_real_market_data(config, refresh=False)

    assert calls == ["2021-07-31"]
    assert first_bundle.calendar.tolist() == [
        pd.Timestamp("2021-07-28"),
        pd.Timestamp("2021-07-29"),
        pd.Timestamp("2021-07-30"),
    ]
    assert second_bundle.calendar.tolist() == first_bundle.calendar.tolist()


def test_prepare_real_market_data_rejects_nonpositive_close_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_download(*args, **kwargs):
        return pd.DataFrame(
            {
                "Open": [3.50],
                "High": [3.52],
                "Low": [3.48],
                "Close": [0.0],
                "Volume": [1000],
            },
            index=pd.to_datetime(["2021-07-28"]),
        )

    monkeypatch.setattr("ai_xquanty.data.real_etf.yf.download", fake_download)
    config = RealBacktestConfig(
        start="2021-07-28",
        end="2021-07-29",
        symbols=("510300.SS",),
        cache_dir=tmp_path,
    )

    with pytest.raises(ValueError, match="close"):
        prepare_real_market_data(config, refresh=True)


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("open", float("inf")),
        ("high", float("nan")),
        ("low", float("inf")),
        ("volume", float("nan")),
    ],
)
def test_prepare_real_market_data_rejects_invalid_ohlcv_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    column: str,
    value: float,
) -> None:
    def fake_download(*args, **kwargs):
        row = {
            "Open": [3.50],
            "High": [3.52],
            "Low": [3.48],
            "Close": [3.51],
            "Volume": [1000.0],
        }
        row[column.capitalize()] = [value]
        return pd.DataFrame(
            row,
            index=pd.to_datetime(["2021-07-28"]),
        )

    monkeypatch.setattr("ai_xquanty.data.real_etf.yf.download", fake_download)
    config = RealBacktestConfig(
        start="2021-07-28",
        end="2021-07-29",
        symbols=("510300.SS",),
        cache_dir=tmp_path,
    )

    with pytest.raises(ValueError, match=column):
        prepare_real_market_data(config, refresh=True)


@pytest.mark.parametrize(
    ("start", "end"),
    [
        (None, "2021-07-29"),
        ("2021-07-28", None),
        ("today", "2021-07-29"),
        ("2021-07-28", "now"),
    ],
)
def test_real_backtest_config_rejects_non_explicit_dates(
    tmp_path: Path, start: object, end: object
) -> None:
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        RealBacktestConfig(
            start=start,
            end=end,
            symbols=("510300.SS",),
            cache_dir=tmp_path,
        )
