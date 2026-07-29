from pathlib import Path

import pandas as pd

from ai_xquanty.config import BacktestConfig
from ai_xquanty.domain.models import Instrument, MarketDataBundle


def _read_table(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def _validate_calendar(calendar: pd.DatetimeIndex) -> None:
    if calendar.empty or not calendar.is_monotonic_increasing or not calendar.is_unique:
        raise ValueError("calendar must be non-empty, unique, and sorted")


def _validate_bars(
    bars: pd.DataFrame, calendar: pd.DatetimeIndex, instrument_symbols: tuple[str, ...]
) -> None:
    trade_dates = pd.to_datetime(bars["trade_date"], errors="coerce")
    if bars.duplicated(subset=["trade_date", "symbol"]).any():
        raise ValueError("bars contain duplicate rows")

    if trade_dates.isna().any() or not trade_dates.is_monotonic_increasing:
        raise ValueError("bars must be in chronological order")

    calendar_dates = set(calendar)
    if not set(trade_dates).issubset(calendar_dates):
        raise ValueError("bars contain dates outside the calendar")

    instrument_symbol_set = set(instrument_symbols)
    symbols = set(bars["symbol"])
    if not symbols.issubset(instrument_symbol_set):
        raise ValueError("bars contain undeclared symbols")

    expected_index = pd.MultiIndex.from_product(
        [calendar, instrument_symbols], names=["trade_date", "symbol"]
    )
    actual_index = pd.MultiIndex.from_frame(
        pd.DataFrame({"trade_date": trade_dates, "symbol": bars["symbol"]})
    )
    if not expected_index.equals(actual_index):
        raise ValueError("bars coverage does not match calendar x instruments")


def load_market_data(config: BacktestConfig) -> MarketDataBundle:
    calendar = pd.DatetimeIndex(pd.read_csv(config.calendar_path)["trade_date"])
    _validate_calendar(calendar)
    instruments_df = _read_table(config.instruments_path)
    bars = _read_table(config.bars_path)
    instruments = {
        row.symbol: Instrument(
            symbol=row.symbol,
            market=row.market,
            instrument_type=row.instrument_type,
            list_date=pd.Timestamp(row.list_date).date(),
            is_active=bool(row.is_active),
        )
        for row in instruments_df.itertuples(index=False)
    }
    _validate_bars(bars, calendar, tuple(instruments))
    bars["trade_date"] = pd.to_datetime(bars["trade_date"])
    bars = bars.sort_values(["trade_date", "symbol"]).set_index(["trade_date", "symbol"])
    return MarketDataBundle(calendar=calendar, instruments=instruments, bars=bars)
