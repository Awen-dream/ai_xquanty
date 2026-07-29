from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from ai_xquanty.config import RealBacktestConfig
from ai_xquanty.domain.models import Instrument, MarketDataBundle


_PRICE_COLUMNS = ("open", "high", "low", "close", "volume")


def _date_bounds(start: str, end: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    return pd.Timestamp(start), pd.Timestamp(end)


def _download_end(end: str) -> str:
    return (date.fromisoformat(end) + timedelta(days=1)).isoformat()


def _normalise_symbol_frame(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    if frame.empty:
        raise ValueError(f"empty data returned for {symbol}")

    normalised = frame.copy()
    normalised.columns = [str(column).lower() for column in normalised.columns]
    missing_columns = set(_PRICE_COLUMNS).difference(normalised.columns)
    if missing_columns:
        raise ValueError(f"invalid data for {symbol}: missing {sorted(missing_columns)}")

    normalised["trade_date"] = pd.to_datetime(normalised.index, errors="coerce")
    normalised["symbol"] = symbol
    return _validate_and_complete_frame(normalised, symbol)


def _validate_and_complete_frame(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    required_columns = {"trade_date", "symbol", *_PRICE_COLUMNS}
    missing_columns = required_columns.difference(frame.columns)
    if missing_columns:
        raise ValueError(f"invalid data for {symbol}: missing {sorted(missing_columns)}")
    if frame.empty:
        raise ValueError(f"empty data returned for {symbol}")

    normalised = frame.copy()
    normalised["trade_date"] = pd.to_datetime(normalised["trade_date"], errors="coerce")
    if normalised["trade_date"].isna().any():
        raise ValueError(f"invalid data for {symbol}: trade_date")

    for column in _PRICE_COLUMNS:
        normalised[column] = pd.to_numeric(normalised[column], errors="coerce")
        values = normalised[column]
        if values.isna().any() or not np.isfinite(values).all():
            raise ValueError(f"invalid {column} data for {symbol}")
    if (normalised["close"] <= 0).any():
        raise ValueError(f"invalid close data for {symbol}")

    normalised["turnover"] = normalised.get("turnover", normalised["close"] * normalised["volume"])
    for column in ("is_suspended", "is_limit_up", "is_limit_down"):
        normalised[column] = normalised.get(column, 0)
    return normalised[
        [
            "trade_date",
            "symbol",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "turnover",
            "is_suspended",
            "is_limit_up",
            "is_limit_down",
        ]
    ]


def _filter_frame_to_requested_range(
    frame: pd.DataFrame, symbol: str, start: str, end: str
) -> pd.DataFrame:
    start_date, end_date = _date_bounds(start, end)
    filtered = frame.loc[
        (frame["trade_date"] >= start_date) & (frame["trade_date"] <= end_date)
    ].copy()
    if filtered.empty:
        raise ValueError(f"empty data returned for {symbol} between {start} and {end}")
    return filtered


def _frame_covers_requested_range(frame: pd.DataFrame, start: str, end: str) -> bool:
    start_date, end_date = _date_bounds(start, end)
    available_dates = frame["trade_date"]
    return available_dates.min() <= start_date and available_dates.max() >= end_date


def _load_or_download_symbol(
    symbol: str, start: str, end: str, cache_dir: Path, refresh: bool
) -> pd.DataFrame:
    cache_file = cache_dir / f"{symbol}.csv"
    if cache_file.exists() and not refresh:
        cached = _validate_and_complete_frame(pd.read_csv(cache_file), symbol)
        if _frame_covers_requested_range(cached, start, end):
            return _filter_frame_to_requested_range(cached, symbol, start, end)

    downloaded = yf.download(
        symbol,
        start=start,
        end=_download_end(end),
        auto_adjust=False,
        multi_level_index=False,
        progress=False,
    )
    frame = _filter_frame_to_requested_range(
        _normalise_symbol_frame(downloaded, symbol), symbol, start, end
    )
    cache_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(cache_file, index=False)
    return frame


def prepare_real_market_data(
    config: RealBacktestConfig, refresh: bool = False
) -> MarketDataBundle:
    if not config.symbols:
        raise ValueError("symbols must not be empty")

    frames = [
        _load_or_download_symbol(
            symbol, config.start, config.end, config.cache_dir, refresh
        )
        for symbol in config.symbols
    ]
    bars = pd.concat(frames, ignore_index=True).sort_values(["trade_date", "symbol"])
    calendar = pd.DatetimeIndex(sorted(bars["trade_date"].drop_duplicates()))
    instruments = {
        symbol: Instrument(
            symbol=symbol,
            market="CN",
            instrument_type="ETF",
            list_date=calendar[0].date(),
            is_active=True,
        )
        for symbol in config.symbols
    }
    return MarketDataBundle(
        calendar=calendar,
        instruments=instruments,
        bars=bars.set_index(["trade_date", "symbol"]),
    )
