# Real Data Validation CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repeatable real-data ETF validation CLI that can run the first trend-filter strategy on a fixed 5-year window, compare it against an equal-weight buy-and-hold baseline, and emit report artifacts.

**Architecture:** Keep the existing sample backtest path unchanged, add a simple strategy-name selector inside the backtest engine, and introduce a small real-data preparation layer that downloads and caches ETF daily bars into the existing canonical `MarketDataBundle` shape. The CLI layer orchestrates loading, running, comparing against a baseline, and writing artifacts without adding any real-trading capability.

**Tech Stack:** Python 3.12, pandas, numpy, yfinance, pytest, argparse, JSON/CSV files

## Global Constraints

- Continue working on branch `codex/subproject-1-main`
- Do not create or use a new worktree; user explicitly chose branch-based isolation
- Keep `run-sample-backtest` behavior intact
- Real-data validation must use explicit dates, never `today`, `now()`, or omitted `end`
- Default real-data validation window must be `2021-07-28` through `2026-07-27`
- Strategy selection must support exactly `rotation` and `trend_filter` in this slice
- Real-data validation must write cache files locally and fail loudly on empty or invalid downloads
- Follow TDD: write failing tests first, verify RED, then add minimal production code

## File Structure

- Modify: `src/ai_xquanty/config.py` — extend backtest configuration to carry strategy choice and real-data parameters
- Modify: `src/ai_xquanty/backtest/engine.py` — route strategy selection, keep sample path stable
- Modify: `src/ai_xquanty/cli.py` — add `run-real-backtest`
- Modify: `src/ai_xquanty/reporting/render.py` — write baseline comparison artifact when present
- Modify: `src/ai_xquanty/reporting/metrics.py` — add richer summary fields used by the real-data report
- Modify: `tests/backtest/test_engine.py` — cover strategy selection without regressing the sample path
- Modify: `tests/test_cli_smoke.py` — cover the new CLI command and preserve the old one
- Create: `src/ai_xquanty/strategy/registry.py` — strategy-name to signal-function mapping
- Create: `src/ai_xquanty/data/real_etf.py` — download, validate, cache, and normalize real ETF bars
- Create: `src/ai_xquanty/reporting/baseline.py` — compute equal-weight buy-and-hold baseline and comparison summary
- Create: `tests/data/test_real_etf.py` — unit tests for real-data preparation and validation
- Create: `tests/reporting/test_baseline.py` — tests for baseline comparison outputs

---

### Task 1: Route strategy selection through the engine

**Files:**
- Create: `src/ai_xquanty/strategy/registry.py`
- Modify: `src/ai_xquanty/config.py`
- Modify: `src/ai_xquanty/backtest/engine.py`
- Modify: `tests/backtest/test_engine.py`

**Interfaces:**
- Consumes: `compute_etf_signals(bundle, as_of, lookback_days, top_n)` and `compute_trend_filter_signals(bundle, as_of, lookback_days, short_window, long_window, top_n)`
- Produces:
  - `resolve_signal_fn(strategy_name: str) -> Callable[[MarketDataBundle, pd.Timestamp], list[SignalSnapshot]]`
  - `BacktestConfig.strategy_name: str = "rotation"`
  - `run_backtest(config: BacktestConfig) -> BacktestResult` honoring `config.strategy_name`

- [ ] **Step 1: Write the failing engine test for `trend_filter` selection**

```python
def test_run_backtest_uses_trend_filter_strategy_when_selected(
    repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    used_names: list[str] = []

    def fake_resolve_signal_fn(strategy_name: str):
        used_names.append(strategy_name)

        def _fake_signal_fn(bundle, as_of):
            return []

        return _fake_signal_fn

    monkeypatch.setattr("ai_xquanty.backtest.engine.resolve_signal_fn", fake_resolve_signal_fn)

    config = BacktestConfig.from_sample_data(repo_root, strategy_name="trend_filter")
    result = run_backtest(config)

    assert used_names == ["trend_filter"]
    assert result.equity_curve["nav"].tolist()[0] == 1_000_000.0
```

- [ ] **Step 2: Run the single RED test**

Run: `.venv/bin/pytest tests/backtest/test_engine.py::test_run_backtest_uses_trend_filter_strategy_when_selected -q`
Expected: FAIL because `BacktestConfig.from_sample_data` does not yet accept `strategy_name`, or `resolve_signal_fn` does not yet exist

- [ ] **Step 3: Implement the minimal strategy registry**

```python
def resolve_signal_fn(strategy_name: str):
    if strategy_name == "rotation":
        return lambda bundle, as_of: compute_etf_signals(bundle, as_of, lookback_days=3, top_n=2)
    if strategy_name == "trend_filter":
        return lambda bundle, as_of: compute_trend_filter_signals(
            bundle,
            as_of,
            lookback_days=3,
            short_window=2,
            long_window=4,
            top_n=2,
        )
    raise ValueError(f"Unsupported strategy: {strategy_name}")
```

