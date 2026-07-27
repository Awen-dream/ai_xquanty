from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BacktestConfig:
    calendar_path: Path
    instruments_path: Path
    bars_path: Path
    initial_cash: float = 1_000_000.0

    @classmethod
    def from_sample_data(cls, repo_root: Path) -> "BacktestConfig":
        sample_dir = repo_root / "data" / "sample"
        return cls(
            calendar_path=sample_dir / "calendar.csv",
            instruments_path=sample_dir / "instruments.csv",
            bars_path=sample_dir / "bars.csv",
        )
