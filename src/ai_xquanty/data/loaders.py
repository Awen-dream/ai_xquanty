from pathlib import Path

import pandas as pd

from ai_xquanty.config import BacktestConfig
from ai_xquanty.domain.models import Instrument, MarketDataBundle


def _read_table(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def load_market_data(config: BacktestConfig) -> MarketDataBundle:
    calendar = pd.DatetimeIndex(pd.read_csv(config.calendar_path)["trade_date"])
    instruments_df = _read_table(config.instruments_path)
    bars = _read_table(config.bars_path)
    bars["trade_date"] = pd.to_datetime(bars["trade_date"])
    bars = bars.sort_values(["trade_date", "symbol"]).set_index(["trade_date", "symbol"])
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
    return MarketDataBundle(calendar=calendar, instruments=instruments, bars=bars)