- [ ] **Step 4: Extend `BacktestConfig` minimally**

```python
@dataclass(frozen=True)
class BacktestConfig:
    calendar_path: Path
    instruments_path: Path
    bars_path: Path
    initial_cash: float = 1_000_000.0
    strategy_name: str = "rotation"

    @classmethod
    def from_sample_data(cls, repo_root: Path, strategy_name: str = "rotation") -> "BacktestConfig":
        sample_dir = repo_root / "data" / "sample"
        return cls(
            calendar_path=sample_dir / "calendar.csv",
            instruments_path=sample_dir / "instruments.csv",
            bars_path=sample_dir / "bars.csv",
            strategy_name=strategy_name,
        )
```

- [ ] **Step 5: Update the engine to use the selector**

```python
signal_fn = resolve_signal_fn(config.strategy_name)
bundle = load_market_data(config)
rebalance_dates = set(select_weekly_rebalance_dates(bundle.calendar))
signals = signal_fn(bundle, trade_date)
```

- [ ] **Step 6: Run the new engine test to verify GREEN**

Run: `.venv/bin/pytest tests/backtest/test_engine.py::test_run_backtest_uses_trend_filter_strategy_when_selected -q`
Expected: PASS

- [ ] **Step 7: Run the full engine test file**

Run: `.venv/bin/pytest tests/backtest/test_engine.py -q`
Expected: PASS

### Task 2: Add real ETF data preparation with cache and validation

**Files:**
- Create: `src/ai_xquanty/data/real_etf.py`
- Modify: `src/ai_xquanty/config.py`
- Create: `tests/data/test_real_etf.py`

**Interfaces:**
- Consumes: `yfinance.download`, explicit `start`, explicit `end`, symbol list, local cache directory
- Produces:
  - `RealBacktestConfig` with `start`, `end`, `symbols`, `cache_dir`, `initial_cash`, `strategy_name`
  - `prepare_real_market_data(config: RealBacktestConfig, refresh: bool = False) -> MarketDataBundle`

- [ ] **Step 1: Write the failing test for cached bundle creation**

```python
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
    assert bundle.calendar.tolist() == [pd.Timestamp("2021-07-28"), pd.Timestamp("2021-07-29")]
    assert float(bundle.bars.loc[(pd.Timestamp("2021-07-28"), "510300.SS"), "close"]) == 3.51
    assert (tmp_path / "510300.SS.csv").exists()
```

- [ ] **Step 2: Write the failing test for empty download rejection**

```python
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
```

- [ ] **Step 3: Write the failing test for cache reuse**

```python
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
```

- [ ] **Step 4: Run the RED test file**

Run: `.venv/bin/pytest tests/data/test_real_etf.py -q`
Expected: FAIL because `RealBacktestConfig` or `prepare_real_market_data` does not exist

- [ ] **Step 5: Implement `RealBacktestConfig` and the data-prep module minimally**

```python
@dataclass(frozen=True)
class RealBacktestConfig:
    start: str
    end: str
    symbols: list[str]
    cache_dir: Path
    initial_cash: float = 1_000_000.0
    strategy_name: str = "trend_filter"
```

```python
def prepare_real_market_data(config: RealBacktestConfig, refresh: bool = False) -> MarketDataBundle:
    frames = []
    for symbol in config.symbols:
        frame = _load_or_download_symbol(symbol, config.start, config.end, config.cache_dir, refresh)
        frames.append(frame)
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
```

- [ ] **Step 6: Run the data-prep tests to verify GREEN**

Run: `.venv/bin/pytest tests/data/test_real_etf.py -q`
Expected: PASS

### Task 3: Add baseline comparison and richer artifact output

**Files:**
- Create: `src/ai_xquanty/reporting/baseline.py`
- Modify: `src/ai_xquanty/backtest/engine.py`
- Modify: `src/ai_xquanty/reporting/metrics.py`
- Modify: `src/ai_xquanty/reporting/render.py`
- Create: `tests/reporting/test_baseline.py`

**Interfaces:**
- Consumes: `MarketDataBundle`, `BacktestResult.equity_curve`, `BacktestResult.fills`, `initial_cash`
- Produces:
  - `compute_equal_weight_buy_and_hold(bundle: MarketDataBundle, initial_cash: float) -> pd.DataFrame`
  - `compute_baseline_comparison(result: BacktestResult, bundle: MarketDataBundle, initial_cash: float) -> dict[str, float]`
  - `BacktestResult.baseline_comparison: dict[str, float] | None`

- [ ] **Step 1: Write the failing baseline comparison test**

