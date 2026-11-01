"""compute() on a synthetic export of the Drive "VL fondos" tab, checked by hand."""
import csv
import json
from datetime import date

import pytest

from jocari.cli import main
from jocari.compute import compute, valuation_dates
from jocari.config import load_benchmark_instruments, load_instruments

FUNDS = list(load_instruments())
ETFS = list(load_benchmark_instruments())
DWS, ACWI, GOVT, CORP = "LU0034353002", "IE00B6R52259", "IE00B3VTMJ91", "IE00BH04FZ00"


def _write(tmp_path, rows):
    p = tmp_path / "vl.csv"
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Semana", "Nombre", "ISIN", "Clase", "Referencia", "Fecha del VL", "VL", "Fuente", "Observaciones"])
        for isin, d, v, ref in rows:
            w.writerow(["", "", isin, "", ref, d, v, "test", ""])
    return p


def _base_rows(oct_values=None):
    oct_values = oct_values or {}
    rows = []
    for i in FUNDS + ETFS:
        rows.append((i, "31/12/2025", "100,00", "cierre año"))
        rows.append((i, "30/10/2026", oct_values.get(i, "100,00"), "cierre semana"))
        rows.append((i, "30/10/2026", oct_values.get(i, "100,00"), "cierre mes"))  # same NAV, other reference
    return rows


def test_valuation_dates():
    assert valuation_dates(date(2025, 12, 31), date(2026, 10, 30), date(2027, 1, 5)) == [
        date(2025, 12, 31), date(2026, 10, 30), date(2026, 11, 30), date(2026, 12, 31)]


def test_estimated_ytd_by_hand(tmp_path):
    # DWS +10%, every other fund flat. Defensive holds 20% DWS -> +2%; Conservative 10% -> +1%.
    # Benchmark: Govt +2%, Corp +4%, ACWI +8%.
    #   Defensive 50/50 -> +3%; Conservative 25/37.5/37.5 -> 2% + 0.75% + 1.5% = +4.25%
    path = _write(tmp_path, _base_rows({DWS: "110,00", GOVT: "102", CORP: "104", ACWI: "108"}))
    doc, report, table = compute(path, date(2026, 11, 1))
    d, c = doc["portfolios"]["defensive"], doc["portfolios"]["conservative"]
    assert d["periods"][0]["type"] == "estimated"
    assert d["periods"][0]["portfolio"] == pytest.approx(0.02)
    assert d["periods"][0]["benchmark"] == pytest.approx(0.03)
    assert c["periods"][0]["portfolio"] == pytest.approx(0.01)
    assert c["periods"][0]["benchmark"] == pytest.approx(0.0425)
    assert d["dates"] == ["2025-12-31", "2026-10-30"]
    assert report["rejected_rows"] == []
    assert table[0][0] == "Cartera" and len(table) == 1 + 5


def test_live_month_is_marked_live_and_constant_weights(tmp_path):
    rows = _base_rows({DWS: "110,00"}) + [(i, "30/11/2026", "113,30" if i == DWS else "100,00", "cierre mes")
                                          for i in FUNDS + ETFS]
    doc, report, _ = compute(_write(tmp_path, rows), date(2026, 12, 2))
    d = doc["portfolios"]["defensive"]
    assert [x["type"] for x in d["periods"]] == ["estimated", "live"]
    # November: DWS 110 -> 113.3 (+3%), reset to 20% -> +0.6%. Value 102 -> 102.612
    assert d["periods"][1]["portfolio"] == pytest.approx(0.006)
    assert d["portfolio"][-1] == pytest.approx(102.612)


def test_missing_fund_stops_the_portfolio_but_not_others(tmp_path):
    rows = [r for r in _base_rows() if not (r[0] == "LU1213836080" and r[1] == "30/10/2026")]  # Fidelity Tech
    doc, report, _ = compute(_write(tmp_path, rows), date(2026, 11, 1))
    assert doc["portfolios"]["aggressive"]["periods"] == []
    assert report["portfolios"]["aggressive"]["missing"]["portfolio"] == [{"date": "2026-10-30", "isins": ["LU1213836080"]}]
    assert len(doc["portfolios"]["dynamic"]["periods"]) == 1


def test_anomalous_move_is_rejected(tmp_path):
    rows = _base_rows() + [(DWS, "06/11/2026", "110", "cierre semana")]  # +10% in a week, fixed income
    doc, report, _ = compute(_write(tmp_path, rows), date(2026, 11, 8))
    assert any(r["isin"] == DWS and "exceeds" in r["reason"] for r in report["rejected_rows"])


def test_bad_rows_are_rejected_and_reported(tmp_path):
    rows = _base_rows() + [(DWS, "01/11/2026", "100", "error: domingo"),
                           (GOVT, "30/10/2026", "99", "conflicto")]
    doc, report, _ = compute(_write(tmp_path, rows), date(2026, 11, 2))
    reasons = {(r["isin"], r["reason"].split(":")[0]) for r in report["rejected_rows"]}
    assert (DWS, DWS) in reasons                                # weekend
    assert any(r["isin"] == GOVT and "conflicting" in r["reason"] for r in report["rejected_rows"])
    assert len(doc["portfolios"]["defensive"]["periods"]) == 1  # still valued from the good rows


def test_provisional_since_last_valuation(tmp_path):
    rows = _base_rows() + [(i, "06/11/2026", "103" if i == DWS else "100", "cierre semana") for i in FUNDS + ETFS]
    doc, report, _ = compute(_write(tmp_path, rows), date(2026, 11, 8))
    prov = report["portfolios"]["defensive"]["provisional"]
    assert prov["since"] == "2026-10-30" and prov["portfolio"] == pytest.approx(0.006)  # 20% x 3%


def test_public_results_never_contain_fund_navs(tmp_path):
    out = tmp_path / "r.json"
    rows = _base_rows({DWS: "123,456"}) + [(GOVT, "30/10/2026", "98,765", "conflicto")]
    assert main(["compute", "--nav", str(_write(tmp_path, rows)), "--asof", "2026-11-01", "--json", str(out),
                 "--report", str(tmp_path / "rep.json"), "--table", str(tmp_path / "t.csv")]) == 0
    for f in (out, tmp_path / "rep.json"):
        text = f.read_text()
        assert "123.456" not in text and "98.765" not in text
    assert set(json.loads(out.read_text())["portfolios"]) == {"defensive", "conservative", "balanced", "dynamic",
                                                              "aggressive"}


def test_public_results_only_change_when_a_valuation_closes(tmp_path):
    out = tmp_path / "r.json"
    rows = _base_rows()
    main(["compute", "--nav", str(_write(tmp_path, rows)), "--asof", "2026-11-01", "--json", str(out)])
    first = out.read_text()
    rows += [(i, "06/11/2026", "100,50", "cierre semana") for i in FUNDS + ETFS]  # a week later, same month
    main(["compute", "--nav", str(_write(tmp_path, rows)), "--asof", "2026-11-08", "--json", str(out)])
    assert out.read_text() == first


def test_not_found_rows_are_skipped_quietly(tmp_path):
    # The routine records "NOT FOUND" rows with no date and no NAV; they are not errors.
    rows = _base_rows() + [(DWS, "", "", "(d) Cierre 2025"), (GOVT, "—", "", "(c) Cierre mes anterior")]
    _, report, _ = compute(_write(tmp_path, rows), date(2026, 11, 2))
    assert report["rejected_rows"] == []


def test_header_with_unit_in_brackets():
    from jocari.compute import _pick
    assert _pick(["ISIN", "Fecha VL", "VL (EUR)"], ("vl", "nav")) == 2
