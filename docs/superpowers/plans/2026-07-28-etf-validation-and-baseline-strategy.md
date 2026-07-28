# ETF Validation And Baseline Strategy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a concrete strategy-validity standard and implement the first ETF baseline strategy as a tested signal module.

**Architecture:** Keep the “how do we judge validity” guidance in the course validation area so it stays close to the teaching materials, and add the first reusable ETF strategy under `src/ai_xquanty/strategy/`. The strategy stays intentionally simple: trend filter first, ranking second, with no parameter scan baked into the implementation.

**Tech Stack:** Markdown, Python 3.12, pandas, numpy, pytest

## Global Constraints

- Continue working on branch `codex/subproject-1-main`
- Do not create or use a new worktree; user explicitly chose branch-based isolation
- Strategy validity guidance must clearly distinguish “教学跑通” from “投资有效”
- New baseline strategy must avoid implicit parameter optimization logic
- Follow TDD: test first, verify failure, then implement minimal production code

---

### Task 1: Add strategy validity standard document

**Files:**
- Create: `docs/superpowers/specs/course/q5-how-to-validate/2026-07-28-strategy-validity-standard.md`

**Interfaces:**
- Consumes: Q1 execution findings, existing Q5 validation chapter positioning
- Produces: A stable written checklist for judging whether a strategy is merely runnable or actually investable

- [ ] **Step 1: Write the document with four decision layers**

```markdown
# 策略有效性判定标准

## 四层判定

1. 工程跑通
2. 基线比较
3. 样本外稳定性
4. 执行可落地性
```

- [ ] **Step 2: Include the current Q1 conclusion explicitly**

```markdown
- Q1 简单定投：可作为基线
- Q1 均线增强定投：当前样本下未证明优于基线
- Q1 参数扫描与样本外验证：证明了过拟合风险
```

- [ ] **Step 3: Re-read the document for scope and wording**

Check manually:
- It belongs under `q5-how-to-validate/`
- It defines pass / fail style criteria rather than vague advice
- It names the next baseline strategy direction

### Task 2: Add failing tests for the first ETF baseline strategy

**Files:**
- Create: `tests/strategy/test_etf_trend_filter.py`

**Interfaces:**
- Consumes: `MarketDataBundle`, `SignalSnapshot`
- Produces: Test-defined contract for `compute_trend_filter_signals(bundle, as_of, lookback_days, short_window, long_window, top_n)`

- [ ] **Step 1: Write the failing test for trend-qualified ranking**

```python
def test_compute_trend_filter_signals_ranks_only_symbols_above_long_trend(sample_bundle):
    signals = compute_trend_filter_signals(
        sample_bundle,
        as_of=pd.Timestamp("2024-01-08"),
        lookback_days=3,
        short_window=2,
        long_window=4,
        top_n=2,
    )

    assert [signal.symbol for signal in signals] == ["510300.SH", "510500.SH"]
    assert all(signal.strategy_name == "etf_trend_filter" for signal in signals)
```

- [ ] **Step 2: Write the failing test for “all symbols below trend returns empty”**

```python
def test_compute_trend_filter_signals_returns_empty_when_no_symbol_passes_filter(sample_bundle):
    sample_bundle.bars.loc[(pd.Timestamp("2024-01-08"), slice(None)), "close"] = [1.0, 1.0, 1.0, 1.0]

    signals = compute_trend_filter_signals(
        sample_bundle,
        as_of=pd.Timestamp("2024-01-08"),
        lookback_days=3,
        short_window=2,
        long_window=4,
        top_n=2,
    )

    assert signals == []
```

- [ ] **Step 3: Write the failing test for insufficient history**

```python
def test_compute_trend_filter_signals_rejects_insufficient_history(sample_bundle):
    with pytest.raises(ValueError, match="history"):
        compute_trend_filter_signals(
            sample_bundle,
            as_of=pd.Timestamp("2024-01-03"),
            lookback_days=3,
            short_window=2,
            long_window=4,
            top_n=2,
        )
```

- [ ] **Step 4: Run the new test file to verify RED**

Run: `.venv/bin/pytest tests/strategy/test_etf_trend_filter.py -q`
Expected: FAIL with import or missing-function error

### Task 3: Implement the ETF trend filter strategy minimally

**Files:**
- Create: `src/ai_xquanty/strategy/etf_trend_filter.py`

**Interfaces:**
- Consumes: `MarketDataBundle.bars` with `close` prices indexed by `trade_date`, `symbol`
- Produces: `compute_trend_filter_signals(bundle, as_of, lookback_days, short_window, long_window, top_n) -> list[SignalSnapshot]`

- [ ] **Step 1: Implement the minimal function**

```python
def compute_trend_filter_signals(bundle, as_of, lookback_days, short_window, long_window, top_n):
    closes = bundle.bars["close"].unstack("symbol").sort_index()
    history_length = max(lookback_days + 1, long_window)
    window = closes.loc[:as_of].tail(history_length)
    if len(window) < history_length:
        raise ValueError("Insufficient history for trend filter")
    close_values = window.to_numpy(dtype=float)
    if not np.isfinite(close_values).all() or (close_values <= 0).any():
        raise ValueError("Trend filter history contains invalid close prices")

    trailing_returns = window.iloc[-1] / window.iloc[-(lookback_days + 1)] - 1.0
    short_ma = window.tail(short_window).mean()
    long_ma = window.tail(long_window).mean()
    latest_close = window.iloc[-1]
    eligible = (latest_close > long_ma) & (short_ma > long_ma)
    ranked = trailing_returns[eligible].sort_values(ascending=False).head(top_n)
    return [
        SignalSnapshot(
            trade_date=as_of.date(),
            strategy_name="etf_trend_filter",
            symbol=symbol,
            score=float(score),
        )
        for symbol, score in ranked.items()
    ]
```

- [ ] **Step 2: Run the new test file to verify GREEN**

Run: `.venv/bin/pytest tests/strategy/test_etf_trend_filter.py -q`
Expected: PASS

- [ ] **Step 3: Run the existing strategy tests to guard regressions**

Run: `.venv/bin/pytest tests/strategy/test_etf_rotation.py tests/strategy/test_etf_trend_filter.py -q`
Expected: PASS

### Task 4: Verify and summarize

**Files:**
- Modify: none

**Interfaces:**
- Consumes: New document and strategy test results
- Produces: Verified status report for the user

- [ ] **Step 1: Run the full targeted verification set**

Run: `.venv/bin/pytest tests/strategy/test_etf_rotation.py tests/strategy/test_etf_trend_filter.py tests/backtest/test_engine.py -q`
Expected: PASS

- [ ] **Step 2: Check git status for the exact changed files**

Run: `git status --short`
Expected: Shows the new Q5 document, new strategy module, new tests, and any already-existing notebook refresh changes

- [ ] **Step 3: Report the outcome in user terms**

The report must cover:
- where the validity standard lives
- what the first ETF baseline strategy does
- whether tests passed
- what still remains before a real-money validation cycle
