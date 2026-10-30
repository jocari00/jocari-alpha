"""Command line entry points.

  python -m jocari.cli check-decisions
  python -m jocari.cli compute --nav vl_fondos.csv --asof YYYY-MM-DD --json out.json --table out.csv
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

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


def compute_cmd(a) -> int:
    from .compute import compute, write_outputs
    doc, table = compute(Path(a.nav), date.fromisoformat(a.asof))
    write_outputs(doc, table, Path(a.json) if a.json else None, Path(a.table) if a.table else None)
    for pid, e in doc["portfolios"].items():
        if e["periods"]:
            last = e["periods"][-1]
            print(f"{e['name']:13s} to {last['to']}: portfolio {last['portfolio']:+.2%}  "
                  f"benchmark {last['benchmark']:+.2%}  YTD {e['ytd']['portfolio']:+.2%} vs {e['ytd']['benchmark']:+.2%}")
        else:
            print(f"{e['name']:13s} not valued; missing: {e['missing']}")
    for r in doc["rejected_rows"]:
        print(f"::warning::rejected {r['isin']} {r['date']}: {r['reason']}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="jocari")
    sub = ap.add_subparsers(required=True)
    p = sub.add_parser("check-decisions", help="validate /decisions against the construction rules")
    p.set_defaults(fn=check_decisions)
    p = sub.add_parser("compute", help="portfolio and benchmark returns from the Drive NAV export")
    p.add_argument("--nav", required=True, help="CSV export of the 'VL fondos' tab")
    p.add_argument("--asof", required=True, help="last date to include (YYYY-MM-DD)")
    p.add_argument("--json", help="output JSON (combined returns only)")
    p.add_argument("--table", help="output CSV for the 'Carteras vs benchmark' tab")
    p.set_defaults(fn=compute_cmd)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
