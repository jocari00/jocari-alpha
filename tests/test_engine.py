"""Engine tests against cases computed by hand."""
from datetime import date

import pandas as pd
import pytest

from jocari.config import Decision
from jocari.engine import DataError, align, complete_dates, constant_weights

DATES = pd.DatetimeIndex(["2025-12-31", "2026-10-30", "2026-11-30"])


def _nav(**cols):
    return pd.DataFrame(cols, index=DATES[: len(next(iter(cols.values())))])


def test_align_takes_last_nav_within_window():
    # Fermat-style weekly NAV: 2025-12-29 is within 7 days of the base; 2026-10-26 of Oct 30.
    weekly = pd.Series([1.0, 1.1, 1.2], index=pd.to_datetime(["2025-12-29", "2026-10-26", "2026-11-30"]))
    out = align({"W": weekly}, DATES)
    assert list(out["W"]) == [1.0, 1.1, 1.2]


def test_align_leaves_gaps_missing_instead_of_carrying_forward():
    s = pd.Series([10.0, 11.0], index=pd.to_datetime(["2025-12-31", "2026-11-27"]))
    out = align({"A": s}, DATES)
    assert out["A"].iloc[0] == 10.0
    assert pd.isna(out["A"].iloc[1])        # nothing within 7 days of 2026-10-30
    assert out["A"].iloc[2] == 11.0          # 2026-11-27 is within 7 days of 2026-11-30


def test_align_requires_base_nav():
    late = pd.Series([1.0], index=pd.to_datetime(["2026-01-02"]))
    with pytest.raises(DataError):
        align({"X": late}, DATES)


def test_complete_dates_requires_every_holding():
    nav = pd.DataFrame({"A": [1.0, 1.1, 1.2], "B": [2.0, float("nan"), 2.2]}, index=DATES)
    assert list(complete_dates(nav, ["A", "B"])) == [DATES[0], DATES[2]]
    assert list(complete_dates(nav, ["A"])) == list(DATES)


def test_constant_weights_resets_every_period():
    # A: 10 -> 11 -> 11 ; B: 20 -> 20 -> 22 ; 50/50 reset each period.
    # Period 1: 0.5*10% + 0.5*0% = 5%  -> 105
    # Period 2: 0.5*0% + 0.5*10% = 5%  -> 110.25 (buy and hold would give 110)
    nav = _nav(A=[10.0, 11.0, 11.0], B=[20.0, 20.0, 22.0])
    v = constant_weights([Decision(date(2025, 12, 31), "initial", {"A": 50, "B": 50})], nav)
    assert list(v) == pytest.approx([100, 105, 110.25])


def test_constant_weights_applies_new_decision_from_its_date():
    nav = _nav(A=[10.0, 11.0, 12.1], B=[20.0, 20.0, 20.0])
    decisions = [Decision(date(2025, 12, 31), "initial", {"A": 100}),
                 Decision(date(2026, 10, 30), "change", {"B": 100})]
    v = constant_weights(decisions, nav)
    # Period 1 all in A (+10%), period 2 all in B (0%)
    assert list(v) == pytest.approx([100, 110, 110])


def test_constant_weights_refuses_missing_nav():
    nav = _nav(A=[10.0, float("nan"), 11.0])
    with pytest.raises(DataError):
        constant_weights([Decision(date(2025, 12, 31), "initial", {"A": 100})], nav)


def test_constant_weights_requires_base_at_initial_decision():
    nav = _nav(A=[10.0, 11.0, 12.0])
    with pytest.raises(ValueError):
        constant_weights([Decision(date(2026, 1, 2), "initial", {"A": 100})], nav)
