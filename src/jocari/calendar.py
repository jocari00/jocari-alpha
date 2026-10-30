"""TARGET2 business-day calendar (the common calendar all series are aligned to)."""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd


def easter_sunday(year: int) -> date:
    """Anonymous Gregorian algorithm (Meeus/Jones/Butcher)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def target2_holidays(year: int) -> set[date]:
    e = easter_sunday(year)
    return {
        date(year, 1, 1), e - timedelta(days=2), e + timedelta(days=1),
        date(year, 5, 1), date(year, 12, 25), date(year, 12, 26),
    }


def business_days(start: date, end: date) -> pd.DatetimeIndex:
    hol = set()
    for y in range(start.year, end.year + 1):
        hol |= target2_holidays(y)
    return pd.DatetimeIndex([d for d in pd.bdate_range(start, end) if d.date() not in hol])
