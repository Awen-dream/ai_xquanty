from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass(frozen=True)
class Instrument:
    symbol: str
    market: str
    instrument_type: str
    list_date: date
    is_active: bool

    def __post_init__(self) -> None:
        if self.instrument_type != "ETF":
            raise ValueError("Subproject 1 is ETF-only in the sample bundle")


@dataclass(frozen=True)
class MarketDataBundle:
    calendar: pd.DatetimeIndex
    instruments: dict[str, Instrument]
    bars: pd.DataFrame


@dataclass(frozen=True)
class SignalSnapshot:
    trade_date: date
    strategy_name: str
    symbol: str
    score: float


@dataclass(frozen=True)
class TargetPortfolio:
    strategy_name: str
    weights: dict[str, float]


@dataclass(frozen=True)
class OrderIntent:
    trade_date: date
    symbol: str
    side: str
    quantity: int


@dataclass(frozen=True)
class FillRecord:
    symbol: str
    status: str
    quantity: int
    price: float
    fees: float


@dataclass(frozen=True)
class PositionSnapshot:
    symbol: str
    quantity: int
    average_cost: float
