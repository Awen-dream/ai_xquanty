# Q1-Q9 量化交易生产候选 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 Q1-Q9 的课程研究产物收敛为一个可复现、可样本外验证、可模拟盘观察的三 ETF 量化交易候选，但在全部门槛通过前不接真实资金。

**Architecture:** 研究层固定数据快照和预注册验证协议；策略层直接生成 `TargetPortfolio`，以支持风险平价和波动率降仓，而不是把所有信号强制转换成等权仓位；回测层统一下一交易日开盘成交、A 股整手、交易成本和基准口径；报告层输出样本外指标、年度拆分、成本与执行偏差；模拟盘层只生成订单计划并做人工成交回填与对账。

**Tech Stack:** Python 3.12、pandas 2.x、NumPy 2.x、PyArrow 17.x、pytest 8.x、现有 `ai_xquanty` 包与本地 Parquet/manifest 数据。

## Global Constraints

- 第一阶段固定标的池：`510300.SS`、`513100.SS`、`518880.SS`。
- 比较对象固定为：等权买入持有基准、风险平价基线、动量加波动率降仓挑战者。
- 研究数据必须由 Parquet 文件和 SHA-256 manifest 共同锁定；报告必须写出数据起止日期和哈希。
- 所有信号只使用调仓时点及以前的数据，成交统一发生在下一交易日开盘并计入滑点与费用。
- 任何阈值不得用最终保留集的全样本中位数、最优点或未来数据生成。
- 参数只允许使用预注册的小范围：波动率窗口 `15/20/25`、动量窗口 `15/20/25`、调仓间隔 `10/15/21`；最终保留集只运行一次。
- 不新增止盈、移动止损、机器学习或更多 ETF，除非现有规则先通过样本外门槛。
- 不路由真实订单；模拟盘门槛通过后仍需用户单独批准小资金灰度。
- 保留当前工作区中 Q7、Q8、`pyproject.toml` 和 notebook 测试的未提交改动，不覆盖、不回退。

---

## 当前评估基线

| 维度 | 结论 |
|---|---|
| 自动化测试 | `78 passed`，但 notebook 自动检查只覆盖 Q1、Q2、Q7 |
| Notebook 执行 | 9 本中 8 本带执行结果；Q2 的 4 个代码单元均未执行 |
| 数据 | 仓库 8 个 Parquet 的 SHA-256 全部与 manifest 一致；三 ETF 缓存截至 `2026-03-03` |
| 课程研究 | Q5-Q6 的验证意识最强；Q8-Q9 又在同一全样本上选择波动率阈值，Q9 使用全样本波动率中位数，违反 Q6 的样本外原则 |
| 包内策略 | `rotation` 使用 3 日动量；`trend_filter` 使用 3 日动量和 2/4 日均线，均不是课程中的风险平价或 20 日动量策略 |
| 本地真实引擎 | 2021-01-04 至 2026-03-03：`rotation -9.45%`、`trend_filter -11.20%`、等权基准 `+97.62%` |
| 交易状态 | 研究/回测原型；不满足真实资金上线条件 |

---

### Task 1: 锁定可复现数据快照

**Files:**
- Create: `src/ai_xquanty/data/snapshot.py`
- Modify: `src/ai_xquanty/data/real_etf.py`
- Modify: `src/ai_xquanty/cli.py`
- Create: `tests/data/test_snapshot.py`
- Modify: `tests/test_cli_smoke.py`

**Interfaces:**
- Produces: `load_parquet_snapshot(symbols: tuple[str, ...], data_dir: Path, start: str, end: str) -> MarketDataBundle`
- Produces: `verify_snapshot_manifest(parquet_path: Path, manifest_path: Path) -> dict[str, object]`
- CLI adds: `run-snapshot-backtest --data-dir ... --start ... --end ... --symbols ... --strategy ... --output-dir ...`

- [ ] **Step 1: Write manifest and calendar-intersection tests**

