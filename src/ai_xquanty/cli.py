import argparse
from pathlib import Path

from ai_xquanty.backtest.engine import (
    BacktestResult,
    run_backtest,
    run_backtest_on_bundle,
)
from ai_xquanty.config import BacktestConfig, RealBacktestConfig
from ai_xquanty.data.real_etf import prepare_real_market_data
from ai_xquanty.reporting.baseline import compute_baseline_comparison
from ai_xquanty.reporting.render import write_backtest_artifacts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-xquanty")
    subparsers = parser.add_subparsers(dest="command")
    sample_parser = subparsers.add_parser("run-sample-backtest")
    sample_parser.add_argument("--output-dir", required=True)
    real_parser = subparsers.add_parser("run-real-backtest")
    real_parser.add_argument(
        "--strategy", required=True, choices=["rotation", "trend_filter"]
    )
    real_parser.add_argument("--start", required=True)
    real_parser.add_argument("--end", required=True)
    real_parser.add_argument("--symbols", required=True)
    real_parser.add_argument("--cache-dir", required=True)
    real_parser.add_argument("--output-dir", required=True)
    real_parser.add_argument("--refresh-cache", action="store_true")
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
    if args.command == "run-real-backtest":
        config = RealBacktestConfig(
            start=args.start,
            end=args.end,
            symbols=tuple(
                symbol.strip() for symbol in args.symbols.split(",") if symbol.strip()
            ),
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
    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
