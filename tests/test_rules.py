"""The rule checker must reject portfolios that break the rules."""
import copy

from jocari.config import load_instruments, load_portfolio
from jocari.rules import check_weights

INSTRUMENTS = load_instruments()


def _check(pid, mutate):
    p = load_portfolio(pid)
    w = copy.deepcopy(p.current.weights)
    mutate(w)
    return check_weights(w, p, INSTRUMENTS)


def test_valid_portfolio_passes():
    assert _check("balanced", lambda w: None) == ([], [])


def test_sum_not_100_fails():
    errors, _ = _check("balanced", lambda w: w.update({"LU1623762843": 6.5}))
    assert any("sum" in e for e in errors)


def test_non_half_multiple_fails():
    def m(w):
        w["LU1623762843"] = 6.25
        w["IE000VA5W9H0"] = 7.75
    errors, _ = _check("balanced", m)
    assert any("multiple of 0.5" in e for e in errors)


def test_equity_in_defensive_fails():
    def m(w):
        w["LU0034353002"] -= 5
        w["IE00BYX5NX33"] = 5
    errors, _ = _check("defensive", m)
    assert any("equity" in e for e in errors)


def test_missing_defensive_alternative_fails():
    def m(w):
        w["LU0034353002"] += w.pop("LU1112771503")
    errors, _ = _check("conservative", m)
    assert any("defensive alternatives" in e for e in errors)


def test_wrong_equity_split_fails():
    def m(w):
        w["ES0124037005"] += 1
        w["IE00BYX5NX33"] -= 1
    errors, _ = _check("dynamic", m)
    assert any("equity_value" in e for e in errors)


def test_technology_outside_aggressive_fails():
    def m(w):
        w["IE00BYX5NX33"] -= 1
        w["LU1213836080"] = 1
    errors, _ = _check("dynamic", m)
    assert any("technology" in e for e in errors)


def test_fermat_above_5_warns():
    def m(w):
        w["IE000N9XFSD0"] += 1
        w["LU0034353002"] -= 1
    _, warns = _check("defensive", m)
    assert any("Fermat" in x for x in warns)
