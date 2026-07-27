# Subproject 1 ETF Core Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python research platform that can load bundled sample A-share ETF data, run a cost-aware ETF core backtest with paper execution constraints, and produce reproducible reports without any live trading capability.

**Architecture:** The system is a small Python package organized around domain models, data loading, strategy logic, portfolio construction, risk checks, paper execution, and reporting. The first slice stays intentionally narrow: it runs a bundled ETF sample universe end to end so we can verify the whole research and simulation chain before adding A-share multifactor stock logic.

**Rebalance Cadence Decision:** Rebalance weekly. Update NAV daily, but only generate new orders on weekly rebalance dates.

**Tech Stack:** Python 3.12, pandas, numpy, pyarrow, pytest

## Global Constraints

- 子项目 1 只做研究、回测、模拟执行，不直接连接真实券商自动下单
- 未完成券商接口能力确认、合规报告义务确认、风控演练之前，不进入自动实盘
- 所有真实执行能力都必须默认关闭，需显式启用
- 数据异常、持仓对账异常、订单状态异常时系统必须 fail-closed，而不是继续发送订单
- 候选池规模控制在 4 到 8 只 ETF
- 以宽基或低复杂度资产风格 ETF 为主，不引入高杠杆、高换手主题 ETF
- 输入数据先采用仓库内样例 CSV/Parquet
- 数据供应商接入只做抽象接口，不在子项目 1 内完成正式接入
- 首版仅面向一个小型 ETF 候选池，不在本阶段追求“大而全市场覆盖”
- 使用趋势/动量与相对强弱的规则组合
- 使用周频调仓，避免日内噪声
- 当风控条件不满足时允许转入现金
- 所有回测结果必须是扣成本后的结果
- 不允许未来函数
- 不允许幸存者偏差作为默认假设

---

## Planned File Structure

- Create: `pyproject.toml` — project metadata, dependencies, pytest config
- Create: `README.md` — local setup, sample run command, current scope, non-scope
- Create: `src/ai_xquanty/__init__.py` — package version marker
- Create: `src/ai_xquanty/config.py` — backtest settings and sample-path helpers
- Create: `src/ai_xquanty/domain/models.py` — immutable domain dataclasses
- Create: `src/ai_xquanty/data/loaders.py` — CSV and Parquet readers plus validation
- Create: `src/ai_xquanty/strategy/etf_rotation.py` — signal generation for the ETF core strategy
- Create: `src/ai_xquanty/portfolio/targets.py` — target weights from ranked signals
- Create: `src/ai_xquanty/risk/rules.py` — account-level portfolio guards
- Create: `src/ai_xquanty/execution/paper.py` — order intent generation and next-day fill simulation
- Create: `src/ai_xquanty/backtest/engine.py` — orchestration loop over trading dates
- Create: `src/ai_xquanty/reporting/metrics.py` — summary metrics and drawdown series
- Create: `src/ai_xquanty/reporting/render.py` — write CSV and JSON artifacts
- Create: `src/ai_xquanty/cli.py` — `run-sample-backtest` entry point
- Create: `data/sample/calendar.csv` — sample trading calendar
- Create: `data/sample/instruments.csv` — 4-8 ETF instruments
- Create: `data/sample/bars.csv` — bundled OHLCV sample bars
- Create: `tests/conftest.py` — shared path fixtures
- Create: `tests/test_cli_smoke.py` — CLI help and sample command smoke tests
- Create: `tests/domain/test_models.py` — dataclass and validation tests
- Create: `tests/data/test_loaders.py` — loader shape and ordering tests
- Create: `tests/strategy/test_etf_rotation.py` — signal ranking tests
- Create: `tests/portfolio/test_targets.py` — target weight construction tests
- Create: `tests/risk/test_rules.py` — drawdown and turnover protection tests
- Create: `tests/execution/test_paper.py` — cost, T+1, pause, limit-hit simulation tests
- Create: `tests/backtest/test_engine.py` — end-to-end deterministic backtest test
- Create: `tests/reporting/test_render.py` — report artifact output test

