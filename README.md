# Jocari Alpha

*Model portfolios & market commentary.*

A static website with five model portfolios of investment funds (Defensive, Conservative,
Balanced, Dynamic, Aggressive), each tracked monthly against an ETF-based benchmark.

> Model portfolios for educational and illustrative purposes only. This is not investment
> advice or a personalised recommendation, and no third-party money is managed. Past
> performance does not guarantee future returns. Estimated data is labelled as such.

## Architecture

No database and no server. Decisions and code live in this repository; NAVs live in a
Google Drive sheet. Only combined portfolio and benchmark returns are published, never
the funds' own NAVs.

```
decisions/        One YAML per portfolio: target weights + effective dates (the decision log)
config/           instruments.yaml (ISIN, share class, block), blocks.yaml (block -> asset
                  class), tracking.yaml (base date, live start, constant weights, commentary)
src/jocari/       Python: construction rules, NAV validation, valuation engine, returns
tests/            pytest: construction rules and engine checks against hand-computed cases
```

Tracking model (`config/tracking.yaml`):

- Weights are static: every portfolio is reset to its target weights at each valuation date.
- 2025-12-31 (value 100) to 2026-10-30 is a single **estimated YTD** period.
- From the live start (2026-10-30) the portfolios are valued at every month end.
- A portfolio is valued only when every one of its funds has a NAV within 7 days of the
  date; missing NAVs are never filled in.

Flow:

1. **Routine 1, NAV collection** (weekly Claude routine): records each fund's and benchmark
   ETF's NAV in the Drive sheet *Jocari Portfolios – Retornos semanales*, tab "VL fondos",
   including the month-end NAV whenever a month closes.
2. **Routine 2, calculation** (weekly Claude routine, after routine 1): reads "VL fondos", runs
   this repository's engine for portfolios and benchmarks, writes the results back to the
   sheet and, when a month closes, commits the website's JSON here.
3. **Deployment** (GitHub Actions): runs the tests, builds the site and deploys to GitHub Pages.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
```

## Changing a portfolio's target weights

1. Append a new entry to `decisions/<portfolio>.yaml` with a future `effective_date`:

   ```yaml
     - effective_date: 2027-01-29
       kind: change
       note: Reason for the change.
       weights:
         LU0034353002: 20
         # ...every holding; omitted ISINs are sold
   ```

2. Run `.venv/bin/python -m jocari.cli check-decisions` (the same rules run in the tests).
3. Commit **before** the effective date. The commit timestamp is the proof that the decision
   was taken before the outcome was known.

## Adding a NAV by hand

If routine 1 could not find a NAV, add the row to the "VL fondos" tab of the Drive sheet
yourself, with the date, the NAV and the source you read it from. Routine 2 validates every
row (no future dates or weekends, no duplicates, no move above 5% for fixed income or 15% for
equity without confirmation) before using it.

## Adding a market commentary

*Coming in the website phase.*
