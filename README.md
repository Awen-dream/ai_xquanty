# ai-xquanty

Quantitative research tools for ETF backtesting.

## Current Scope

- Research, backtest, and paper execution only
- Bundled ETF sample universe only
- No broker connectivity and no live order routing

## Run The Sample Backtest

```bash
python -m ai_xquanty.cli run-sample-backtest --output-dir outputs/sample_run
```

The command uses the bundled CSV data and writes deterministic, cost-aware
backtest artifacts to the selected directory: `summary.json`,
`equity_curve.csv`, and `fills.csv`.