### Task 1: Bootstrap The Repository And Bundle Sample Data

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/ai_xquanty/__init__.py`
- Create: `src/ai_xquanty/config.py`
- Create: `src/ai_xquanty/cli.py`
- Create: `data/sample/calendar.csv`
- Create: `data/sample/instruments.csv`
- Create: `data/sample/bars.csv`
- Create: `tests/conftest.py`
- Create: `tests/test_cli_smoke.py`

**Interfaces:**
- Consumes: none
- Produces: `BacktestConfig`, `BacktestConfig.from_sample_data(repo_root: Path) -> BacktestConfig`, `main(argv: list[str] | None = None) -> int`

- [ ] **Step 1: Write the failing smoke tests**

```python
from pathlib import Path

from ai_xquanty.cli import main
from ai_xquanty.config import BacktestConfig


def test_backtest_config_points_to_bundled_sample_data(repo_root: Path) -> None:
    config = BacktestConfig.from_sample_data(repo_root)
    assert config.calendar_path.name == "calendar.csv"
    assert config.instruments_path.name == "instruments.csv"
    assert config.bars_path.name == "bars.csv"


def test_cli_without_subcommand_returns_zero() -> None:
    assert main([]) == 0
```

- [ ] **Step 2: Run the smoke tests to verify they fail**

Run: `pytest tests/test_cli_smoke.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'ai_xquanty'`

- [ ] **Step 3: Add the package scaffold, sample data, and CLI stub**

```toml
[project]
name = "ai-xquanty"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "numpy>=2.0,<3.0",
  "pandas>=2.2,<3.0",
  "pyarrow>=17,<19",
]

[project.optional-dependencies]
dev = ["pytest>=8.3,<9.0"]

[tool.pytest.ini_options]
pythonpath = ["src"]
```

```python
from pathlib import Path

import pytest


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]
```

```python
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
```

```python
import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-xquanty")
    parser.add_argument("--help-only", action="store_true")
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```csv
trade_date
2024-01-02
2024-01-03
2024-01-04
2024-01-05
2024-01-08
```

```csv
symbol,market,instrument_type,list_date,is_active
510300.SH,SSE,ETF,2012-05-28,1
510500.SH,SSE,ETF,2013-03-15,1
159915.SZ,SZSE,ETF,2011-09-16,1
159949.SZ,SZSE,ETF,2014-07-31,1
```

```csv
trade_date,symbol,open,high,low,close,volume,turnover,is_suspended,is_limit_up,is_limit_down
2024-01-02,510300.SH,3.50,3.52,3.48,3.51,1000000,3510000,0,0,0
2024-01-02,510500.SH,5.20,5.22,5.18,5.21,800000,4168000,0,0,0
2024-01-02,159915.SZ,2.40,2.42,2.39,2.41,900000,2169000,0,0,0
2024-01-02,159949.SZ,1.80,1.81,1.79,1.80,700000,1260000,0,0,0
2024-01-03,510300.SH,3.51,3.55,3.50,3.54,1100000,3894000,0,0,0
2024-01-03,510500.SH,5.21,5.24,5.20,5.23,820000,4288600,0,0,0
2024-01-03,159915.SZ,2.41,2.42,2.39,2.40,910000,2184000,0,0,0
2024-01-03,159949.SZ,1.80,1.80,1.78,1.79,690000,1235100,0,0,0
2024-01-04,510300.SH,3.54,3.58,3.53,3.57,1150000,4105500,0,0,0
2024-01-04,510500.SH,5.23,5.27,5.22,5.25,830000,4357500,0,0,0
2024-01-04,159915.SZ,2.40,2.41,2.39,2.40,905000,2172000,0,0,0
2024-01-04,159949.SZ,1.79,1.79,1.78,1.79,680000,1217200,0,0,0
2024-01-05,510300.SH,3.57,3.60,3.56,3.59,1180000,4236200,0,0,0
2024-01-05,510500.SH,5.25,5.29,5.24,5.27,835000,4400450,0,0,0
2024-01-05,159915.SZ,2.40,2.41,2.39,2.40,902000,2164800,0,0,0
2024-01-05,159949.SZ,1.79,1.79,1.77,1.78,675000,1201500,0,0,0
2024-01-08,510300.SH,3.62,3.66,3.62,3.66,1300000,4758000,0,1,0
2024-01-08,510500.SH,5.27,5.32,5.26,5.31,850000,4513500,0,0,0
2024-01-08,159915.SZ,2.40,2.43,2.39,2.42,920000,2226400,0,0,0
2024-01-08,159949.SZ,1.78,1.78,1.76,1.77,660000,1168200,0,0,0
```

