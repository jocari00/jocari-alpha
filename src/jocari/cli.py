"""Command line entry points.

  python -m jocari.cli check-decisions
"""
from __future__ import annotations

import argparse
import sys

from .config import load_instruments, load_portfolios
from .rules import check_portfolio


def check_decisions(_a) -> int:
    instruments = load_instruments()
    failed = False
    for p in load_portfolios().values():
        errors, warnings = check_portfolio(p, instruments)
        for w in warnings:
            print(f"::warning::{w}")
        for e in errors:
            print(f"::error::{e}")
            failed = True
    print("decisions OK" if not failed else "decisions FAILED")
    return 1 if failed else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="jocari")
    sub = ap.add_subparsers(required=True)
    p = sub.add_parser("check-decisions", help="validate /decisions against the construction rules")
    p.set_defaults(fn=check_decisions)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
