"""Engine tests against cases computed by hand."""
from datetime import date

import pandas as pd
import pytest

from jocari.config import Decision, Instrument
from jocari.engine import DataError, align, current_weights, simulate

CAL = pd.DatetimeIndex(["2025-12-31", "2026-01-02", "2026-01-05", "2026-01-06"])


def _nav(**cols):
    return pd.DataFrame(cols, index=CAL[: len(next(iter(cols.values())))])


def test_buy_and_hold_drift():
    # A: 10 -> 11 -> 12 ; B: 20 -> 20 -> 18 ; 50/50 at base 100.
    # units A = 50/10 = 5, units B = 50/20 = 2.5
    # V: 100 ; 5*11 + 2.5*20 = 105 ; 5*12 + 2.5*18 = 105
    nav = _nav(A=[10.0, 11.0, 12.0], B=[20.0, 20.0, 18.0])
    sim = simulate([Decision(date(2025, 12, 31), "initial", {"A": 50, "B": 50})], nav)
    assert list(sim["value"]) == pytest.approx([100, 105, 105])
    w = current_weights(sim, nav)
    assert w["A"] == pytest.approx(60 / 105 * 100)
    assert w["B"] == pytest.approx(45 / 105 * 100)


def test_align_carries_forward_and_seeds_base():
    # Weekly fund: published 2025-12-29 and 2026-01-05 only.
    weekly = pd.Series([1.0, 1.1], index=pd.to_datetime(["2025-12-29", "2026-01-05"]))
    daily = pd.Series([5.0, 5.1, 5.2, 5.3], index=CAL)
    out = align({"W": weekly, "D": daily}, CAL)
    assert list(out["W"]) == [1.0, 1.0, 1.1, 1.1]
    assert list(out["D"]) == [5.0, 5.1, 5.2, 5.3]


def test_align_requires_base_nav():
    late = pd.Series([1.0], index=pd.to_datetime(["2026-01-02"]))
    with pytest.raises(DataError):
        align({"X": late}, CAL)


def _ins(lag):
    return {i: Instrument(i, i, "-", "b", "fixed_income", "daily", lag) for i in "AB"}


def test_rebalance_with_trade_lag():
    # Base 100 all in A at 10 (10 units). Decision on 2026-01-02: 50/50 A/B, lag 1 day.
    # On 01-02: A=12 -> V=120. Orders: A -60 (sell), B +60 (buy), both executed 01-05.
    # On 01-05: A=12, B=20 -> sell 5 units A, buy 3 units B. Units A=5, B=3, cash 0.
    # On 01-06: A=13, B=21 -> V = 65 + 63 = 128.
    nav = _nav(A=[10.0, 12.0, 12.0, 13.0], B=[20.0, 20.0, 20.0, 21.0])
    decisions = [Decision(date(2025, 12, 31), "initial", {"A": 100}),
                 Decision(date(2026, 1, 2), "rebalance", {"A": 50, "B": 50})]
    sim = simulate(decisions, nav, _ins(1))
    assert list(sim["value"]) == pytest.approx([100, 120, 120, 128])
    assert sim.at[CAL[3], "units_A"] == pytest.approx(5)
    assert sim.at[CAL[3], "units_B"] == pytest.approx(3)
    assert sim.at[CAL[3], "cash"] == pytest.approx(0)


def test_rebalance_cash_residual_when_prices_move_before_execution():
    # Decision 01-02 at V=120 (A=12). Sell A for 60 and buy B for 60, executed 01-05.
    # A moves to 15 by 01-05: selling 60 worth = 4 units -> A keeps 6 units (worth 90).
    # Buy B 60 at 20 = 3 units; cash 0. V(01-05) = 90 + 60 = 150.
    nav = _nav(A=[10.0, 12.0, 15.0, 15.0], B=[20.0, 20.0, 20.0, 20.0])
    decisions = [Decision(date(2025, 12, 31), "initial", {"A": 100}),
                 Decision(date(2026, 1, 2), "rebalance", {"A": 50, "B": 50})]
    sim = simulate(decisions, nav, _ins(1))
    assert sim.at[CAL[2], "value"] == pytest.approx(150)
    assert sim.at[CAL[2], "units_A"] == pytest.approx(6)