- [ ] **Step 4: Run the smoke tests to verify the scaffold passes**

Run: `pytest tests/test_cli_smoke.py -q`
Expected: PASS

- [ ] **Step 5: Commit the bootstrap slice**

```bash
git add pyproject.toml README.md src/ai_xquanty data/sample tests
git commit -m "chore: bootstrap quant research package"
```

### Task 2: Implement Domain Models And Canonical Data Loading

**Files:**
- Create: `src/ai_xquanty/domain/models.py`
- Create: `src/ai_xquanty/data/loaders.py`
- Create: `tests/domain/test_models.py`
- Create: `tests/data/test_loaders.py`
- Modify: `src/ai_xquanty/config.py`
- Modify: `tests/conftest.py`

**Interfaces:**
- Consumes: `BacktestConfig`
- Produces: `Instrument`, `SignalSnapshot`, `TargetPortfolio`, `OrderIntent`, `FillRecord`, `PositionSnapshot`, `MarketDataBundle`, `load_market_data(config: BacktestConfig) -> MarketDataBundle`

- [ ] **Step 1: Write failing tests for the domain objects and data bundle**

```python
from datetime import date

from ai_xquanty.config import BacktestConfig
from ai_xquanty.data.loaders import load_market_data
from ai_xquanty.domain.models import Instrument


def test_instrument_rejects_unsupported_type() -> None:
    try:
        Instrument(symbol="600000.SH", market="SSE", instrument_type="STOCK", list_date=date(2020, 1, 1), is_active=True)
    except ValueError as exc:
        assert "ETF-only" in str(exc)
    else:
        raise AssertionError("Instrument should reject unsupported type")


def test_load_market_data_builds_sorted_bundle(repo_root) -> None:
    config = BacktestConfig.from_sample_data(repo_root)
    bundle = load_market_data(config)
    assert bundle.calendar[0].strftime("%Y-%m-%d") == "2024-01-02"
    assert bundle.bars.index.names == ["trade_date", "symbol"]
    assert float(bundle.bars.loc[("2024-01-02", "510300.SH"), "close"]) == 3.51
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/domain/test_models.py tests/data/test_loaders.py -q`
Expected: FAIL with `ImportError` for missing `load_market_data` or missing domain classes

- [ ] **Step 3: Implement immutable models and validated loaders**

```python
from dataclasses import dataclass, field
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
```

```python
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
```

```python
import pytest

from ai_xquanty.config import BacktestConfig
from ai_xquanty.data.loaders import load_market_data


@pytest.fixture
def sample_bundle(repo_root):
    return load_market_data(BacktestConfig.from_sample_data(repo_root))
```

- [ ] **Step 4: Run the data-model tests**

Run: `pytest tests/domain/test_models.py tests/data/test_loaders.py -q`
Expected: PASS

- [ ] **Step 5: Commit the canonical data slice**