```python
def test_load_parquet_snapshot_verifies_hash_and_uses_common_calendar(snapshot_dir):
    bundle = load_parquet_snapshot(
        ("510300.SS", "513100.SS", "518880.SS"),
        snapshot_dir,
        "2021-01-04",
        "2026-03-03",
    )
    assert tuple(bundle.instruments) == ("510300.SS", "513100.SS", "518880.SS")
    assert bundle.calendar[0] == pd.Timestamp("2021-01-04")
    assert bundle.calendar[-1] == pd.Timestamp("2026-03-03")
    assert not bundle.bars[["open", "high", "low", "close", "volume"]].isna().any().any()


def test_load_parquet_snapshot_rejects_hash_mismatch(snapshot_dir):
    (snapshot_dir / "510300.SS.manifest.json").write_text(
        '{"symbol":"510300.SS","sha256":"bad"}', encoding="utf-8"
    )
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        load_parquet_snapshot(("510300.SS",), snapshot_dir, "2021-01-04", "2026-03-03")
```

- [ ] **Step 2: Run the focused tests and confirm they fail**

Run: `.venv/bin/python -m pytest tests/data/test_snapshot.py -q`

Expected: import failure for `ai_xquanty.data.snapshot`.

- [ ] **Step 3: Implement the snapshot loader**

```python
def verify_snapshot_manifest(parquet_path: Path, manifest_path: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual = hashlib.sha256(parquet_path.read_bytes()).hexdigest()
    if actual != manifest["sha256"]:
        raise ValueError(f"SHA-256 mismatch for {parquet_path.name}")
    return manifest


def load_parquet_snapshot(
    symbols: tuple[str, ...], data_dir: Path, start: str, end: str
) -> MarketDataBundle:
    if not symbols:
        raise ValueError("symbols must not be empty")
    # 对每个 symbol 验证 manifest，读取 Parquet，取共同交易日，
    # 转为无时区的 (trade_date, symbol) MultiIndex，并复用现有价格校验。
```

- [ ] **Step 4: Add the offline snapshot CLI path and metadata artifact**

`summary.json` 必须新增：

```json
{
  "data_start": "2021-01-04",
  "data_end": "2026-03-03",
  "symbols": ["510300.SS", "513100.SS", "518880.SS"],
  "snapshot_sha256": {
    "510300.SS": "df1c8604ff33b33e1b0b0a146742d8d671badc1869bc3c5aa5b1a2630ea435e5"
  }
}
```

- [ ] **Step 5: Run data and CLI tests**

Run: `.venv/bin/python -m pytest tests/data tests/test_cli_smoke.py -q`

Expected: all selected tests pass and the CLI performs no network request.

- [ ] **Step 6: Commit**

```bash
git add src/ai_xquanty/data/snapshot.py src/ai_xquanty/data/real_etf.py src/ai_xquanty/cli.py tests/data/test_snapshot.py tests/test_cli_smoke.py
git commit -m "feat: add reproducible parquet snapshot backtests"
```

### Task 2: 让策略直接生成目标权重

**Files:**
- Create: `src/ai_xquanty/strategy/targets.py`
- Create: `src/ai_xquanty/strategy/risk_parity.py`
- Modify: `src/ai_xquanty/strategy/registry.py`
- Modify: `src/ai_xquanty/backtest/engine.py`
- Create: `tests/strategy/test_risk_parity.py`
- Modify: `tests/backtest/test_engine.py`

**Interfaces:**
- Produces: `TargetFn = Callable[[MarketDataBundle, pd.Timestamp], TargetPortfolio]`
- Produces: `resolve_target_fn(strategy_name: str) -> TargetFn`
- Produces: `compute_risk_parity_target(bundle: MarketDataBundle, as_of: pd.Timestamp, volatility_window: int, gross_exposure: float) -> TargetPortfolio`
- Existing `rotation` and `trend_filter` are wrapped as target functions without changing their results.

- [ ] **Step 1: Write the no-lookahead risk-parity tests**

```python
def test_risk_parity_target_uses_only_history_through_as_of(bundle):
    original = compute_risk_parity_target(bundle, pd.Timestamp("2024-01-31"), 20, 0.90)
    mutated = replace_prices_after(bundle, "2024-01-31", multiplier=100.0)
    repeated = compute_risk_parity_target(mutated, pd.Timestamp("2024-01-31"), 20, 0.90)
    assert repeated == original


def test_risk_parity_target_reserves_ten_percent_cash(bundle):
    target = compute_risk_parity_target(bundle, pd.Timestamp("2024-01-31"), 20, 0.90)
    assert sum(target.weights.values()) == pytest.approx(1.0)
    assert target.weights["CASH"] == pytest.approx(0.10)
    assert max(weight for symbol, weight in target.weights.items() if symbol != "CASH") <= 0.50
```

- [ ] **Step 2: Run tests and confirm the missing target interface fails**

