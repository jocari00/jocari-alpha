from datetime import date

import pytest

from jocari.reconstruct import from_cumulative, from_monthly, ytd_matches


def test_from_monthly_backs_out_each_month_end():
    # Anchor 30/03 at 103.02; Mar +1%, Feb +2%, Jan 0% -> Feb end 102, Jan end 100, Dec end 100
    pts = from_monthly(date(2026, 3, 30), 103.02, [0.0, 2.0, 1.0])
    assert pts[date(2026, 2, 28)] == pytest.approx(102.0)
    assert pts[date(2026, 1, 31)] == pytest.approx(100.0)
    assert pts[date(2025, 12, 31)] == pytest.approx(100.0)
    assert list(pts)[-1] == date(2026, 3, 30)


def test_from_monthly_rejects_wrong_length():
    with pytest.raises(ValueError):
        from_monthly(date(2026, 9, 30), 100, [1.0] * 8)


def test_from_cumulative_periods():
    pts = from_cumulative(date(2026, 9, 30), 110.0, {"1m": 10.0, "3m": 0.0, "ytd": 10.0})
    assert pts[date(2026, 8, 31)] == pytest.approx(100.0)
    assert pts[date(2026, 6, 30)] == pytest.approx(110.0)
    assert pts[date(2025, 12, 31)] == pytest.approx(100.0)


def test_one_month_start_override():
    pts = from_cumulative(date(2026, 9, 30), 99.1, {"1m": -0.9}, one_month_start=date(2026, 8, 28))
    assert date(2026, 8, 28) in pts and date(2026, 8, 31) not in pts


def test_ytd_check():
    assert ytd_matches([1.36, 1.51, -0.28, 1.83, 0.74, -0.04, 1.06, 0.85, 0.18], 7.44)
    assert not ytd_matches([1.0, 1.0], 5.0)