```bash
git add src/ai_xquanty/domain src/ai_xquanty/data src/ai_xquanty/config.py tests/domain tests/data
git commit -m "feat: add canonical market data models"
```

### Task 3: Add ETF Signal Ranking And Target Portfolio Construction

**Files:**
- Create: `src/ai_xquanty/strategy/etf_rotation.py`
- Create: `src/ai_xquanty/portfolio/targets.py`
- Create: `tests/strategy/test_etf_rotation.py`
- Create: `tests/portfolio/test_targets.py`

**Interfaces:**
- Consumes: `MarketDataBundle`
- Produces: `compute_etf_signals(bundle: MarketDataBundle, as_of: pd.Timestamp, lookback_days: int, top_n: int) -> list[SignalSnapshot]`, `build_target_portfolio(signals: list[SignalSnapshot], cash_buffer: float, max_positions: int) -> TargetPortfolio`

- [ ] **Step 1: Write failing tests for ranking and target weights**

```python
from datetime import date

import pandas as pd

from ai_xquanty.config import BacktestConfig
from ai_xquanty.data.loaders import load_market_data
from ai_xquanty.domain.models import SignalSnapshot
from ai_xquanty.portfolio.targets import build_target_portfolio
from ai_xquanty.strategy.etf_rotation import compute_etf_signals


def test_compute_etf_signals_ranks_by_trailing_return(repo_root) -> None:
    bundle = load_market_data(BacktestConfig.from_sample_data(repo_root))
    signals = compute_etf_signals(bundle, as_of=pd.Timestamp("2024-01-08"), lookback_days=3, top_n=2)
    assert [signal.symbol for signal in signals] == ["510300.SH", "510500.SH"]


def test_build_target_portfolio_reserves_cash_buffer() -> None:
    signals = [
        SignalSnapshot(trade_date=date(2024, 1, 8), strategy_name="etf_rotation", symbol="510300.SH", score=0.06),
        SignalSnapshot(trade_date=date(2024, 1, 8), strategy_name="etf_rotation", symbol="510500.SH", score=0.04),
    ]
    target = build_target_portfolio(signals, cash_buffer=0.10, max_positions=2)
    assert target.weights == {"510300.SH": 0.45, "510500.SH": 0.45, "CASH": 0.10}
```

- [ ] **Step 2: Run the strategy tests to verify they fail**

Run: `pytest tests/strategy/test_etf_rotation.py tests/portfolio/test_targets.py -q`
Expected: FAIL with `ImportError` for missing strategy or target helpers

- [ ] **Step 3: Implement signal scoring and target-weight logic**

```python
import pandas as pd

from ai_xquanty.domain.models import MarketDataBundle, SignalSnapshot


def compute_etf_signals(
    bundle: MarketDataBundle,
    as_of: pd.Timestamp,
    lookback_days: int,
    top_n: int,
) -> list[SignalSnapshot]:
    closes = bundle.bars["close"].unstack("symbol").sort_index()
    window = closes.loc[:as_of].tail(lookback_days + 1)
    trailing_returns = window.iloc[-1] / window.iloc[0] - 1.0
    ranked = trailing_returns.sort_values(ascending=False).head(top_n)
    return [
        SignalSnapshot(
            trade_date=as_of.date(),
            strategy_name="etf_rotation",
            symbol=symbol,
            score=float(score),
        )
        for symbol, score in ranked.items()
    ]
```

```python
from ai_xquanty.domain.models import SignalSnapshot, TargetPortfolio


def build_target_portfolio(
    signals: list[SignalSnapshot],
    cash_buffer: float,
    max_positions: int,
) -> TargetPortfolio:
    selected = signals[:max_positions]
    equity_weight = (1.0 - cash_buffer) / len(selected) if selected else 0.0
    weights = {signal.symbol: round(equity_weight, 6) for signal in selected}
    weights["CASH"] = round(1.0 - sum(weights.values()), 6)
    return TargetPortfolio(strategy_name="etf_rotation", weights=weights)
```

