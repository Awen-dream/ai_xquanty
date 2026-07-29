from datetime import date
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class BacktestConfig:
    calendar_path: Path
    instruments_path: Path
    bars_path: Path
    initial_cash: float = 1_000_000.0
    strategy_name: str = "rotation"

    @classmethod
    def from_sample_data(
        cls, repo_root: Path, strategy_name: str = "rotation"
    ) -> "BacktestConfig":
        sample_dir = repo_root / "data" / "sample"
        return cls(
            calendar_path=sample_dir / "calendar.csv",
            instruments_path=sample_dir / "instruments.csv",
            bars_path=sample_dir / "bars.csv",
            strategy_name=strategy_name,
        )


@dataclass(frozen=True)
class RealBacktestConfig:
    start: str
    end: str
    symbols: tuple[str, ...]
    cache_dir: Path
    initial_cash: float = 1_000_000.0
    strategy_name: str = "trend_filter"

    def __post_init__(self) -> None:
        start_date = _parse_explicit_date(self.start, field_name="start")
        end_date = _parse_explicit_date(self.end, field_name="end")
        if start_date > end_date:
            raise ValueError("start must be on or before end")


_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_explicit_date(value: object, field_name: str) -> date:
    if not isinstance(value, str) or not _DATE_PATTERN.match(value):
        raise ValueError(f"{field_name} must use explicit YYYY-MM-DD date")

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must use explicit YYYY-MM-DD date") from exc
