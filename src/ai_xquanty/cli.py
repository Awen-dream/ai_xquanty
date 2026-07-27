import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-xquanty")
    parser.add_argument("--help-only", action="store_true")
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