def test_full_liquidation_leaves_no_units():
    nav = _nav(A=[10.0, 12.0, 15.0, 15.0], B=[20.0, 20.0, 20.0, 20.0])
    decisions = [Decision(date(2025, 12, 31), "initial", {"A": 100}),
                 Decision(date(2026, 1, 2), "change", {"B": 100})]
    sim = simulate(decisions, nav, _ins(1))
    # Sell all 10 units A at 15 = 150 cash; buy B for 120 (sized at decision) -> cash 30.
    assert sim.at[CAL[2], "units_A"] == 0
    assert sim.at[CAL[2], "units_B"] == pytest.approx(6)
    assert sim.at[CAL[2], "cash"] == pytest.approx(30)
    assert sim.at[CAL[2], "value"] == pytest.approx(150)


def test_rebalance_requires_trade_lag():
    nav = _nav(A=[10.0, 12.0, 12.0, 13.0], B=[20.0, 20.0, 20.0, 21.0])
    decisions = [Decision(date(2025, 12, 31), "initial", {"A": 100}),
                 Decision(date(2026, 1, 2), "rebalance", {"A": 50, "B": 50})]
    with pytest.raises(DataError):
        simulate(decisions, nav, _ins(None))


def test_align_leaves_gaps_missing_instead_of_carrying_forward():
    ends = pd.DatetimeIndex(["2025-12-31", "2026-01-30", "2026-02-27", "2026-03-31"])
    s = pd.Series([10.0, 11.0], index=pd.to_datetime(["2025-12-31", "2026-03-27"]))  # Mar 27 within 7d of Mar 31
    out = align({"A": s}, ends)
    assert out["A"].iloc[0] == 10.0
    assert out["A"].iloc[1:3].isna().all()
    assert out["A"].iloc[3] == 11.0


def test_complete_dates_requires_every_holding():
    from jocari.engine import complete_dates
    ends = pd.DatetimeIndex(["2025-12-31", "2026-01-30", "2026-02-27"])
    nav = pd.DataFrame({"A": [1.0, 1.1, 1.2], "B": [2.0, float("nan"), 2.2]}, index=ends)
    assert list(complete_dates(nav, ["A", "B"])) == [ends[0], ends[2]]
    assert list(complete_dates(nav, ["A"])) == list(ends)


def test_constant_weights_resets_every_period():
    # A: 10 -> 11 -> 11 ; B: 20 -> 20 -> 22 ; 50/50 reset each period.
    # Period 1: 0.5*10% + 0.5*0% = 5%  -> 105
    # Period 2: 0.5*0% + 0.5*10% = 5%  -> 110.25 (buy and hold would give 110: 5.5*... see drift test)
    from jocari.engine import constant_weights
    nav = _nav(A=[10.0, 11.0, 11.0], B=[20.0, 20.0, 22.0])
    v = constant_weights([Decision(date(2025, 12, 31), "initial", {"A": 50, "B": 50})], nav)
    assert list(v) == pytest.approx([100, 105, 110.25])


def test_constant_weights_applies_new_decision_from_its_date():
    from jocari.engine import constant_weights
    nav = _nav(A=[10.0, 11.0, 12.1], B=[20.0, 20.0, 20.0])
    decisions = [Decision(date(2025, 12, 31), "initial", {"A": 100}),
                 Decision(date(2026, 1, 2), "change", {"B": 100})]
    v = constant_weights(decisions, nav)
    # Period 1 all in A (+10%), period 2 all in B (0%)
    assert list(v) == pytest.approx([100, 110, 110])


def test_constant_weights_refuses_missing_nav():
    from jocari.engine import constant_weights
    nav = _nav(A=[10.0, float("nan"), 11.0])
    with pytest.raises(DataError):
        constant_weights([Decision(date(2025, 12, 31), "initial", {"A": 100})], nav)
