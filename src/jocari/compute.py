"""Portfolio and benchmark returns from the NAVs exported from the Drive sheet.

Input: a CSV export of the "VL fondos" tab (one row per instrument and date). Only the
ISIN, NAV date and NAV columns are used; headers are matched case-insensitively in
Spanish or English. Rows are validated per instrument in date order; a rejected row is
reported and left out.

Outputs:
- results (public, committed, read by the website): closed valuations only, combined
  portfolio and benchmark returns, never a fund's NAV. It only changes when a new
  valuation date closes, so an unchanged file means there is nothing to publish.
- report (private, for routine 2's message): provisional return since the last month
  end, portfolios that could not be valued, rejected rows.
- table: rows for the sheet tab "Carteras vs benchmark".
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from .config import ROOT, Decision, Portfolio, load_benchmark_instruments, load_instruments, load_portfolios
from .engine import MAX_GAP_DAYS, align, constant_weights
from .metrics import period_returns, ytd_return
from .validate import Observation, ValidationError, validate

ISIN_COLS = ("isin",)
DATE_COLS = ("fecha del vl", "fecha vl", "fecha_vl", "fecha", "nav date", "date")
NAV_COLS = ("vl", "nav", "valor liquidativo", "precio", "price")


@dataclass
class NavData:
    series: dict[str, pd.Series] = field(default_factory=dict)
    rejected: list[dict] = field(default_factory=list)


def _pick(header: list[str], names: tuple[str, ...]) -> int:
    low = [h.strip().lower() for h in header]
    for n in names:
        if n in low:
            return low.index(n)
    raise ValueError(f"no column named any of {names} in {header}")


def _number(s: str) -> float:
    s = s.strip().replace("€", "").replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    return float(s)


def _date(s: str) -> date:
    s = s.strip()
    if "/" in s:
        return datetime.strptime(s, "%d/%m/%Y").date()
    return date.fromisoformat(s[:10])


def read_nav_csv(path: Path, asset_class: dict[str, str], today: date) -> NavData:
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    header, body = rows[0], rows[1:]
    ci, cd, cn = _pick(header, ISIN_COLS), _pick(header, DATE_COLS), _pick(header, NAV_COLS)
    parsed: dict[str, dict[date, float]] = {}
    out = NavData()
    for r in body:
        if len(r) <= max(ci, cd, cn) or not r[ci].strip():
            continue
        isin = r[ci].strip().upper()
        if isin not in asset_class:
            continue
        try:
            d, v = _date(r[cd]), _number(r[cn])
        except ValueError:
            out.rejected.append({"isin": isin, "date": r[cd], "reason": "unreadable date or NAV"})
            continue
        prev = parsed.setdefault(isin, {}).get(d)
        if prev is not None and abs(prev - v) > 1e-9:
            out.rejected.append({"isin": isin, "date": d.isoformat(),
                                 "reason": "conflicting NAVs for the same date (kept the first)"})
            continue
        parsed[isin][d] = v  # the sheet repeats the same NAV under several references
    for isin, obs in parsed.items():
        hist = pd.Series(dtype=float)
        for d in sorted(obs):
            try:
                validate(Observation(isin, d, obs[d]), hist, asset_class[isin], today=today)
            except ValidationError as e:
                out.rejected.append({"isin": isin, "date": d.isoformat(), "reason": str(e)})
                continue
            hist = pd.concat([hist, pd.Series([obs[d]], index=[pd.Timestamp(d)])])
        out.series[isin] = hist
    return out


def valuation_dates(base: date, live_start: date, asof: date) -> list[date]:
    """Base, live start, then the end of every month after the live start's month, up to asof.

    The live start (2026-10-30) is October's last business day, so it closes October.
    """
    dates = [base, live_start]
    t = pd.Timestamp(live_start) + pd.offsets.MonthEnd(0) + pd.offsets.MonthEnd(1)
    while t.date() <= asof:
        dates.append(t.date())
        t += pd.offsets.MonthEnd(1)
    return [d for d in dates if d <= asof]


def _has_base(s: pd.Series, base: pd.Timestamp) -> bool:
    return not s[(s.index <= base) & (s.index > base - pd.Timedelta(days=MAX_GAP_DAYS + 1))].empty


def _value(decisions, isins, navs, dates):
    """Values on the run of dates from the base where every holding has a NAV.

    Returns (series or None, gaps); the series stops at the first date with a missing
    NAV, which is reported in gaps. Nothing is filled in.
    """
    idx = pd.DatetimeIndex([pd.Timestamp(d) for d in dates])
    cols = {}
    for i in isins:
        s = navs.get(i)
        cols[i] = (align({i: s}, idx)[i] if s is not None and _has_base(s, idx[0])
                   else pd.Series(float("nan"), index=idx))
    table = pd.DataFrame(cols, index=idx)
    ok, gaps = 0, []
    for t in idx:
        row = table.loc[t]
        if row.isna().any():
            gaps.append({"date": t.date().isoformat(), "isins": sorted(row[row.isna()].index)})
            break
        ok += 1
    if ok < 2:
        return None, gaps
    return constant_weights(decisions, table.iloc[:ok]), gaps


def _bench_decisions(p: Portfolio) -> list[Decision]:
    return [Decision(p.decisions[0].effective_date, "benchmark", {k: v for k, v in p.benchmark.items() if v > 0})]


def compute(nav_csv: Path, asof: date, root: Path = ROOT) -> tuple[dict, dict, list[list]]:
    tracking = yaml.safe_load(open(root / "config" / "tracking.yaml", encoding="utf-8"))
    base, live = tracking["base_date"], tracking["live_start"]
    funds = load_instruments(root)
    benches = load_benchmark_instruments(root)
    asset_class = {i: f.asset_class for i, f in funds.items()} | {i: b["sleeve"] for i, b in benches.items()}
    data = read_nav_csv(nav_csv, asset_class, today=asof)
    dates = valuation_dates(base, live, asof)

    doc = {"base_date": base.isoformat(), "live_start": live.isoformat(), "weights": "constant", "portfolios": {}}
    report = {"asof": asof.isoformat(), "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "portfolios": {}, "rejected_rows": data.rejected}
    table = [["Cartera", "Desde", "Hasta", "Tipo", "Cartera %", "Benchmark %", "Diferencia %",
              "YTD cartera %", "YTD benchmark %"]]

    for pid, p in load_portfolios(root).items():
        holdings = sorted({i for d in p.decisions for i in d.weights})
        bench_isins = sorted(k for k, v in p.benchmark.items() if v > 0)
        pv, pgaps = _value(p.decisions, holdings, data.series, dates)
        bv, bgaps = _value(_bench_decisions(p), bench_isins, data.series, dates)
        entry = {"name": p.name, "equity_target": p.equity_target,
                 "dates": [], "portfolio": [], "benchmark": [], "periods": []}
        rep = {"missing": {"portfolio": pgaps, "benchmark": bgaps}, "provisional": None}
        if pv is not None and bv is not None:
            common = pv.index.intersection(bv.index)
            pv, bv = pv.loc[common], bv.loc[common]
            entry["dates"] = [t.date().isoformat() for t in common]
            entry["portfolio"] = [round(x, 4) for x in pv]
            entry["benchmark"] = [round(x, 4) for x in bv]
            for (t, rp), rb in zip(period_returns(pv).items(), period_returns(bv)):
                start = common[common.get_loc(t) - 1]
                kind = "estimated" if t.date() <= live else "live"
                entry["periods"].append({"from": start.date().isoformat(), "to": t.date().isoformat(), "type": kind,
                                         "portfolio": round(rp, 6), "benchmark": round(rb, 6),
                                         "excess": round(rp - rb, 6)})
                table.append([p.name, start.date().isoformat(), t.date().isoformat(),
                              "estimado" if kind == "estimated" else "live",
                              f"{rp * 100:.2f}", f"{rb * 100:.2f}", f"{(rp - rb) * 100:.2f}",
                              f"{ytd_return(pv, t) * 100:.2f}", f"{ytd_return(bv, t) * 100:.2f}"])
            entry["ytd"] = {"portfolio": round(ytd_return(pv), 6), "benchmark": round(ytd_return(bv), 6)}
            rep["provisional"] = _provisional(p, data.series, pv, asof)
            if rep["provisional"]:
                pr = rep["provisional"]
                table.append([p.name, pr["since"], pr["date"], "provisional", f"{pr['portfolio'] * 100:.2f}",
                              f"{pr['benchmark'] * 100:.2f}", f"{pr['excess'] * 100:.2f}", "", ""])
        doc["portfolios"][pid] = entry
        report["portfolios"][pid] = rep
    return doc, report, table


def _provisional(p: Portfolio, navs, pv: pd.Series, asof: date) -> dict | None:
    """Return since the last valuation date up to asof (sheet only, never published)."""
    last = pv.index[-1]
    if last.date() >= asof:
        return None
    idx = pd.DatetimeIndex([last, pd.Timestamp(asof)])
    out = {"date": asof.isoformat(), "since": last.date().isoformat()}
    for key, decisions in (("portfolio", p.decisions), ("benchmark", _bench_decisions(p))):
        w = [d for d in decisions if pd.Timestamp(d.effective_date) <= last][-1].weights
        r = 0.0
        for i, wt in w.items():
            if i not in navs or navs[i].index[-1] <= last:
                return None  # no NAV newer than the last valuation: nothing provisional to show
            v = align({i: navs[i]}, idx)[i]
            if v.isna().any():
                return None
            r += wt / 100 * (v.iloc[1] / v.iloc[0] - 1)
        out[key] = round(r, 6)
    out["excess"] = round(out["portfolio"] - out["benchmark"], 6)
    return out


def _write_json(obj: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def write_outputs(doc: dict, report: dict, table: list[list], json_path: Path | None,
                  report_path: Path | None, table_path: Path | None) -> None:
    if json_path:
        _write_json(doc, json_path)
    if report_path:
        _write_json(report, report_path)
    if table_path:
        table_path.parent.mkdir(parents=True, exist_ok=True)
        with open(table_path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(table)
