# Research Notes: Mini Event Study

## Official contracts

- OpenDART disclosure search supports three-month windows without a corporation code,
  pagination up to 100 rows per page, exchange disclosure type `I001`, and receipt dates but
  not receipt times.
- OpenDART `document.xml` returns a ZIP containing the original disclosure XML. Real contract
  documents expose labelled rows for contract amount, recent revenue, and reported ratio.
- The Financial Services Commission stock-price service on the Public Data Portal exposes
  daily OHLCV, trading value, listed shares, and market capitalization. It is end-of-day data
  updated after the source business date despite some portal metadata saying “real-time”.
- The Public Data Portal requires a separate utilization permission and key. A missing key is
  a blocked live stage, not justification for an unofficial fallback.

Primary references:

- <https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019001>
- <https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019003>
- <https://www.data.go.kr/data/15094808/openapi.do>
- <https://www.data.go.kr/data/15094807/openapi.do>

## Preregistered pilot choices

- Target 40 events; caller may choose 30–50.
- Cohort: original KOSPI/KOSDAQ exact-title contract notices. Corrections, subsidiary notices,
  and autonomous disclosures remain audited but are excluded from the first homogeneous cohort.
- Search baseline: calendar days `[-14,-3]`; event attention: `[0,+2]` in one NAVER request.
- Return entry: first post-receipt trading-day open.
- Return endpoints: that day's close and 1, 3, 5 subsequent closes.
- Benchmark: same-market KOSPI/KOSDAQ index over identical dates when available.
- Analysis: completeness, medians, quartile summaries, and scatter-ready joined rows only.
- Attention groups: lower `< -0.5`, neutral `[-0.5, 0.5]`, and higher `> 0.5` on the
  preregistered log attention-excess scale; missing values remain a separate group.

## Interpretation limits

- The 40 events are recent and selected from one disclosure family; they are not representative
  of every firm or market regime.
- A receipt date is weaker than an exchange dissemination timestamp. Next-day entry is a
  conservative daily-data convention, not an execution claim.
- Search activity may react to price, media coverage, or unrelated news.
- NAVER ratios do not measure absolute query counts or sentiment.
- A market-subtracted return is not a full factor-model abnormal return.
- Descriptive differences in this pilot cannot establish predictive power or profitability.