Run: `.venv/bin/python -m pytest tests/strategy/test_risk_parity.py tests/backtest/test_engine.py -q`

Expected: import failure for `compute_risk_parity_target` or `resolve_target_fn`.

- [ ] **Step 3: Implement inverse-volatility weights**

```python
returns = closes.loc[:as_of].pct_change().tail(volatility_window)
annualized_vol = returns.std(ddof=1) * np.sqrt(252.0)
inverse_vol = 1.0 / annualized_vol
raw = inverse_vol / inverse_vol.sum() * gross_exposure
```

Reject zero, missing, infinite or insufficient volatility history. Clamp each ETF to `0.50`, renormalize the remaining ETF exposure to `0.90`, and assign the residual to `CASH`.

- [ ] **Step 4: Change the engine to consume `TargetFn`**

```python
target_fn = resolve_target_fn(config.strategy_name)
# inside each rebalance
target = target_fn(bundle, trade_date)
```

The wrapper for existing signal strategies calls `build_target_portfolio`; the new risk-parity strategy bypasses the equal-weight conversion.

- [ ] **Step 5: Run strategy and engine tests**

Run: `.venv/bin/python -m pytest tests/strategy tests/portfolio tests/backtest -q`

Expected: all selected tests pass; legacy sample outputs remain unchanged.

- [ ] **Step 6: Commit**

```bash
git add src/ai_xquanty/strategy/targets.py src/ai_xquanty/strategy/risk_parity.py src/ai_xquanty/strategy/registry.py src/ai_xquanty/backtest/engine.py tests/strategy/test_risk_parity.py tests/backtest/test_engine.py
git commit -m "feat: add risk parity target strategy"
```

### Task 3: 显式化回撤停机并防止静默永久空仓

**Files:**
- Modify: `src/ai_xquanty/config.py`
- Modify: `src/ai_xquanty/backtest/engine.py`
- Modify: `src/ai_xquanty/risk/rules.py`
- Modify: `src/ai_xquanty/backtest/__init__.py`
- Modify: `tests/risk/test_rules.py`
- Modify: `tests/backtest/test_engine.py`

**Interfaces:**
- Produces: `BacktestConfig.portfolio_halt_drawdown: float | None`
- Produces: `BacktestResult.halted_at: str | None`
- A hard drawdown breach is a terminal halt with an explicit artifact; candidate research defaults to `None` and relies on exposure sizing rather than an implicit permanent 10% stop.

- [ ] **Step 1: Write terminal-halt and disabled-halt tests**

```python
def test_drawdown_halt_is_reported_and_terminal(bundle):
    result = run_backtest_on_bundle(config_with_halt(0.10), bundle)
    assert result.halted_at == "2021-03-26"
    assert result.equity_curve.loc[
        result.equity_curve.trade_date > result.halted_at, "holdings_value"
    ].eq(0.0).all()


def test_disabled_drawdown_halt_does_not_force_cash(bundle):
    result = run_backtest_on_bundle(config_with_halt(None), bundle)
    assert result.halted_at is None
    assert result.equity_curve.iloc[-1].holdings_value > 0.0
```

- [ ] **Step 2: Run tests and confirm the current hard-coded `0.10` behavior fails**

Run: `.venv/bin/python -m pytest tests/risk/test_rules.py tests/backtest/test_engine.py -q`

Expected: `BacktestConfig` lacks the new field and `BacktestResult` lacks `halted_at`.

- [ ] **Step 3: Move the threshold into config and record the halt date**

Do not add an automatic re-entry rule based on peak drawdown: once cash is held, peak drawdown cannot recover by itself. A later re-entry design requires an independently validated cooldown or market-state rule.

- [ ] **Step 4: Include halt status in `summary.json`**

```json
{
  "halted_at": null,
  "portfolio_halt_drawdown": null
}
```

- [ ] **Step 5: Run risk, engine and reporting tests**

