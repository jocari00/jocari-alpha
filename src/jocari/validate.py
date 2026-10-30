"""Validation of NAV observations read from the Drive sheet before they are used.

The NAVs themselves are collected by the weekly routine into Google Drive (tab
"VL fondos"); nothing here stores them. A row that fails validation is reported
and left out: the calculation never fills it in.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

# Moves between consecutive observations above these thresholds are rejected unless
# confirmed. The check only applies to observations at most MOVE_CHECK_DAYS apart
# (weekly or month-end NAVs); the base (2025-12-31) to the live start is ten months.
MAX_MOVE = {"fixed_income": 0.05, "equity": 0.15}
MOVE_CHECK_DAYS = 35


@dataclass
class Observation:
    isin: str
    date: date
    nav: float
    source: str = ""


class ValidationError(ValueError):
    pass


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
        limit = MAX_MOVE[asset_class]
        close = (obs.date - last_date).days <= MOVE_CHECK_DAYS
        if close and abs(move) > limit and not confirm_jump:
            raise ValidationError(
                f"{obs.isin}: move of {move:+.2%} vs {last_date} exceeds {limit:.0%}; "
                "check the source and confirm it if it is real")