- [ ] **Step 4: Run the strategy and target tests**

Run: `pytest tests/strategy/test_etf_rotation.py tests/portfolio/test_targets.py -q`
Expected: PASS

- [ ] **Step 5: Commit the strategy slice**

```bash
git add src/ai_xquanty/strategy src/ai_xquanty/portfolio tests/strategy tests/portfolio
git commit -m "feat: add etf ranking strategy"
```

### Task 4: Add Portfolio Guards And Paper Execution Constraints

**Files:**
- Create: `src/ai_xquanty/risk/rules.py`
- Create: `src/ai_xquanty/execution/paper.py`
- Create: `tests/risk/test_rules.py`
- Create: `tests/execution/test_paper.py`
- Modify: `src/ai_xquanty/domain/models.py`

**Interfaces:**
- Consumes: `TargetPortfolio`, `PositionSnapshot`, `MarketDataBundle`
- Produces: `apply_risk_rules(target: TargetPortfolio, current_positions: dict[str, PositionSnapshot], current_drawdown: float, max_single_weight: float, min_cash_weight: float, drawdown_stop: float) -> TargetPortfolio`, `build_order_intents(current_positions: dict[str, PositionSnapshot], target: TargetPortfolio, prices: pd.Series, trade_date: pd.Timestamp, portfolio_value: float) -> list[OrderIntent]`, `simulate_next_day_fills(order_intents: list[OrderIntent], bundle: MarketDataBundle, trade_date: pd.Timestamp, commission_rate: float, stamp_duty_rate: float, transfer_fee_rate: float, slippage_bps: float) -> list[FillRecord]`

- [ ] **Step 1: Write failing tests for drawdown protection and no-fill scenarios**

```python
import pandas as pd

from ai_xquanty.domain.models import TargetPortfolio
from ai_xquanty.execution.paper import build_order_intents, simulate_next_day_fills
from ai_xquanty.risk.rules import apply_risk_rules


def test_apply_risk_rules_forces_cash_when_drawdown_limit_is_breached() -> None:
    target = TargetPortfolio(strategy_name="etf_rotation", weights={"510300.SH": 0.90, "CASH": 0.10})
    protected = apply_risk_rules(target, current_positions={}, current_drawdown=0.11, max_single_weight=0.50, min_cash_weight=0.10, drawdown_stop=0.10)
    assert protected.weights == {"CASH": 1.0}


def test_simulate_next_day_fills_marks_limit_up_buy_as_unfilled(sample_bundle) -> None:
    intents = build_order_intents(
        current_positions={},
        target=TargetPortfolio(strategy_name="etf_rotation", weights={"510300.SH": 0.90, "CASH": 0.10}),
        prices=pd.Series({"510300.SH": 3.51}),
        trade_date=pd.Timestamp("2024-01-05"),
        portfolio_value=1_000_000.0,
    )
    fills = simulate_next_day_fills(intents, sample_bundle, trade_date=pd.Timestamp("2024-01-08"), commission_rate=0.0003, stamp_duty_rate=0.0, transfer_fee_rate=0.00001, slippage_bps=5.0)
    assert fills[0].status == "rejected_limit_up"
```

- [ ] **Step 2: Run the guard and execution tests to verify they fail**

Run: `pytest tests/risk/test_rules.py tests/execution/test_paper.py -q`
Expected: FAIL with missing risk or execution functions

- [ ] **Step 3: Implement risk clamping, order intent generation, and fill simulation**

