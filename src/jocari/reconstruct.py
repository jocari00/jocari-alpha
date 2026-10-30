"""Back out month-end values from factsheet figures (reconstructed period only).

A factsheet gives one anchor value (a NAV, or 100 when no NAV is stated) and either
a table of calendar-month returns or cumulative returns over 1m / 3m / 6m / YTD.
Every point is obtained by dividing the anchor by (1 + return); nothing is
interpolated, so months the document does not cover stay missing.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

PERIOD_MONTHS = {"1m": 1, "3m": 3, "6m": 6}


def month_end(year: int, month: int) -> date:
    return (pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(0)).date()


def _shift_month_end(d: date, months: int) -> date:
    t = pd.Timestamp(d.year, d.month, 1) - pd.DateOffset(months=months)
    return month_end(t.year, t.month)


def from_monthly(anchor_date: date, anchor_value: float, monthly: list[float]) -> dict[date, float]:
    """`monthly` holds the year's returns (%) from January up to the anchor's month."""
    year = anchor_date.year
    if len(monthly) != anchor_date.month:
        raise ValueError(f"{len(monthly)} monthly returns but anchor is month {anchor_date.month}")
    points = {anchor_date: anchor_value}
    v = anchor_value
    for m in range(anchor_date.month, 0, -1):
        v = v / (1 + monthly[m - 1] / 100)
        points[month_end(year - 1, 12) if m == 1 else month_end(year, m - 1)] = v
    return dict(sorted(points.items()))


def from_cumulative(anchor_date: date, anchor_value: float, cumulative: dict[str, float],
                    one_month_start: date | None = None) -> dict[date, float]:
    points = {anchor_date: anchor_value}
    for period, r in cumulative.items():
        if period == "ytd":
            d = date(anchor_date.year - 1, 12, 31)
        elif period == "1m" and one_month_start is not None:
            d = one_month_start
        else:
            d = _shift_month_end(anchor_date, PERIOD_MONTHS[period])
        points[d] = anchor_value / (1 + r / 100)
    return dict(sorted(points.items()))


def ytd_matches(monthly: list[float], ytd: float, tol: float = 0.06) -> bool:
    """Compounded monthly returns must reproduce the stated YTD within rounding."""
    g = 1.0
    for r in monthly:
        g *= 1 + r / 100
    return abs((g - 1) * 100 - ytd) <= tol