Run: `.venv/bin/python -m pytest tests/risk tests/backtest tests/reporting -q`

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/ai_xquanty/config.py src/ai_xquanty/backtest/engine.py src/ai_xquanty/risk/rules.py src/ai_xquanty/backtest/__init__.py tests/risk/test_rules.py tests/backtest/test_engine.py
git commit -m "fix: make portfolio drawdown halt explicit"
```

### Task 4: 建立统一的交易绩效报告

**Files:**
- Modify: `src/ai_xquanty/reporting/metrics.py`
- Modify: `src/ai_xquanty/reporting/baseline.py`
- Modify: `src/ai_xquanty/reporting/render.py`
- Modify: `tests/reporting/test_baseline.py`
- Create: `tests/reporting/test_metrics.py`
- Modify: `tests/reporting/test_render.py`

**Interfaces:**
- `compute_summary_metrics(equity_curve: pd.DataFrame, fills: pd.DataFrame | None = None) -> dict[str, float]`
- Required fields: `total_return`、`annualized_return`、`annualized_volatility`、`sharpe_ratio`、`sortino_ratio`、`calmar_ratio`、`max_drawdown`、`max_drawdown_duration_days`、`turnover`、`fees_paid`、`num_filled_orders`。
- Baseline comparison adds: `annualized_excess_return`、`tracking_error`、`information_ratio`。

- [ ] **Step 1: Write deterministic metric tests**

```python
def test_compute_summary_metrics_reports_return_risk_and_costs():
    curve = pd.DataFrame({"nav": [100.0, 110.0, 99.0, 121.0]})
    fills = pd.DataFrame({"status": ["filled", "filled"], "fees": [1.0, 2.0]})
    metrics = compute_summary_metrics(curve, fills)
    assert metrics["total_return"] == pytest.approx(0.21)
    assert metrics["max_drawdown"] == pytest.approx(0.10)
    assert metrics["fees_paid"] == pytest.approx(3.0)
    assert metrics["num_filled_orders"] == 2.0
```

- [ ] **Step 2: Run reporting tests and confirm missing metrics fail**

Run: `.venv/bin/python -m pytest tests/reporting -q`

Expected: assertions fail because the current report contains only three fields.

- [ ] **Step 3: Implement metrics from daily NAV returns**

Use `252` trading sessions per year and risk-free rate `0.0`; return `0.0` instead of infinity for a zero denominator, and record the denominator condition in `summary.json` as `metric_warnings`.

- [ ] **Step 4: Write annual returns and drawdown episodes artifacts**

Create `annual_returns.csv` with `year,strategy_return,baseline_return,excess_return` and `drawdowns.csv` with `start,trough,recovered,depth,days_to_trough,days_to_recovery`.

- [ ] **Step 5: Run reporting and full tests**

Run: `.venv/bin/python -m pytest -q`

Expected: the full suite passes.

- [ ] **Step 6: Commit**

```bash
git add src/ai_xquanty/reporting/metrics.py src/ai_xquanty/reporting/baseline.py src/ai_xquanty/reporting/render.py tests/reporting/test_baseline.py tests/reporting/test_metrics.py tests/reporting/test_render.py
git commit -m "feat: add production candidate performance reports"
```

### Task 5: 实现预注册的波动率降仓挑战者

**Files:**
- Create: `src/ai_xquanty/strategy/momentum_vol_filter.py`
- Modify: `src/ai_xquanty/strategy/registry.py`
- Create: `tests/strategy/test_momentum_vol_filter.py`

**Interfaces:**
- Produces: `compute_momentum_vol_target(bundle: MarketDataBundle, as_of: pd.Timestamp, momentum_window: int = 20, volatility_window: int = 20, regime_threshold: float = 0.15, high_vol_gross_exposure: float = 0.45) -> TargetPortfolio`
- Normal regime: select positive 20-day risk-adjusted momentum across all three ETFs and allocate `0.90` gross exposure.
- High-volatility regime: keep the same relative weights but reduce gross exposure to `0.45`; residual is cash.

- [ ] **Step 1: Write leakage and exposure tests**

```python
def test_regime_threshold_is_configuration_not_full_sample_statistic(bundle):
    target = compute_momentum_vol_target(
        bundle, pd.Timestamp("2024-01-31"), regime_threshold=0.15
    )
    assert target.strategy_name == "momentum_vol_filter"


def test_high_volatility_halves_gross_exposure(high_vol_bundle):
    target = compute_momentum_vol_target(
        high_vol_bundle, pd.Timestamp("2024-01-31"), regime_threshold=0.15
    )
    assert sum(v for k, v in target.weights.items() if k != "CASH") == pytest.approx(0.45)
    assert target.weights["CASH"] == pytest.approx(0.55)
