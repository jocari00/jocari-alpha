---
title: Methodology
---

## Portfolios and decisions

There are five model portfolios with a fixed share of equity: Defensive 0%, Conservative 25%,
Balanced 50%, Dynamic 75% and Aggressive 100%. Aggressive alternatives count as equity and
defensive alternatives as fixed income. The target weights of every portfolio are recorded in the
project's [public repository](https://github.com/jocari00/jocari-alpha/tree/main/decisions). Each
change is committed **before** it takes effect, so the dated history shows that decisions were
taken before the outcome was known.

## How returns are calculated

- **Time-weighted, in euros**, from each fund's net asset value (NAV). NAVs are already net of the
  funds' ongoing charges. Subscription or redemption fees and taxes are not included.
- **Static weights.** At every valuation date each portfolio is reset to its target weights, so the
  return of a period is the weighted average of its funds' returns over that period.
- **Valuation dates:** 31 December 2025 (base 100), 30 October 2026 and every month end after it.
  Each fund takes its last NAV published within 7 days of the date, which covers holidays and the
  weekly NAV of the cat-bond fund. If any fund of a portfolio has no NAV, the portfolio is not valued
  for that date: missing values are never estimated or filled in.
- **Returns are not annualised.** Risk metrics (volatility, drawdown, ratios) will be added once
  there are at least twelve months of live history.

## Estimated period and live tracking

The portfolios were formalised in October 2026. The period from 31 December 2025 to 30 October
2026 is an **estimate**: a single period calculated with the current target weights, shown as a
dashed line and labelled *Estimated*. It is not a live track record. Live tracking starts on
30 October 2026, with one valuation per month end.

## Benchmarks

Each portfolio is compared with a passive mix that has its same share of equity and fixed income,
built with accumulating ETFs whose price already reflects total return:

- Equity: iShares MSCI ACWI UCITS ETF (Acc), price in euros.
- Fixed income: 50% iShares € Govt Bond 1-3yr UCITS ETF (Acc) and 50% Vanguard EUR Corporate
  1-3 Year Bond UCITS ETF (Acc). The portfolios' fixed income is short duration, so a long-duration
  aggregate index would not be a fair comparison.

| Portfolio | MSCI ACWI | EUR Govt 1-3 | EUR Corp 1-3 |
|---|---|---|---|
| Defensive | 0% | 50% | 50% |
| Conservative | 25% | 37.5% | 37.5% |
| Balanced | 50% | 25% | 25% |
| Dynamic | 75% | 12.5% | 12.5% |
| Aggressive | 100% | 0% | 0% |

The benchmark weights are also reset at every valuation date.

## Data sources

NAVs and ETF prices are collected every week from the fund managers' publications and other
public sources, and cross-checked where possible. Only combined portfolio and benchmark returns
are published; the funds' own NAVs are not.

## Limitations

- The estimated period uses today's weights and is not a real track record.
- Funds and ETFs price at different times and some publish with a delay; the 7-day window aligns
  them to each valuation date, not to the same minute.
- Model portfolios are not real accounts: trading costs, minimum investments and taxes are ignored.
- The methodology is inspired by the GIPS® standards but the portfolios are not GIPS compliant.

Charts are built with [TradingView Lightweight Charts™](https://www.tradingview.com/).