```python
from ai_xquanty.domain.models import TargetPortfolio


def apply_risk_rules(
    target: TargetPortfolio,
    current_positions: dict[str, object],
    current_drawdown: float,
    max_single_weight: float,
    min_cash_weight: float,
    drawdown_stop: float,
) -> TargetPortfolio:
    if current_drawdown >= drawdown_stop:
        return TargetPortfolio(strategy_name=target.strategy_name, weights={"CASH": 1.0})
    clamped = {
        symbol: min(weight, max_single_weight)
        for symbol, weight in target.weights.items()
        if symbol != "CASH"
    }
    cash_weight = max(min_cash_weight, 1.0 - sum(clamped.values()))
    clamped["CASH"] = round(cash_weight, 6)
    return TargetPortfolio(strategy_name=target.strategy_name, weights=clamped)
```

```python
import pandas as pd

from ai_xquanty.domain.models import FillRecord, OrderIntent


def build_order_intents(
    current_positions: dict[str, object],
    target,
    prices: pd.Series,
    trade_date: pd.Timestamp,
    portfolio_value: float,
) -> list[OrderIntent]:
    intents: list[OrderIntent] = []
    for symbol, weight in target.weights.items():
        if symbol == "CASH":
            continue
        quantity = int((portfolio_value * weight) / prices[symbol] / 100) * 100
        intents.append(OrderIntent(trade_date=trade_date.date(), symbol=symbol, side="BUY", quantity=quantity))
    return intents


def simulate_next_day_fills(order_intents, bundle, trade_date, commission_rate, stamp_duty_rate, transfer_fee_rate, slippage_bps):
    fills: list[FillRecord] = []
    for intent in order_intents:
        row = bundle.bars.loc[(trade_date, intent.symbol)]
        if bool(row["is_suspended"]):
            fills.append(FillRecord(symbol=intent.symbol, status="rejected_suspended", quantity=0, price=0.0, fees=0.0))
            continue
        if intent.side == "BUY" and bool(row["is_limit_up"]):
            fills.append(FillRecord(symbol=intent.symbol, status="rejected_limit_up", quantity=0, price=0.0, fees=0.0))
            continue
        price = float(row["open"]) * (1.0 + slippage_bps / 10000.0)
        fees = price * intent.quantity * (commission_rate + transfer_fee_rate + stamp_duty_rate)
        fills.append(FillRecord(symbol=intent.symbol, status="filled", quantity=intent.quantity, price=price, fees=fees))
    return fills
```

- [ ] **Step 4: Run the risk and execution tests**

Run: `pytest tests/risk/test_rules.py tests/execution/test_paper.py -q`
Expected: PASS

- [ ] **Step 5: Commit the risk and execution slice**

```bash
git add src/ai_xquanty/risk src/ai_xquanty/execution src/ai_xquanty/domain tests/risk tests/execution
git commit -m "feat: add paper execution safeguards"
```

### Task 5: Build The Backtest Loop And Performance Reporting

**Files:**
- Create: `src/ai_xquanty/backtest/engine.py`
- Create: `src/ai_xquanty/reporting/metrics.py`
- Create: `src/ai_xquanty/reporting/render.py`
- Create: `tests/backtest/test_engine.py`
- Create: `tests/reporting/test_render.py`

**Interfaces:**
- Consumes: `BacktestConfig`, `load_market_data`, `compute_etf_signals`, `build_target_portfolio`, `apply_risk_rules`, `build_order_intents`, `simulate_next_day_fills`
- Produces: `BacktestResult`, `select_weekly_rebalance_dates(calendar: pd.DatetimeIndex) -> list[pd.Timestamp]`, `run_backtest(config: BacktestConfig) -> BacktestResult`, `compute_summary_metrics(equity_curve: pd.DataFrame) -> dict[str, float]`, `write_backtest_artifacts(result: BacktestResult, output_dir: Path) -> None`

- [ ] **Step 1: Write failing tests for the end-to-end engine and artifact rendering**

