"""The committed decisions in /decisions must satisfy every construction rule."""
import warnings

import pytest

from jocari.config import PORTFOLIOS, load_instruments, load_portfolios
from jocari.rules import FERMAT_ISIN, FERMAT_MAX_WEIGHT, check_portfolio, is_half_multiple, round_half

INSTRUMENTS = load_instruments()
PORTS = load_portfolios()


def test_all_five_portfolios_exist():
    assert set(PORTS) == set(PORTFOLIOS)


@pytest.mark.parametrize("pid", PORTFOLIOS)
def test_portfolio_rules(pid):
    errors, warns = check_portfolio(PORTS[pid], INSTRUMENTS)
    assert errors == []
    for w in warns:
        warnings.warn(w)


@pytest.mark.parametrize("pid", PORTFOLIOS)
def test_sums_to_100_and_half_multiples(pid):
    for d in PORTS[pid].decisions:
        assert sum(d.weights.values()) == pytest.approx(100)
        assert all(is_half_multiple(w) for w in d.weights.values())


def test_fermat_not_above_limit():
    """Cat bonds carry event risk: warn (do not fail) if any portfolio holds more than 5%."""
    for p in PORTS.values():
        w = p.current.weights.get(FERMAT_ISIN, 0)
        if w > FERMAT_MAX_WEIGHT:
            warnings.warn(f"{p.id}: Fermat cat bonds at {w}% (> {FERMAT_MAX_WEIGHT}%)")


def test_gamma_global_counts_as_fixed_income():
    assert INSTRUMENTS["ES0140794001"].asset_class == "fixed_income"


def test_round_half_ties_up():
    assert round_half(3.75) == 4.0
    assert round_half(6.25) == 6.5
    assert round_half(3.125) == 3.0
    assert round_half(1.25) == 1.5
    assert round_half(11.25) == 11.5
    assert round_half(9.375) == 9.5
