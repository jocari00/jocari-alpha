"""Return and risk metrics on a daily value series (TARGET2 calendar).

- Returns are never annualised for periods shorter than one year.
- Risk ratios use daily returns and the sqrt(252) convention; results carry a
  `period_lt_1y` flag so the site can add the "period shorter than 1 year" note.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

PERIODS_PER_YEAR = 252


def daily_returns(v: pd.Series) -> pd.Series:
    return v.pct_change().dropna()


def cumulative_return(v: pd.Series) -> float:
    return v.iloc[-1] / v.iloc[0] - 1


def _value_on_or_before(v: pd.Series, t: pd.Timestamp) -> float:
    s = v[v.index <= t]
    return s.iloc[-1] if not s.empty else v.iloc[0]


def ytd_return(v: pd.Series, asof: pd.Timestamp | None = None) -> float:
    asof = v.index[-1] if asof is None else asof
    base = _value_on_or_before(v, pd.Timestamp(asof.year - 1, 12, 31))
    return _value_on_or_before(v, asof) / base - 1


def mtd_return(v: pd.Series, asof: pd.Timestamp | None = None) -> float:
    asof = v.index[-1] if asof is None else asof
    base = _value_on_or_before(v, asof.replace(day=1) - pd.Timedelta(days=1))
    return _value_on_or_before(v, asof) / base - 1


def monthly_returns(v: pd.Series) -> pd.DataFrame:
    """Years in rows, months 1..12 in columns.

    The base date is a month end (2025-12-31), so the first month shown is the one
    after it, measured from the base value.
    """
    ends = v.groupby([v.index.year, v.index.month]).last()
    r = (ends / ends.shift(1) - 1).dropna()
    table = r.unstack()
    table.index.name, table.columns.name = "year", "month"
    return table.reindex(columns=range(1, 13))


def drawdown(v: pd.Series) -> pd.Series:
    return v / v.cummax() - 1


def max_drawdown(v: pd.Series) -> float:
    return float(drawdown(v).min())


def volatility(r: pd.Series) -> float:
    return float(r.std(ddof=1) * math.sqrt(PERIODS_PER_YEAR))


def _excess(r: pd.Series, rf: pd.Series | float) -> pd.Series:
    if isinstance(rf, pd.Series):
        rf = rf.reindex(r.index).fillna(0.0)
    return r - rf


def sharpe(r: pd.Series, rf: pd.Series | float = 0.0) -> float:
    ex = _excess(r, rf)
    return float(ex.mean() / ex.std(ddof=1) * math.sqrt(PERIODS_PER_YEAR))


def sortino(r: pd.Series, rf: pd.Series | float = 0.0) -> float:
    """Downside deviation over all observations, target = risk-free."""
    ex = _excess(r, rf)
    dd = math.sqrt((np.minimum(ex, 0.0) ** 2).mean())
    return float(ex.mean() / dd * math.sqrt(PERIODS_PER_YEAR)) if dd else float("nan")


def tracking_error(rp: pd.Series, rb: pd.Series) -> float:
    return float((rp - rb).std(ddof=1) * math.sqrt(PERIODS_PER_YEAR))


def beta(rp: pd.Series, rb: pd.Series) -> float:
    return float(rp.cov(rb) / rb.var(ddof=1))


def summary(v: pd.Series, b: pd.Series, rf: pd.Series | float = 0.0) -> dict:
    rp, rb = daily_returns(v), daily_returns(b)
    days = (v.index[-1] - v.index[0]).days
    return {
        "start": v.index[0].date().isoformat(),
        "end": v.index[-1].date().isoformat(),
        "period_lt_1y": days < 365,
        "return_mtd": mtd_return(v), "benchmark_mtd": mtd_return(b),
        "return_ytd": ytd_return(v), "benchmark_ytd": ytd_return(b),
        "return_since_inception": cumulative_return(v), "benchmark_since_inception": cumulative_return(b),
        "excess_return": cumulative_return(v) - cumulative_return(b),
        "volatility": volatility(rp), "benchmark_volatility": volatility(rb),
        "max_drawdown": max_drawdown(v), "benchmark_max_drawdown": max_drawdown(b),
        "sharpe": sharpe(rp, rf), "sortino": sortino(rp, rf),
        "tracking_error": tracking_error(rp, rb), "beta": beta(rp, rb),
    }
