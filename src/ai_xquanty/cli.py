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


if __name__ == "__main__":
    raise SystemExit(main())
