import pandas as pd
import pytest

from jocari import metrics as m

IDX = pd.DatetimeIndex(["2025-12-31", "2026-10-30", "2026-11-30", "2026-12-31", "2027-01-29"])
V = pd.Series([100, 105, 103.95, 106.029, 107.08929], index=IDX)


def test_cumulative():
    assert m.cumulative_return(V) == pytest.approx(0.0708929)


def test_period_returns():
    # 100 -> 105 (+5%) -> 103.95 (-1%) -> 106.029 (+2%) -> 107.08929 (+1%)
    assert list(m.period_returns(V)) == pytest.approx([0.05, -0.01, 0.02, 0.01])
    assert m.period_returns(V).index[0] == IDX[1]


def test_ytd_resets_each_year():
    assert m.ytd_return(V, IDX[3]) == pytest.approx(0.06029)   # 2026: 100 -> 106.029
    assert m.ytd_return(V) == pytest.approx(0.01)              # 2027: 106.029 -> 107.08929
