"""Write the reconstructed month-end points (2025-12-31 .. 2026-09-30) to private-data/nav/.

Inputs (all in the private repository):
  reconstruction/factsheet_figures.yaml   figures extracted from official factsheets
  raw/*                                   daily NAV files published by three managers
  fx/ecb_eurusd.csv                       ECB euro reference rates (USD per EUR)

Run once; it refuses to overwrite existing CSVs.
"""
from __future__ import annotations

import re
import sys
from datetime import date

import pandas as pd
import yaml

from jocari.navstore import DATA_ROOT, Observation, append, nav_path
from jocari.reconstruct import from_cumulative, from_monthly, month_end, ytd_matches

BASE, LAST = date(2025, 12, 31), date(2026, 9, 30)
MONTH_ENDS = [month_end(2025, 12)] + [month_end(2026, m) for m in range(1, 10)]


def daily_points(isin: str) -> dict[date, float]:
    raw = DATA_ROOT / "raw"
    if isin == "ES0124037005":
        df = pd.read_excel(next(raw.glob(f"{isin}_*.xlsx")))
        s = pd.Series(df.iloc[:, 1].values, index=pd.to_datetime(df.iloc[:, 0], format="%Y/%m/%d"))
    elif isin == "ES0112611001":
        df = pd.read_excel(next(raw.glob(f"{isin}_*.xlsx")))
        s = pd.Series(df.iloc[:, 4].values, index=pd.to_datetime(df.iloc[:, 0]))
    elif isin == "ES0112618006":
        from pypdf import PdfReader
        text = "\n".join(p.extract_text() or "" for p in PdfReader(next(raw.glob(f"{isin}_*.pdf"))).pages)
        rows = re.findall(r"(\d\d/\d\d/20\d\d) (\d+,\d+)", text)
        s = pd.Series([float(v.replace(".", "").replace(",", ".")) for _, v in rows],
                      index=pd.to_datetime([d for d, _ in rows], dayfirst=True))
    else:
        raise KeyError(isin)
    s = s[~s.index.duplicated()].sort_index()
    s = s[s.index.day_of_week < 5]  # B&H also lists weekends with the previous value
    out = {}
    for e in MONTH_ENDS:
        prior = s[s.index <= pd.Timestamp(e)]
        out[prior.index[-1].date()] = float(prior.iloc[-1])
    return out


def ecb_rate(fx: pd.Series, d: date) -> float:
    return float(fx[fx.index <= pd.Timestamp(d)].iloc[-1])


def main() -> int:
    figures = yaml.safe_load(open(DATA_ROOT / "reconstruction" / "factsheet_figures.yaml", encoding="utf-8"))
    fx = pd.read_csv(DATA_ROOT / "fx" / "ecb_eurusd.csv", usecols=["TIME_PERIOD", "OBS_VALUE"])
    fx = pd.Series(fx["OBS_VALUE"].values, index=pd.to_datetime(fx["TIME_PERIOD"]))

    for isin, f in figures.items():
        if nav_path(isin).exists():
            print(f"{isin}: CSV exists, skipped")
            continue
        basis, note = "nav", "reconstructed"
        if f.get("daily_file"):
            pts = daily_points(isin)
            note = "reconstructed: month-end from manager's daily NAV file"
        else:
            a = f["anchor"]
            basis = a.get("basis", "nav")
            if "monthly" in f:
                if not ytd_matches(f["monthly"], f["ytd_check"], tol=0.06 if basis == "nav" else 0.15):
                    print(f"{isin}: monthly returns do not compound to stated YTD", file=sys.stderr)
                    return 1
                pts = from_monthly(a["date"], a["value"], f["monthly"])
                note = "reconstructed: backed out from factsheet monthly returns"
            else:
                pts = from_cumulative(a["date"], a["value"], f["cumulative"], f.get("one_month_start"))
                if "extra_anchor" in f:
                    x = f["extra_anchor"]
                    pts.update(from_cumulative(x["date"], x["value"], x["cumulative"]))
                note = "reconstructed: backed out from factsheet cumulative returns"
            if f.get("currency") == "USD":  # convert a USD index to EUR with ECB reference rates
                pts = {d: v / ecb_rate(fx, d) for d, v in pts.items()}
                base = pts[min(pts)]
                pts = {d: 100 * v / base for d, v in pts.items()}
                note += "; USD converted to EUR at ECB reference rate (Source: ECB statistics)"
            if f.get("provisional"):
                note += "; PROVISIONAL vendor sheet, replace with official factsheet"
        for d in sorted(pts):
            if not (BASE - pd.Timedelta(days=7).to_pytimedelta() <= d <= LAST):
                continue
            append(Observation(isin, d, round(pts[d], 6), f["doc"], note, basis))
        print(f"{isin}: {len(pts)} points ({basis})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
