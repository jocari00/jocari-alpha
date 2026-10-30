"""Command line entry points.

  python -m jocari.cli add-nav ISIN YYYY-MM-DD NAV --source URL_OR_manual [--note ...] [--confirm-jump]
  python -m jocari.cli check-decisions
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

from .config import load_benchmark_instruments, load_instruments, load_portfolios
from .navstore import Observation, ValidationError, append, read_nav, validate
from .rules import check_portfolio


def add_nav(a) -> int:
    instruments = load_instruments()
    benchmarks = load_benchmark_instruments()
    if a.isin in instruments:
        asset_class = instruments[a.isin].asset_class
    elif a.isin in benchmarks:
        asset_class = benchmarks[a.isin]["sleeve"]
    else:
        print(f"unknown ISIN {a.isin}", file=sys.stderr)
        return 2
    obs = Observation(a.isin, date.fromisoformat(a.date), float(a.nav), a.source, a.note)
    try:
        validate(obs, read_nav(a.isin), asset_class, confirm_jump=a.confirm_jump)
    except ValidationError as e:
        print(f"rejected: {e}", file=sys.stderr)
        return 1
    append(obs)
    print(f"stored {obs.isin} {obs.date} {obs.nav}")
    return 0


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
    p = sub.add_parser("add-nav", help="add one NAV by hand (validated)")
    p.add_argument("isin")
    p.add_argument("date")
    p.add_argument("nav")
    p.add_argument("--source", required=True, help="URL or document the NAV comes from, or 'manual'")
    p.add_argument("--note", default="")
    p.add_argument("--confirm-jump", action="store_true", help="accept a move above the anomaly threshold")
    p.set_defaults(fn=add_nav)
    p = sub.add_parser("check-decisions", help="validate /decisions against the construction rules")
    p.set_defaults(fn=check_decisions)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
