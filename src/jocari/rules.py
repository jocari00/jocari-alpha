"""Portfolio construction rules (section 7 of the project brief).

check_portfolio() returns a list of rule violations (empty = OK) and a list of
non-blocking warnings (e.g. cat-bond concentration).
"""
from __future__ import annotations

from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from .config import Instrument, Portfolio

FERMAT_ISIN = "IE000N9XFSD0"
FERMAT_MAX_WEIGHT = 5.0

# Share of the equity sleeve (incl. aggressive alternatives) per block, per fund.
EQUITY_SPLIT = {"equity_value": 12.5, "equity_emerging": 15.0, "aggressive_alternatives": 5.0}
EQUITY_SPLIT_AGGRESSIVE_EXTRA = {"equity_technology": 10.0}
DEFENSIVE_ALT_SHARE = 5.0  # % of the fixed-income sleeve, per defensive alternative


def round_half(x: float | Decimal) -> float:
    """Round to the nearest multiple of 0.5; ties round up (3.75 -> 4.0, 6.25 -> 6.5)."""
    d = Decimal(str(x)) * 2
    return float(d.quantize(Decimal("1"), rounding=ROUND_HALF_UP) / 2)


def is_half_multiple(x: float) -> bool:
    return (Decimal(str(x)) * 2) % 1 == 0


def check_weights(weights: dict[str, float], p: Portfolio, instruments: dict[str, Instrument]
                  ) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    unknown = set(weights) - set(instruments)
    if unknown:
        errors.append(f"unknown ISINs: {sorted(unknown)}")
        return errors, warnings

    total = sum(Decimal(str(w)) for w in weights.values())
    if total != 100:
        errors.append(f"weights sum to {total}, not 100")

    for isin, w in weights.items():
        if w <= 0:
            errors.append(f"{isin}: non-positive weight {w}")
        if not is_half_multiple(w):
            errors.append(f"{isin}: weight {w} is not a multiple of 0.5")

    by_block: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for isin, w in weights.items():
        by_block[instruments[isin].block].append((isin, w))
    eq = sum(w for i, w in weights.items() if instruments[i].asset_class == "equity")
    fi = sum(w for i, w in weights.items() if instruments[i].asset_class == "fixed_income")

    if eq != p.equity_target:
        errors.append(f"equity sleeve is {eq}, target {p.equity_target}")
    if fi != p.fixed_income_target:
        errors.append(f"fixed-income sleeve is {fi}, target {p.fixed_income_target}")

    def in_block(block: str) -> set[str]:
        return {i for i, ins in instruments.items() if ins.block == block}

    # Rule 1: fixed income -> all defensive alternatives; equity -> all aggressive alternatives.
    if fi > 0 and not in_block("defensive_alternatives") <= set(weights):
        errors.append("portfolio has fixed income but is missing defensive alternatives")
    if eq > 0 and not in_block("aggressive_alternatives") <= set(weights):
        errors.append("portfolio has equity but is missing aggressive alternatives")

    # Rule 2: no equity / aggressive alternatives when the equity target is 0.
    if p.equity_target == 0 and eq > 0:
        errors.append("0% equity profile holds equity or aggressive alternatives")

    # Rule 3: each defensive alternative = 5% of the fixed-income sleeve.
    if fi > 0:
        expected = round_half(fi * DEFENSIVE_ALT_SHARE / 100)
        for isin, w in by_block["defensive_alternatives"]:
            if w != expected:
                errors.append(f"{isin}: defensive alternative weight {w}, expected {expected}")

    # Rules 4 and 6: equity split; the index fund absorbs the rounding residual.
    if eq > 0:
        split = dict(EQUITY_SPLIT)
        if p.equity_target == 100:
            split.update(EQUITY_SPLIT_AGGRESSIVE_EXTRA)
        elif by_block["equity_technology"]:
            errors.append("technology fund is only allowed in the 100% equity profile")
        non_index = 0.0
        for block, share in split.items():
            expected = round_half(eq * share / 100)
            funds = by_block[block]
            if not funds:
                errors.append(f"missing block {block}")
            for isin, w in funds:
                non_index += w
                if w != expected:
                    errors.append(f"{isin}: {block} weight {w}, expected {expected}")
        index = sum(w for _, w in by_block["equity_index"])
        if index != eq - non_index:
            errors.append(f"index fund weight {index}, expected residual {eq - non_index}")

    # Technical note: cat-bond event risk.
    if weights.get(FERMAT_ISIN, 0) > FERMAT_MAX_WEIGHT:
        warnings.append(f"Fermat cat bonds weight {weights[FERMAT_ISIN]}% exceeds {FERMAT_MAX_WEIGHT}%")

    return errors, warnings


def check_benchmark(p: Portfolio) -> list[str]:
    errors = []
    b = p.benchmark
    if sum(Decimal(str(v)) for v in b.values()) != 100:
        errors.append(f"benchmark weights sum to {sum(b.values())}")
    if b.get("IE00B6R52259", 0) != p.equity_target:
        errors.append("benchmark equity weight does not match the profile")
    return errors


def check_portfolio(p: Portfolio, instruments: dict[str, Instrument]) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for d in p.decisions:
        e, w = check_weights(d.weights, p, instruments)
        errors += [f"{p.id} {d.effective_date}: {m}" for m in e]
        warnings += [f"{p.id} {d.effective_date}: {m}" for m in w]
    errors += [f"{p.id} benchmark: {m}" for m in check_benchmark(p)]
    return errors, warnings