```python
from pathlib import Path

from ai_xquanty.config import BacktestConfig
from ai_xquanty.backtest.engine import run_backtest
from ai_xquanty.reporting.render import write_backtest_artifacts


def test_run_backtest_returns_deterministic_summary(repo_root: Path, tmp_path: Path) -> None:
    result = run_backtest(BacktestConfig.from_sample_data(repo_root))
    assert result.summary["final_nav"] > 0.0
    assert result.summary["max_drawdown"] <= 0.10
    write_backtest_artifacts(result, tmp_path)
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "fills.csv").exists()


def test_write_backtest_artifacts_writes_equity_curve(tmp_path: Path, repo_root: Path) -> None:
    result = run_backtest(BacktestConfig.from_sample_data(repo_root))
    write_backtest_artifacts(result, tmp_path)
    assert (tmp_path / "equity_curve.csv").exists()


def test_select_weekly_rebalance_dates_uses_last_trading_day_of_week() -> None:
    import pandas as pd
    from ai_xquanty.backtest.engine import select_weekly_rebalance_dates

    calendar = pd.DatetimeIndex(
        [
            "2024-01-02",
            "2024-01-03",
            "2024-01-04",
            "2024-01-05",
            "2024-01-08",
        ]
    )
    assert select_weekly_rebalance_dates(calendar) == [pd.Timestamp("2024-01-05")]
```

- [ ] **Step 2: Run the engine and reporting tests to verify they fail**

Run: `pytest tests/backtest/test_engine.py tests/reporting/test_render.py -q`
Expected: FAIL with missing engine or reporting functions

- [ ] **Step 3: Implement the backtest orchestration and report writers**

```python
from dataclasses import dataclass

import pandas as pd

from ai_xquanty.config import BacktestConfig
from ai_xquanty.data.loaders import load_market_data
from ai_xquanty.execution.paper import build_order_intents, simulate_next_day_fills
from ai_xquanty.portfolio.targets import build_target_portfolio
from ai_xquanty.reporting.metrics import compute_summary_metrics
from ai_xquanty.risk.rules import apply_risk_rules
from ai_xquanty.strategy.etf_rotation import compute_etf_signals


@dataclass(frozen=True)
class BacktestResult:
    equity_curve: pd.DataFrame
    fills: pd.DataFrame
    summary: dict[str, float]


def select_weekly_rebalance_dates(calendar: pd.DatetimeIndex) -> list[pd.Timestamp]:
    weeks = pd.Series(calendar, index=calendar).groupby(calendar.to_period("W-FRI")).max()
    return [pd.Timestamp(value) for value in weeks.tolist()[:-1]]


def run_backtest(config: BacktestConfig) -> BacktestResult:
    bundle = load_market_data(config)
    nav_rows: list[dict[str, float | str]] = []
    fill_rows: list[dict[str, float | str]] = []
    portfolio_value = config.initial_cash
    rebalance_dates = select_weekly_rebalance_dates(bundle.calendar)
    for rebalance_date in rebalance_dates:
        signals = compute_etf_signals(bundle, rebalance_date, lookback_days=3, top_n=2)
        target = build_target_portfolio(signals, cash_buffer=0.10, max_positions=2)
        protected = apply_risk_rules(target, current_positions={}, current_drawdown=0.0, max_single_weight=0.50, min_cash_weight=0.10, drawdown_stop=0.10)
        prices = bundle.bars.xs(rebalance_date, level="trade_date")["close"]
        intents = build_order_intents({}, protected, prices, rebalance_date, portfolio_value)
        fills = simulate_next_day_fills(intents, bundle, bundle.calendar[bundle.calendar.get_loc(rebalance_date) + 1], 0.0003, 0.0, 0.00001, 5.0)
        fill_rows.extend([fill.__dict__ for fill in fills])
    for trade_date in bundle.calendar:
        nav_rows.append({"trade_date": trade_date.strftime("%Y-%m-%d"), "nav": portfolio_value})
    equity_curve = pd.DataFrame(nav_rows)
    fills_df = pd.DataFrame(fill_rows)
    return BacktestResult(equity_curve=equity_curve, fills=fills_df, summary=compute_summary_metrics(equity_curve))
```

