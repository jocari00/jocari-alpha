from datetime import date

import pandas as pd
import pytest

from jocari.navstore import Observation, ValidationError, append, read_nav, validate

HIST = pd.Series([100.0, 100.5], index=pd.to_datetime(["2026-10-26", "2026-10-27"]))
TODAY = date(2026, 10, 30)


def ok(d, nav, ac="fixed_income", **kw):
    validate(Observation("X", d, nav, "test"), HIST, ac, today=TODAY, **kw)


def test_accepts_normal_value():
    ok(date(2026, 10, 28), 100.6)


@pytest.mark.parametrize("d,nav,why", [
    (date(2026, 10, 31), 100.6, "future"),
    (date(2026, 10, 25), 100.6, "weekend"),
    (date(2026, 10, 27), 100.6, "duplicate"),
    (date(2026, 10, 23), 100.6, "before the last"),
    (date(2026, 10, 28), 0.0, "positive"),
    (date(2026, 10, 28), 104.0, "exceeds"),
])
def test_rejects(d, nav, why):
    with pytest.raises(ValidationError, match=why):
        ok(d, nav)


def test_equity_threshold_is_wider_and_jump_can_be_confirmed():
    ok(date(2026, 10, 28), 104.0, ac="equity")
    ok(date(2026, 10, 28), 104.0, confirm_jump=True)


def test_append_and_read_roundtrip(tmp_path):
    append(Observation("X", date(2026, 10, 27), 100.5, "manual", "from factsheet"), root=tmp_path)
    append(Observation("X", date(2026, 10, 28), 100.6, "manual"), root=tmp_path)
    s = read_nav("X", root=tmp_path)
    assert list(s) == [100.5, 100.6]
    assert s.index[-1] == pd.Timestamp("2026-10-28")
