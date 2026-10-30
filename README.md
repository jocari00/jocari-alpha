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

## Computing returns from the Drive export

Routine 2 exports the "VL fondos" tab as CSV and runs:

```bash
.venv/bin/python -m jocari.cli compute --nav vl_fondos.csv --asof 2026-11-01 \
    --json data/results.json --table carteras_vs_benchmark.csv
```

- `data/results.json` (committed, read by the website): for each portfolio and its benchmark,
  the values at each valuation date and each period's return, marked `estimated` (to the live
  start) or `live`. It contains combined returns only, never a fund's NAV.
- The CSV table goes into the sheet tab "Carteras vs benchmark".
- A `provisional` return since the last month end is included for the sheet; the site ignores it.
- Rows that fail validation and portfolios that could not be valued are listed in the output.

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

## Website

Astro static site in `site/`, deployed to GitHub Pages by `.github/workflows/pages.yml` on every
push that touches the site, the results or the portfolio definitions. It reads `decisions/`,
`config/` and `data/results.json` at build time; until the first results exist it shows clearly
labelled sample data.

```bash
cd site && npm ci && npm run dev      # local preview
```

To move to a custom domain later, build with `SITE_URL=https://jocari.net BASE_PATH=/`.

## Editing the site's text

Everything editorial is Markdown in `site/content/`, one file per language:

- `editorial/en.md` / `es.md`: one paragraph per portfolio, per block and (optionally) per fund.
  Leave a value empty to show "Commentary coming soon".
- `pages/{methodology,about,legal}.{en,es}.md`: the text pages. Put your LinkedIn URL in the
  `linkedin` field of `about.*.md`.
- `commentary/{en,es}/<period>.md`: market commentary. Copy `commentary/_template.md` (English) or
  `commentary/_template.es.md` (Spanish); both lay out the sections (one line, macro, fixed income,
  equity, alternatives, the portfolios, what we are watching). Name the file by
  the period it covers (`2026-11.md` for a month, `2026-q1.md` for a quarter) and set `written` to
  the real date you wrote it. Monthly commentaries get the period's returns block automatically.
  If a commentary exists in only one language, the other language shows it with a notice.
