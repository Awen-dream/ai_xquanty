from pathlib import Path

import pandas as pd
import pytest

from ai_xquanty.config import BacktestConfig
from ai_xquanty.data.loaders import load_market_data


def _config_with_tables(
    tmp_path: Path,
    *,
    calendar: pd.DataFrame,
    instruments: pd.DataFrame,
    bars: pd.DataFrame,
) -> BacktestConfig:
    calendar_path = tmp_path / "calendar.csv"
    instruments_path = tmp_path / "instruments.csv"
    bars_path = tmp_path / "bars.csv"
    calendar.to_csv(calendar_path, index=False)
    instruments.to_csv(instruments_path, index=False)
    bars.to_csv(bars_path, index=False)
    return BacktestConfig(
        calendar_path=calendar_path,
        instruments_path=instruments_path,
        bars_path=bars_path,
    )


def _sample_tables(repo_root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sample_dir = repo_root / "data" / "sample"
    return (
        pd.read_csv(sample_dir / "calendar.csv"),
        pd.read_csv(sample_dir / "instruments.csv"),
        pd.read_csv(sample_dir / "bars.csv"),
    )


def test_load_market_data_builds_sorted_bundle(repo_root) -> None:
    config = BacktestConfig.from_sample_data(repo_root)

    bundle = load_market_data(config)

    assert bundle.calendar[0].strftime("%Y-%m-%d") == "2024-01-02"
    assert bundle.bars.index.names == ["trade_date", "symbol"]
    assert float(bundle.bars.loc[("2024-01-02", "510300.SH"), "close"]) == 3.51


@pytest.mark.parametrize(
    "trade_dates",
    [
        [],
        ["2024-01-03", "2024-01-02"],
        ["2024-01-02", "2024-01-02"],
    ],
    ids=["empty", "unsorted", "duplicate"],
)
def test_load_market_data_rejects_malformed_calendar(
    tmp_path: Path, repo_root: Path, trade_dates: list[str]
) -> None:
    _, instruments, bars = _sample_tables(repo_root)
    config = _config_with_tables(
        tmp_path,
        calendar=pd.DataFrame({"trade_date": trade_dates}),
        instruments=instruments,
        bars=bars[bars["trade_date"].isin(trade_dates)],
    )

    with pytest.raises(ValueError, match="calendar"):
        load_market_data(config)


def test_load_market_data_rejects_bars_outside_calendar(
    tmp_path: Path, repo_root: Path
) -> None:
    calendar, instruments, bars = _sample_tables(repo_root)
    calendar = calendar.iloc[:-1]
    config = _config_with_tables(
        tmp_path,
        calendar=calendar,
        instruments=instruments,
        bars=bars,
    )

    with pytest.raises(ValueError, match="outside the calendar"):
        load_market_data(config)


def test_load_market_data_rejects_duplicate_bars(
    tmp_path: Path, repo_root: Path
) -> None:
    calendar, instruments, bars = _sample_tables(repo_root)
    bars = pd.concat([bars, bars.iloc[[0]]], ignore_index=True)
    config = _config_with_tables(
        tmp_path,
        calendar=calendar,
        instruments=instruments,
        bars=bars,
    )

    with pytest.raises(ValueError, match="duplicate"):
        load_market_data(config)


def test_load_market_data_rejects_out_of_order_bar_dates(
    tmp_path: Path, repo_root: Path
) -> None:
    calendar, instruments, bars = _sample_tables(repo_root)
    bars = pd.concat([bars.iloc[[-1]], bars.iloc[:-1]], ignore_index=True)
    config = _config_with_tables(
        tmp_path,
        calendar=calendar,
        instruments=instruments,
        bars=bars,
    )

    with pytest.raises(ValueError, match="chronological"):
        load_market_data(config)


def test_load_market_data_rejects_undeclared_bar_symbol(
    tmp_path: Path, repo_root: Path
) -> None:
    calendar, instruments, bars = _sample_tables(repo_root)
    bars.loc[0, "symbol"] = "UNKNOWN"
    config = _config_with_tables(
        tmp_path,
        calendar=calendar,
        instruments=instruments,
        bars=bars,
    )

    with pytest.raises(ValueError, match="undeclared"):
        load_market_data(config)


def test_load_market_data_rejects_missing_expected_daily_bar(
    tmp_path: Path, repo_root: Path
) -> None:
    calendar, instruments, bars = _sample_tables(repo_root)
    bars = bars.drop(index=0)
    config = _config_with_tables(
        tmp_path,
        calendar=calendar,
        instruments=instruments,
        bars=bars,
    )

    with pytest.raises(ValueError, match="coverage"):
        load_market_data(config)