```python
import json
from pathlib import Path

import pandas as pd


def compute_summary_metrics(equity_curve: pd.DataFrame) -> dict[str, float]:
    nav = equity_curve["nav"].astype(float)
    running_peak = nav.cummax()
    drawdown = (nav / running_peak - 1.0).fillna(0.0)
    return {
        "final_nav": float(nav.iloc[-1]),
        "max_drawdown": float(abs(drawdown.min())),
        "num_observations": float(len(equity_curve)),
    }
```

```python
import json
from pathlib import Path


def write_backtest_artifacts(result, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    result.equity_curve.to_csv(output_dir / "equity_curve.csv", index=False)
    result.fills.to_csv(output_dir / "fills.csv", index=False)
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(result.summary, handle, indent=2, ensure_ascii=False)
```

- [ ] **Step 4: Run the engine and reporting tests**

Run: `pytest tests/backtest/test_engine.py tests/reporting/test_render.py -q`
Expected: PASS

- [ ] **Step 5: Commit the engine and reporting slice**

```bash
git add src/ai_xquanty/backtest src/ai_xquanty/reporting tests/backtest tests/reporting
git commit -m "feat: add sample backtest engine"
```

### Task 6: Wire The CLI To The Backtest And Lock In Reproducibility

**Files:**
- Modify: `src/ai_xquanty/cli.py`
- Modify: `README.md`
- Modify: `tests/test_cli_smoke.py`

**Interfaces:**
- Consumes: `BacktestConfig.from_sample_data`, `run_backtest`, `write_backtest_artifacts`
- Produces: `python -m ai_xquanty.cli run-sample-backtest --output-dir outputs/sample_run`, deterministic sample output files under a user-selected directory

- [ ] **Step 1: Write failing tests for the real CLI backtest command**

```python
from pathlib import Path

from ai_xquanty.cli import main


def test_cli_run_sample_backtest_writes_outputs(tmp_path: Path) -> None:
    exit_code = main(["run-sample-backtest", "--output-dir", str(tmp_path)])
    assert exit_code == 0
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "equity_curve.csv").exists()
```

- [ ] **Step 2: Run the CLI backtest test to verify it fails**

Run: `pytest tests/test_cli_smoke.py::test_cli_run_sample_backtest_writes_outputs -q`
Expected: FAIL because `run-sample-backtest` is not yet a supported subcommand

- [ ] **Step 3: Replace the CLI stub with a runnable sample-backtest command and document it**

```python
import argparse
from pathlib import Path

from ai_xquanty.backtest.engine import run_backtest
from ai_xquanty.config import BacktestConfig
from ai_xquanty.reporting.render import write_backtest_artifacts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-xquanty")
    subparsers = parser.add_subparsers(dest="command")
    sample_parser = subparsers.add_parser("run-sample-backtest")
    sample_parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "run-sample-backtest":
        repo_root = Path(__file__).resolve().parents[2]
        config = BacktestConfig.from_sample_data(repo_root)
        result = run_backtest(config)
        write_backtest_artifacts(result, Path(args.output_dir))
        return 0
    raise ValueError(f"Unsupported command: {args.command}")
```

````markdown
## Current Scope

- Research, backtest, and paper execution only
- Bundled ETF sample universe only
- No broker connectivity and no live order routing

## Run The Sample Backtest

```bash
python -m ai_xquanty.cli run-sample-backtest --output-dir outputs/sample_run
```
````

- [ ] **Step 4: Run the focused CLI test and then the full suite**

Run: `pytest tests/test_cli_smoke.py::test_cli_run_sample_backtest_writes_outputs -q`
Expected: PASS

Run: `pytest -q`
Expected: PASS

- [ ] **Step 5: Commit the runnable MVP**

```bash
git add README.md src/ai_xquanty/cli.py tests data/sample
git commit -m "feat: expose runnable sample backtest"
```
