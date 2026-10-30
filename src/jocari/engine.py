"""Portfolio valuation: NAVs on valuation dates + decisions -> portfolio value.

Conventions (documented on the Methodology page and in config/tracking.yaml):
- Valuation dates: the base (2025-12-31, value 100), the live start (2026-10-30) and
  every month end after it. The first period (base -> live start) is the estimated YTD.
- Each instrument takes its last NAV published within `max_gap_days` before a date
  (covers holidays, valuation holidays and Fermat's weekly NAV). If there is none the
  value is missing: nothing is carried forward over a gap and nothing is interpolated.
  A portfolio is only valued on dates where every holding has a value.
- Constant weights: at every valuation date the portfolio is reset to its target
  weights, so a period's return is the weighted average of its funds' returns.
- No external cash flows, so the time-weighted return equals the value ratio.
"""
from __future__ import annotations

import pandas as pd

from .config import Decision

MAX_GAP_DAYS = 7


class DataError(ValueError):
    pass


def align(navs: dict[str, pd.Series], dates: pd.DatetimeIndex,
          max_gap_days: int = MAX_GAP_DAYS) -> pd.DataFrame:
    """Value of each series on each date: its last NAV within max_gap_days, else NaN.

    Raises DataError if an instrument has no NAV for the first date (the base).
    """
    cols = {}
    for isin, s in navs.items():
        s = s.sort_index()
        s = s[~s.index.duplicated(keep="last")]
        vals = []
        for t in dates:
            prior = s[(s.index <= t) & (s.index > t - pd.Timedelta(days=max_gap_days + 1))]
            vals.append(prior.iloc[-1] if not prior.empty else float("nan"))
        if pd.isna(vals[0]):
            raise DataError(f"{isin}: no NAV within {max_gap_days} days of base date {dates[0].date()}")
        cols[isin] = vals
    return pd.DataFrame(cols, index=dates)


def complete_dates(nav: pd.DataFrame, isins) -> pd.DatetimeIndex:
    """Dates on which every listed instrument has a value."""
    return nav.index[nav[list(isins)].notna().all(axis=1)]


def constant_weights(decisions: list[Decision], nav: pd.DataFrame, base_value: float = 100.0
                     ) -> pd.Series:
    """Portfolio value on each date of `nav`, resetting to target weights at every date.

    The weights for the period (t-1, t] are those of the latest decision effective on
    or before t-1. Every holding must have a value on every date (use complete_dates).
    """
    if not decisions:
        raise ValueError("no decisions")
    decisions = sorted(decisions, key=lambda d: d.effective_date)
    if pd.Timestamp(decisions[0].effective_date) != nav.index[0]:
        raise ValueError(f"first date must be the initial decision date {decisions[0].effective_date}")
    values = [base_value]
    for prev, t in zip(nav.index[:-1], nav.index[1:]):
        w = [d for d in decisions if pd.Timestamp(d.effective_date) <= prev][-1].weights
        missing = [i for i in w if pd.isna(nav.at[prev, i]) or pd.isna(nav.at[t, i])]
        if missing:
            raise DataError(f"no NAV for {missing} on {prev.date()} or {t.date()}")
        r = sum(wt / 100 * (nav.at[t, i] / nav.at[prev, i] - 1) for i, wt in w.items())
        values.append(values[-1] * (1 + r))
    return pd.Series(values, index=nav.index, name="value")
