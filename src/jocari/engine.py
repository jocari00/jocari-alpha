"""Portfolio simulation: aligned NAVs + decisions -> daily portfolio value.

Conventions (documented on the Methodology page):
- All series are aligned to the TARGET2 business-day calendar. A NAV missing on a
  calendar day (local holiday, weekly NAV) is carried forward from the last
  published value. Nothing is ever interpolated.
- Base date: the initial decision's effective date (2025-12-31). Each fund's base
  NAV is its last NAV published on or before that date. Value = 100 at base.
- Buy and hold: units are fixed after each decision, so weights drift with the market.
- No external cash flows, so the time-weighted return equals the value ratio.
- A later decision (rebalance) is turned into an order per fund, sized with the
  portfolio value on the effective date D, and executed at the NAV of D + the fund's
  trade_lag_days. Cash between a sale and a purchase earns 0% (cash may be briefly
  negative if a purchase settles before a sale; also at 0%).
"""
from __future__ import annotations

import pandas as pd

from .config import Decision, Instrument


class DataError(ValueError):
    pass


def align(navs: dict[str, pd.Series], calendar: pd.DatetimeIndex) -> pd.DataFrame:
    """Align raw NAV series (DatetimeIndex -> NAV) to the calendar, carrying values forward.

    Values published before the first calendar day are used only to seed the base.
    Raises DataError if an instrument has no NAV on or before the first calendar day.
    """
    cols = {}
    for isin, s in navs.items():
        s = s.sort_index()
        s = s[~s.index.duplicated(keep="last")]
        if s.empty or s.index[0] > calendar[0]:
            raise DataError(f"{isin}: no NAV on or before base date {calendar[0].date()}")
        full = s.reindex(s.index.union(calendar)).ffill()
        cols[isin] = full.reindex(calendar)
    return pd.DataFrame(cols, index=calendar)


def _exec_date(calendar: pd.DatetimeIndex, d: pd.Timestamp, lag: int) -> pd.Timestamp | None:
    pos = calendar.searchsorted(d)
    if pos + lag >= len(calendar):
        return None  # not yet executed (future)
    return calendar[pos + lag]


def simulate(decisions: list[Decision], nav: pd.DataFrame, instruments: dict[str, Instrument] | None = None,
             base_value: float = 100.0) -> pd.DataFrame:
    """Return a DataFrame indexed by date with columns: value, cash, and units_<ISIN>."""
    if not decisions:
        raise ValueError("no decisions")
    cal = nav.index
    first = decisions[0]
    t0 = cal[0]
    if pd.Timestamp(first.effective_date) != t0:
        raise ValueError(f"calendar must start at the initial decision date {first.effective_date}")
    isins = sorted({i for d in decisions for i in d.weights})
    missing = set(isins) - set(nav.columns)
    if missing:
        raise DataError(f"no NAV series for {sorted(missing)}")

    units = pd.DataFrame(0.0, index=cal, columns=isins)
    cash = pd.Series(0.0, index=cal)

    # Scheduled trades: date -> list of (isin, amount or "liquidate").
    trades: dict[pd.Timestamp, list[tuple[str, float | None]]] = {}
    pending = list(decisions[1:])

    u = {i: base_value * first.weights.get(i, 0.0) / 100 / nav.at[t0, i] for i in isins}
    c = 0.0
    for t in cal:
        # A new decision takes effect at the close of its effective date.
        while pending and pd.Timestamp(pending[0].effective_date) <= t:
            d = pending.pop(0)
            value_d = sum(u[i] * nav.at[t, i] for i in isins) + c
            for i in isins:
                target = value_d * d.weights.get(i, 0.0) / 100
                current = u[i] * nav.at[t, i]
                if abs(target - current) < 1e-12:
                    continue
                lag = instruments[i].trade_lag_days if instruments else 0
                if lag is None:
                    raise DataError(f"{i}: trade_lag_days not set; cannot apply decision {d.effective_date}")
                when = _exec_date(cal, t, lag)
                if when is None:
                    continue
                trades.setdefault(when, []).append((i, None if target == 0 else target - current))
        for i, amount in trades.pop(t, []):
            px = nav.at[t, i]
            if amount is None:  # full liquidation: sell every unit, no residual position
                c += u[i] * px
                u[i] = 0.0
            else:
                u[i] += amount / px
                c -= amount
        for i in isins:
            units.at[t, i] = u[i]
        cash.at[t] = c

    value = (units * nav[isins]).sum(axis=1) + cash
    out = units.add_prefix("units_")
    out.insert(0, "cash", cash)
    out.insert(0, "value", value)
    return out


def current_weights(sim: pd.DataFrame, nav: pd.DataFrame, on: pd.Timestamp | None = None) -> dict[str, float]:
    """Drifted weights (%) on a date (default: last date)."""
    t = on if on is not None else sim.index[-1]
    v = sim.at[t, "value"]
    return {c[6:]: 100 * sim.at[t, c] * nav.at[t, c[6:]] / v
            for c in sim.columns if c.startswith("units_") and sim.at[t, c] != 0}
