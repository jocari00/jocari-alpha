"""Load instruments, blocks and portfolio decisions from the repo."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PORTFOLIOS = ("defensive", "conservative", "balanced", "dynamic", "aggressive")


@dataclass(frozen=True)
class Instrument:
    isin: str
    name: str
    share_class: str
    block: str
    asset_class: str


@dataclass(frozen=True)
class Decision:
    effective_date: date
    kind: str
    weights: dict[str, float]
    note: str = ""


@dataclass
class Portfolio:
    id: str
    name: str
    equity_target: float
    fixed_income_target: float
    benchmark: dict[str, float]
    decisions: list[Decision] = field(default_factory=list)

    @property
    def current(self) -> Decision:
        return self.decisions[-1]


def _read(path: Path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_blocks(root: Path = ROOT) -> dict[str, dict]:
    return _read(root / "config" / "blocks.yaml")


def load_instruments(root: Path = ROOT) -> dict[str, Instrument]:
    blocks = load_blocks(root)
    raw = _read(root / "config" / "instruments.yaml")
    out = {}
    for f in raw["funds"]:
        out[f["isin"]] = Instrument(
            isin=f["isin"], name=f["name"], share_class=f["share_class"], block=f["block"],
            asset_class=blocks[f["block"]]["asset_class"],
        )
    return out


def load_benchmark_instruments(root: Path = ROOT) -> dict[str, dict]:
    return {b["isin"]: b for b in _read(root / "config" / "instruments.yaml")["benchmarks"]}


def _portfolio(raw: dict) -> Portfolio:
    decisions = [
        Decision(
            effective_date=d["effective_date"], kind=d.get("kind", "change"),
            weights={k: float(v) for k, v in d["weights"].items()}, note=d.get("note", ""),
        )
        for d in raw["decisions"]
    ]
    decisions.sort(key=lambda d: d.effective_date)
    return Portfolio(
        id=raw["portfolio"], name=raw["name"],
        equity_target=float(raw["equity_target"]),
        fixed_income_target=float(raw["fixed_income_target"]),
        benchmark={k: float(v) for k, v in raw["benchmark"].items()},
        decisions=decisions,
    )


def load_portfolio(pid: str, root: Path = ROOT) -> Portfolio:
    return _portfolio(_read(root / "decisions" / f"{pid}.yaml"))


def load_portfolios(root: Path = ROOT) -> dict[str, Portfolio]:
    return {p: load_portfolio(p, root) for p in PORTFOLIOS}


@dataclass
class Personal:
    portfolio: Portfolio
    start_date: date
    extra_funds: dict[str, dict]  # ISIN -> entry; funds outside config/instruments.yaml


def load_personal(root: Path = ROOT) -> Personal | None:
    """My own portfolio (personal/jordi.yaml), shown only on the About page."""
    path = root / "personal" / "jordi.yaml"
    if not path.exists():
        return None
    raw = _read(path)
    return Personal(portfolio=_portfolio(raw), start_date=raw["start_date"],
                    extra_funds={f["isin"]: f for f in raw.get("extra_funds", [])})
