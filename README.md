# Jocari Alpha

*Model portfolios & market commentary.*

A static website with five model portfolios of investment funds (Defensive, Conservative,
Balanced, Dynamic, Aggressive), each tracked monthly against an ETF-based benchmark.

> Model portfolios for educational and illustrative purposes only. This is not investment
> advice or a personalised recommendation, and no third-party money is managed. Past
> performance does not guarantee future returns. Reconstructed data is labelled as such.

## Architecture

No database and no server. Everything lives in this repository, and every change is a dated commit.

```
decisions/        One YAML per portfolio: target weights + effective dates (the decision log)
config/           Instrument master (ISIN, share class, block) and block -> asset class map
data/factsheets/  Factsheets downloaded by hand (gitignored: manager copyright)
private-data/     Separate PRIVATE repo: nav/ (one CSV per ISIN, with source), log/ (ingestion
                  failures; a failed source never produces an invented value), raw/, fx/
src/jocari/       Python: rules, NAV store and validation, simulation engine, metrics
tests/            pytest: construction rules and engine checks against hand-computed cases
```

Tracking model (`config/tracking.yaml`): weights are held constant (reset to target at every
valuation date). The period from 2025-12-31 to the live start (2026-10-30) is shown as a single
**estimated YTD** segment; from then on the portfolios are valued at every month end.

Raw NAVs are third-party data and live in `private-data/`, a separate private repository.
Only combined portfolio and benchmark returns are published.

Monthly flow:

1. **NAV collection** (scheduled Claude routine): reads each month-end NAV following the source
   chain in `config/sources.yaml`, validates it, appends it to `private-data/nav/<ISIN>.csv`
   and commits to the private repository.
2. **Calculation and deployment** (GitHub Actions): runs the tests, computes the portfolios
   and metrics, writes the JSON consumed by the website and deploys to GitHub Pages.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
```

## Adding a decision (rebalance or weight change)

1. Append a new entry to `decisions/<portfolio>.yaml` with a future `effective_date`:

   ```yaml
     - effective_date: 2027-01-04
       kind: rebalance
       note: Annual rebalance to target weights.
       weights:
         LU0034353002: 20
         # ...every holding; omitted ISINs are sold
   ```

2. Run `.venv/bin/python -m jocari.cli check-decisions` (the same rules run in the tests).
3. Commit **before** the effective date. The commit timestamp is the proof that the decision
   was taken before the outcome was known.

Every fund being traded needs `trade_lag_days` set in `config/instruments.yaml`. The engine
refuses to apply a decision while that value is missing.

## Adding a NAV by hand

Use this route when a source is down or publishes late. The value goes through the same
validation as the automated routine.

```bash
.venv/bin/python -m jocari.cli add-nav LU0034353002 2026-10-29 92.95 \
    --source "https://<official-page-or-document>" --note "entered by hand: routine source down"
```

- `--source` is required: give the URL or document the value was read from, or `manual`.
- The command rejects future dates, weekends, duplicates, dates before the last stored
  date and moves above the anomaly threshold (3% fixed income, 8% equity). If a large move is
  real, check it against a second source and re-run with `--confirm-jump`.
- Commit the change with a message such as `nav: LU0034353002 2026-10-29 (manual, source down)`.

Never edit past rows silently. If a stored value is wrong, correct it in its own commit and
explain the reason in the message.

## Adding a market commentary

*Coming in the website phase.*
