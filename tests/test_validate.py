from datetime import date

import pandas as pd
import pytest

from jocari.validate import Observation, ValidationError, validate

HIST = pd.Series([100.0, 100.5], index=pd.to_datetime(["2026-10-23", "2026-10-30"]))
TODAY = date(2026, 11, 8)


def ok(d, nav, ac="fixed_income", **kw):
    validate(Observation("X", d, nav), HIST, ac, today=TODAY, **kw)


def test_accepts_normal_value():
    ok(date(2026, 11, 6), 100.9)


@pytest.mark.parametrize("d,nav,why", [
    (date(2026, 11, 9), 100.6, "future"),
    (date(2026, 11, 7), 100.6, "weekend"),
    (date(2026, 10, 30), 100.6, "duplicate"),
    (date(2026, 10, 28), 100.6, "before the last"),
    (date(2026, 11, 6), 0.0, "positive"),
    (date(2026, 11, 6), 106.0, "exceeds"),
])
def test_rejects(d, nav, why):
    with pytest.raises(ValidationError, match=why):
        ok(d, nav)


def test_equity_threshold_is_wider_and_jump_can_be_confirmed():
    ok(date(2026, 11, 6), 110.0, ac="equity")
    ok(date(2026, 11, 6), 106.0, confirm_jump=True)
