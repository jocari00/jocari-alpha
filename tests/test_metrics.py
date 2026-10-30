"""Metric tests against values computed by hand.

Series V = 100, 110, 99, 108.9 -> daily returns +10%, -10%, +10%.
  mean = 0.033333, sample std = sqrt(0.0266667 / 2) = 0.1154701
  volatility = 0.1154701 * sqrt(252) = 1.8330303
  Sharpe (rf=0) = 0.033333 / 0.1154701 * sqrt(252) = 4.5825757
  downside dev = sqrt((0 + 0.01 + 0) / 3) = 0.0577350
  Sortino = 0.033333 / 0.0577350 * sqrt(252) = 9.1651514
  max drawdown = 99 / 110 - 1 = -0.1
Benchmark B = 100, 105, 99.75, 104.7375 -> +5%, -5%, +5% (exactly half of V)
  beta = 2; active returns +5%, -5%, +5% -> TE = 0.0577350 * sqrt(252)
"""
import math

import pandas as pd
import pytest

from jocari import metrics as m

IDX = pd.DatetimeIndex(["2025-12-31", "2026-01-02", "2026-01-05", "2026-01-06"])
V = pd.Series([100, 110, 99, 108.9], index=IDX)
B = pd.Series([100, 105, 99.75, 104.7375], index=IDX)


def test_cumulative_and_drawdown():
    assert m.cumulative_return(V) == pytest.approx(0.089)
    assert m.max_drawdown(V) == pytest.approx(-0.1)
    assert list(m.drawdown(V)) == pytest.approx([0, 0, -0.1, -0.01])


def test_volatility_sharpe_sortino():
    r = m.daily_returns(V)
    assert m.volatility(r) == pytest.approx(1.8330303, rel=1e-6)
    assert m.sharpe(r) == pytest.approx(4.5825757, rel=1e-6)
    assert m.sortino(r) == pytest.approx(9.1651514, rel=1e-6)


def test_sharpe_with_risk_free():
    r = m.daily_returns(V)
    # A constant rf shifts the mean but not the std: (0.033333 - 0.001) / 0.1154701 * sqrt(252)
    assert m.sharpe(r, 0.001) == pytest.approx((1 / 30 - 0.001) / 0.1154701 * math.sqrt(252), rel=1e-6)


def test_beta_and_tracking_error():
    rp, rb = m.daily_returns(V), m.daily_returns(B)
    assert m.beta(rp, rb) == pytest.approx(2.0)
    # Active returns = +5%, -5%, +5%: sample std = 0.0577350
    assert m.tracking_error(rp, rb) == pytest.approx(0.0577350 * math.sqrt(252), rel=1e-6)


def test_monthly_table_and_ytd():
    idx = pd.DatetimeIndex(["2025-12-31", "2026-01-15", "2026-01-30", "2026-02-16", "2026-02-27"])
    v = pd.Series([100, 101, 102, 100, 99.96], index=idx)
    t = m.monthly_returns(v)
    assert t.loc[2026, 1] == pytest.approx(0.02)
    assert t.loc[2026, 2] == pytest.approx(-0.02)
    assert math.isnan(t.loc[2026, 3])
    assert 2025 not in t.index  # base month holds only the base value
    assert m.ytd_return(v) == pytest.approx(-0.0004)
    assert m.mtd_return(v) == pytest.approx(-0.02)


def test_summary_flags_short_period():
    s = m.summary(V, B)
    assert s["period_lt_1y"] is True
    assert s["excess_return"] == pytest.approx(0.089 - 0.047375)