```

- [ ] **Step 2: Run tests and confirm the new strategy is missing**

Run: `.venv/bin/python -m pytest tests/strategy/test_momentum_vol_filter.py -q`

Expected: import failure for `compute_momentum_vol_target`.

- [ ] **Step 3: Implement the challenger without using a full-history median**

At `as_of`, compute only trailing windows ending at `as_of`. The fixed `0.15` threshold comes from the protocol and can only be changed before the final holdout run.

- [ ] **Step 4: Register `momentum_vol_filter` in CLI and strategy registry**

Run: `.venv/bin/python -m ai_xquanty.cli run-snapshot-backtest --strategy momentum_vol_filter --start 2021-01-04 --end 2026-03-03 --symbols 510300.SS,513100.SS,518880.SS --data-dir data/oxq/market --output-dir /tmp/ai-xquanty-momentum-vol`

Expected: deterministic artifacts with the snapshot hashes and no network access.

- [ ] **Step 5: Run strategy and CLI tests**

Run: `.venv/bin/python -m pytest tests/strategy tests/test_cli_smoke.py -q`

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/ai_xquanty/strategy/momentum_vol_filter.py src/ai_xquanty/strategy/registry.py tests/strategy/test_momentum_vol_filter.py
git commit -m "feat: add preregistered volatility filtered momentum"
```

### Task 6: 建立 Walk-Forward 选拔与一次性最终保留集

**Files:**
- Create: `src/ai_xquanty/validation/__init__.py`
- Create: `src/ai_xquanty/validation/protocol.py`
- Create: `src/ai_xquanty/validation/walk_forward.py`
- Create: `tests/validation/test_walk_forward.py`
- Modify: `src/ai_xquanty/cli.py`
- Create: `docs/superpowers/specs/project/ai_xquanty/2026-08-12-production-candidate-protocol.md`

**Interfaces:**
- Produces: `ValidationProtocol(train_sessions: int, test_sessions: int, step_sessions: int, final_holdout_start: str, primary_metric: str)`
- Produces: `run_walk_forward(protocol: ValidationProtocol, strategies: tuple[str, ...], bundle: MarketDataBundle) -> pd.DataFrame`
- CLI adds: `validate-candidates` and writes `fold_results.csv`, `parameter_stability.csv`, `go_no_go.json`.

- [ ] **Step 1: Write temporal split tests**

```python
def test_walk_forward_splits_are_ordered_and_non_overlapping(calendar):
    splits = build_splits(calendar, train_sessions=504, test_sessions=126, step_sessions=126)
    for split in splits:
        assert split.train_end < split.test_start
        assert split.test_end < pd.Timestamp("2025-01-02")


def test_final_holdout_is_excluded_from_parameter_selection(calendar):
    splits = build_splits(
        calendar, train_sessions=504, test_sessions=126,
        step_sessions=126, final_holdout_start="2025-01-02"
    )
    assert all(split.test_end < pd.Timestamp("2025-01-02") for split in splits)
```

- [ ] **Step 2: Run tests and confirm validation modules are missing**

Run: `.venv/bin/python -m pytest tests/validation -q`

Expected: import failure for `ai_xquanty.validation`.

- [ ] **Step 3: Implement expanding-window validation**

Use at least `504` training sessions, `126` test sessions and `126` step sessions. Parameter selection uses only completed training windows. The final holdout begins `2025-01-02` and is not inspected until the protocol file is committed.

- [ ] **Step 4: Encode go/no-go thresholds**

The candidate advances to simulated trading only if all conditions hold:

```json
{
  "median_fold_excess_return_gt": 0.0,
  "mean_oos_sharpe_gte": 0.7,
  "positive_excess_fold_ratio_gte": 0.6,
  "final_holdout_excess_return_gt": 0.0,
  "final_holdout_max_drawdown_lte": 0.15,
  "annualized_cost_drag_lte": 0.015,
  "parameter_choices_used_lte": 27
}
```

If no candidate passes, retain the equal-weight benchmark and return to hypothesis design; do not widen the parameter grid.

- [ ] **Step 5: Run the full validation command once**

Run: `.venv/bin/python -m ai_xquanty.cli validate-candidates --data-dir data/oxq/market --symbols 510300.SS,513100.SS,518880.SS --start 2021-01-04 --end 2026-03-03 --final-holdout-start 2025-01-02 --output-dir outputs/candidate-validation`

Expected: one deterministic go/no-go decision with all fold rows and snapshot hashes.

- [ ] **Step 6: Run validation and full tests**

Run: `.venv/bin/python -m pytest -q`

