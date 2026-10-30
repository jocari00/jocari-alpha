"""Return figures on a portfolio or benchmark value series (valuation dates only).

Returns are never annualised. Risk metrics (volatility, Sharpe, drawdown...) are
deferred until there is at least one year of live history.
"""
from __future__ import annotations

import pandas as pd


def cumulative_return(v: pd.Series) -> float:
    return v.iloc[-1] / v.iloc[0] - 1


def _value_on_or_before(v: pd.Series, t: pd.Timestamp) -> float:
    s = v[v.index <= t]
    return s.iloc[-1] if not s.empty else v.iloc[0]


def ytd_return(v: pd.Series, asof: pd.Timestamp | None = None) -> float:
    asof = v.index[-1] if asof is None else asof
    base = _value_on_or_before(v, pd.Timestamp(asof.year - 1, 12, 31))
    return _value_on_or_before(v, asof) / base - 1


def period_returns(v: pd.Series) -> pd.Series:
    """Return of each valuation period, indexed by its end date."""
    return (v / v.shift(1) - 1).dropna()
