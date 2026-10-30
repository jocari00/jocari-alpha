"""NAV storage (one CSV per ISIN in private-data/nav/) and validation of new observations.

private-data/ is a separate private repository: raw NAVs are third-party data and are
never published. Only combined portfolio returns derived from them are.

CSV columns: date, nav, basis, source, retrieved_at, note
- `basis` is `nav` (a published NAV) or `index` (a value backed out from returns,
  base 100 at the anchor, used when the document states no NAV). Only ratios within
  a series are ever used, so both work; a series must not mix them.
- `source` is the URL or document the NAV was read from, or `manual`.
- Rows are append-only in date order. A correction is a deliberate edit of an
  existing row, done in its own commit with the reason in the message.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from .config import ROOT

FIELDS = ["date", "nav", "basis", "source", "retrieved_at", "note"]
# Daily moves above these thresholds are rejected unless explicitly confirmed.
MAX_DAILY_MOVE = {"fixed_income": 0.03, "equity": 0.08}


@dataclass
class Observation:
    isin: str
    date: date
    nav: float
    source: str
    note: str = ""
    basis: str = "nav"


class ValidationError(ValueError):
    pass


DATA_ROOT = ROOT / "private-data"


def nav_path(isin: str, root: Path = DATA_ROOT) -> Path:
    return root / "nav" / f"{isin}.csv"


def read_nav(isin: str, root: Path = DATA_ROOT) -> pd.Series:
    p = nav_path(isin, root)
    if not p.exists():
        return pd.Series(dtype=float, name=isin)
    df = pd.read_csv(p, parse_dates=["date"])
    return pd.Series(df["nav"].values, index=pd.DatetimeIndex(df["date"]), name=isin)


def validate(obs: Observation, history: pd.Series, asset_class: str, today: date | None = None,
             confirm_jump: bool = False) -> None:
    today = today or date.today()
    if obs.date > today:
        raise ValidationError(f"{obs.isin}: date {obs.date} is in the future")
    if obs.date.weekday() >= 5:
        raise ValidationError(f"{obs.isin}: {obs.date} is a weekend")
    if not obs.nav > 0:
        raise ValidationError(f"{obs.isin}: NAV must be positive, got {obs.nav}")
    if not history.empty:
        last_date = history.index[-1].date()
        if obs.date in set(history.index.date):
            raise ValidationError(f"{obs.isin}: {obs.date} already stored (duplicate)")
        if obs.date < last_date:
            raise ValidationError(f"{obs.isin}: {obs.date} is before the last stored date {last_date}")
        move = obs.nav / history.iloc[-1] - 1
        limit = MAX_DAILY_MOVE[asset_class]
        if abs(move) > limit and not confirm_jump:
            raise ValidationError(
                f"{obs.isin}: move of {move:+.2%} vs {last_date} exceeds {limit:.0%}; "
                "check the source and re-run with confirmation if it is real")


def append(obs: Observation, root: Path = DATA_ROOT) -> None:
    p = nav_path(obs.isin, root)
    p.parent.mkdir(parents=True, exist_ok=True)
    new = not p.exists()
    with open(p, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow({
            "date": obs.date.isoformat(), "nav": repr(obs.nav), "basis": obs.basis, "source": obs.source,
            "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "note": obs.note,
        })


def log_failure(isin: str, message: str, root: Path = DATA_ROOT) -> None:
    """Record a failed fetch/validation. The last stored NAV is kept; nothing is invented."""
    p = root / "log" / "ingestion_failures.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    new = not p.exists()
    with open(p, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["logged_at", "isin", "message"])
        w.writerow([datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), isin, message])