```python
def test_compute_baseline_comparison_reports_strategy_and_baseline_returns(sample_bundle) -> None:
    equity_curve = pd.DataFrame(
        [
            {"trade_date": "2024-01-02", "cash": 1_000_000.0, "holdings_value": 0.0, "nav": 1_000_000.0},
            {"trade_date": "2024-01-08", "cash": 550_000.0, "holdings_value": 460_000.0, "nav": 1_010_000.0},
        ]
    )
    result = BacktestResult(
        equity_curve=equity_curve,
        fills=pd.DataFrame([{"status": "filled"}]),
        summary={"final_nav": 1_010_000.0, "max_drawdown": 0.0, "num_observations": 2.0},
        baseline_comparison=None,
    )

    comparison = compute_baseline_comparison(result, sample_bundle, initial_cash=1_000_000.0)

    assert set(comparison) == {
        "strategy_total_return",
        "baseline_total_return",
        "excess_return",
        "strategy_max_drawdown",
        "baseline_max_drawdown",
        "num_filled_orders",
    }
```

- [ ] **Step 2: Write the failing artifact writer test**

```python
def test_write_backtest_artifacts_writes_baseline_comparison_json(tmp_path: Path) -> None:
    result = BacktestResult(
        equity_curve=pd.DataFrame([{"trade_date": "2024-01-02", "cash": 1.0, "holdings_value": 0.0, "nav": 1.0}]),
        fills=pd.DataFrame(columns=["trade_date", "symbol", "side", "status", "quantity", "price", "fees"]),
        summary={"final_nav": 1.0, "max_drawdown": 0.0, "num_observations": 1.0},
        baseline_comparison={"strategy_total_return": 0.01},
    )

    write_backtest_artifacts(result, tmp_path)

    assert (tmp_path / "baseline_comparison.json").exists()
```

- [ ] **Step 3: Run the RED reporting tests**

Run: `.venv/bin/pytest tests/reporting/test_baseline.py -q`
Expected: FAIL because baseline helpers or `baseline_comparison` support is missing

- [ ] **Step 4: Implement the minimal baseline helpers and artifact writer support**

```python
@dataclass(frozen=True)
class BacktestResult:
    equity_curve: pd.DataFrame
    fills: pd.DataFrame
    summary: dict[str, float]
    baseline_comparison: dict[str, float] | None = None
```

```python
def compute_baseline_comparison(result, bundle, initial_cash):
    baseline_curve = compute_equal_weight_buy_and_hold(bundle, initial_cash)
    strategy_total_return = result.equity_curve["nav"].iloc[-1] / initial_cash - 1.0
    baseline_total_return = baseline_curve["nav"].iloc[-1] / initial_cash - 1.0
    return {
        "strategy_total_return": float(strategy_total_return),
        "baseline_total_return": float(baseline_total_return),
        "excess_return": float(strategy_total_return - baseline_total_return),
        "strategy_max_drawdown": float(compute_summary_metrics(result.equity_curve)["max_drawdown"]),
        "baseline_max_drawdown": float(compute_summary_metrics(baseline_curve)["max_drawdown"]),
        "num_filled_orders": float((result.fills["status"] == "filled").sum()),
    }
```

- [ ] **Step 5: Run the reporting tests to verify GREEN**

Run: `.venv/bin/pytest tests/reporting/test_baseline.py -q`
Expected: PASS

### Task 4: Add the real-data CLI entrypoint

**Files:**
- Modify: `src/ai_xquanty/cli.py`
- Modify: `tests/test_cli_smoke.py`
- Modify: `src/ai_xquanty/backtest/engine.py`
- Create: `src/ai_xquanty/data/real_etf.py` (reuse from Task 2)
- Create: `src/ai_xquanty/reporting/baseline.py` (reuse from Task 3)

**Interfaces:**
- Consumes:
  - `prepare_real_market_data(config: RealBacktestConfig, refresh: bool = False) -> MarketDataBundle`
  - `run_backtest_on_bundle(config: BacktestConfig | RealBacktestConfig, bundle: MarketDataBundle) -> BacktestResult`
  - `compute_baseline_comparison(result: BacktestResult, bundle: MarketDataBundle, initial_cash: float) -> dict[str, float]`
- Produces:
  - CLI subcommand `run-real-backtest`
  - output files in `--output-dir`

- [ ] **Step 1: Write the failing CLI smoke test**