Expected: the full suite passes.

- [ ] **Step 7: Commit protocol before discussing threshold changes**

```bash
git add src/ai_xquanty/validation src/ai_xquanty/cli.py tests/validation docs/superpowers/specs/project/ai_xquanty/2026-08-12-production-candidate-protocol.md
git commit -m "feat: add preregistered candidate validation"
```

### Task 7: 进行 12 周人工模拟盘与执行对账

**Files:**
- Create: `src/ai_xquanty/execution/order_plan.py`
- Create: `src/ai_xquanty/execution/reconcile.py`
- Create: `src/ai_xquanty/monitoring/health.py`
- Create: `tests/execution/test_order_plan.py`
- Create: `tests/execution/test_reconcile.py`
- Create: `tests/monitoring/test_health.py`
- Modify: `src/ai_xquanty/cli.py`

**Interfaces:**
- Produces: `write_order_plan(target: TargetPortfolio, positions: dict[str, PositionSnapshot], prices: pd.Series, account_value: float, path: Path) -> None`
- Produces: `reconcile_fills(order_plan: pd.DataFrame, actual_fills: pd.DataFrame) -> pd.DataFrame`
- Produces: `evaluate_execution_health(reconciliation: pd.DataFrame) -> dict[str, float | bool]`
- No broker API or automatic order submission is added.

- [ ] **Step 1: Write order-plan and reconciliation tests**

```python
def test_order_plan_is_a_share_lot_rounded_and_cash_safe():
    plan = build_order_plan(target, positions, prices, account_value=100_000.0)
    assert (plan.quantity % 100 == 0).all()
    assert plan.loc[plan.side == "BUY", "estimated_cash_change"].sum() <= 100_000.0


def test_reconciliation_reports_implementation_shortfall():
    report = reconcile_fills(order_plan, actual_fills)
    assert "slippage_bps" in report
    assert "quantity_difference" in report
    assert "fee_difference" in report
```

- [ ] **Step 2: Run tests and confirm the modules are missing**

Run: `.venv/bin/python -m pytest tests/execution/test_order_plan.py tests/execution/test_reconcile.py tests/monitoring/test_health.py -q`

Expected: import failure for the new modules.

- [ ] **Step 3: Implement cash-safe order generation and manual fill import**

The CLI writes `order_plan.csv`; the user manually executes in a paper account and imports `actual_fills.csv`. Reject duplicate fill IDs, unknown symbols, negative quantities and fills outside the planned trading session.

- [ ] **Step 4: Encode the 12-week paper gate**

Advance only after all conditions hold:

- at least `12` calendar weeks;
- at least `6` rebalance decisions and `20` matched fills;
- `100%` daily data completeness;
- no position or cash reconciliation mismatch after T+1 settlement;
- median absolute slippage `<= 15 bps` and 95th percentile absolute slippage `<= 100 bps`;
- annualized implementation cost estimate `<= 1.5%`;
- simulated strategy has positive excess return over the same-period equal-weight benchmark.

- [ ] **Step 5: Run full tests**

Run: `.venv/bin/python -m pytest -q`

Expected: the full suite passes.

- [ ] **Step 6: Commit**

```bash
git add src/ai_xquanty/execution/order_plan.py src/ai_xquanty/execution/reconcile.py src/ai_xquanty/monitoring/health.py src/ai_xquanty/cli.py tests/execution/test_order_plan.py tests/execution/test_reconcile.py tests/monitoring/test_health.py
git commit -m "feat: add manual paper trading reconciliation"
```

## Execution Decision

完成 Task 1-6 之前，结论固定为 `NO-GO`。Task 6 通过后进入 12 周人工模拟盘；Task 7 通过后，只形成“小资金灰度建议”，不自动创建真实订单。真实资金阶段建议从可投资资金的 `5%` 开始，单 ETF 不超过总资金的 `2.5%`，无融资、无做空，并要求用户对券商、账户、交易时段和停机规则另行确认。

## Self-Review

- Spec coverage: 数据、策略、风控、报告、样本外、执行与监控均有独立任务和验收门槛。
- Placeholder scan: 计划未保留待定实现项；参数、接口、命令与门槛均已写明。
- Type consistency: 策略统一产生 `TargetPortfolio`；引擎、风控、订单计划和报告均消费同一对象。
- Scope control: 不接券商、不扩标的池、不增加机器学习或大规模参数搜索。