```python
def test_cli_run_real_backtest_writes_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = load_market_data(BacktestConfig.from_sample_data(Path(__file__).resolve().parents[1]))

    monkeypatch.setattr("ai_xquanty.cli.prepare_real_market_data", lambda config, refresh=False: bundle)
    monkeypatch.setattr(
        "ai_xquanty.cli.run_backtest_on_bundle",
        lambda config, bundle: BacktestResult(
            equity_curve=pd.DataFrame([{"trade_date": "2024-01-02", "cash": 1.0, "holdings_value": 0.0, "nav": 1.0}]),
            fills=pd.DataFrame(columns=["trade_date", "symbol", "side", "status", "quantity", "price", "fees"]),
            summary={"final_nav": 1.0, "max_drawdown": 0.0, "num_observations": 1.0},
            baseline_comparison=None,
        ),
    )
    monkeypatch.setattr(
        "ai_xquanty.cli.compute_baseline_comparison",
        lambda result, bundle, initial_cash: {"strategy_total_return": 0.0},
    )

    exit_code = main(
        [
            "run-real-backtest",
            "--strategy",
            "trend_filter",
            "--start",
            "2021-07-28",
            "--end",
            "2026-07-27",
            "--symbols",
            "510300.SS,510500.SS,159915.SZ,159949.SZ",
            "--cache-dir",
            str(tmp_path / "cache"),
            "--output-dir",
            str(tmp_path / "report"),
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "report" / "summary.json").exists()
    assert (tmp_path / "report" / "baseline_comparison.json").exists()
```

- [ ] **Step 2: Run the RED CLI test**

Run: `.venv/bin/pytest tests/test_cli_smoke.py::test_cli_run_real_backtest_writes_outputs -q`
Expected: FAIL because `run-real-backtest` is unsupported

- [ ] **Step 3: Implement the minimal CLI path**

```python
real_parser = subparsers.add_parser("run-real-backtest")
real_parser.add_argument("--strategy", required=True, choices=["rotation", "trend_filter"])
real_parser.add_argument("--start", required=True)
real_parser.add_argument("--end", required=True)
real_parser.add_argument("--symbols", required=True)
real_parser.add_argument("--cache-dir", required=True)
real_parser.add_argument("--output-dir", required=True)
real_parser.add_argument("--refresh-cache", action="store_true")
```

```python
if args.command == "run-real-backtest":
    config = RealBacktestConfig(
        start=args.start,
        end=args.end,
        symbols=tuple(symbol.strip() for symbol in args.symbols.split(",") if symbol.strip()),
        cache_dir=Path(args.cache_dir),
        strategy_name=args.strategy,
    )
    bundle = prepare_real_market_data(config, refresh=args.refresh_cache)
    result = run_backtest_on_bundle(config, bundle)
    comparison = compute_baseline_comparison(result, bundle, config.initial_cash)
    result = BacktestResult(
        equity_curve=result.equity_curve,
        fills=result.fills,
        summary=result.summary,
        baseline_comparison=comparison,
    )
    write_backtest_artifacts(result, Path(args.output_dir))
    return 0
```

- [ ] **Step 4: Run the CLI smoke tests to verify GREEN**

Run: `.venv/bin/pytest tests/test_cli_smoke.py -q`
Expected: PASS

### Task 5: Full targeted verification and first live command

**Files:**
- Modify: none

**Interfaces:**
- Consumes: All code and tests above
- Produces: Verified implementation status and a ready-to-run real-data CLI command

- [ ] **Step 1: Run the full targeted verification set**

Run: `.venv/bin/pytest tests/backtest/test_engine.py tests/data/test_real_etf.py tests/reporting/test_baseline.py tests/strategy/test_etf_rotation.py tests/strategy/test_etf_trend_filter.py tests/test_cli_smoke.py -q`
Expected: PASS

- [ ] **Step 2: Run the sample CLI smoke command as a regression check**

Run: `.venv/bin/python -m ai_xquanty.cli run-sample-backtest --output-dir /tmp/ai_xquanty-sample-check`
Expected: exit 0 and artifact files created in `/tmp/ai_xquanty-sample-check`

- [ ] **Step 3: Run the first live real-data validation command**

Run: `.venv/bin/python -m ai_xquanty.cli run-real-backtest --strategy trend_filter --start 2021-07-28 --end 2026-07-27 --symbols 510300.SS,510500.SS,159915.SZ,159949.SZ --cache-dir /tmp/ai_xquanty-real-cache --output-dir /tmp/ai_xquanty-real-report --refresh-cache`
Expected: exit 0; writes `summary.json`, `equity_curve.csv`, `fills.csv`, and `baseline_comparison.json`

- [ ] **Step 4: Check git status for the exact changed files**

Run: `git status --short`
Expected: shows the config, engine, CLI, reporting, new data/reporting modules, new tests, and any already-existing notebook/spec work

- [ ] **Step 5: Report the outcome and remaining gap**

The handoff must cover:
- strategy selection is now configurable
- real-data cache path and report path
- whether the first live validation run succeeded
- what still remains before gray release or small-capital validation
