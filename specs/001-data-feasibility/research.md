# Research Notes: Data Feasibility and Hypothesis Discipline

## Hypothesis family

The motivating claim is split before data is inspected:

- **H1 — Euphoria continuation**: unusually positive crowd excess predicts a short
  continuation before decay.
- **H2 — Euphoria reversal**: unusually positive crowd excess predicts negative future
  abnormal return after the event-day move.
- **H3 — Panic rebound**: unusually negative crowd excess predicts a rebound.
- **H4 — Disagreement volatility**: unusual disagreement predicts absolute return or
  volume rather than direction.

None is privileged by the implementation. Future-return horizons and transaction-cost
assumptions must be preregistered before the first full-sample analysis.

## Source decisions

### OpenDART — supported with credential

The official disclosure search endpoint returns receipt metadata and structured status
codes. The no-company query window is capped at three months. Supply-contract reports are
discovered by official metadata first; extracting numeric fields from source documents is
a later, separately tested parser task.

Primary reference:
<https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019001>

### KRX — official manual export in this milestone

KRX Data Marketplace exposes stock prices and investor-type trading statistics. The spike
uses files exported by the user and never reverse-engineers a private web endpoint.

Primary reference: <https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd>

### Naver user posts — automated collection blocked

Naver's terms prohibit automated collection of user IDs and posts without prior consent.
The project therefore provides no Naver Finance board collector.

Primary reference: <https://policy.naver.com/rules/service_pre_20250710.html>

### NAVER Search Trend — supported attention proxy

The current NAVER API HUB returns relative search ratios. It measures attention, not
opinion or sentiment, and the maximum value inside the requested comparison is normalized
to 100. Ratios from separately requested windows are not directly comparable without an
anchor query strategy.

Primary reference: <https://api.ncloud-docs.com/docs/naver-api-hub-search-trend>

## First event family

`SINGLE_SALES_SUPPLY_CONTRACT` is selected because contract amount divided by recent
annual revenue is a visible, comparable starting denominator. It still does not equal a
fundamental valuation surprise: margins, contract duration, prior expectations,
counterparty quality, cancellation clauses, and duplicate announcements remain potential
confounders.

## Identification risks

- Reverse causality: posts and searches may follow price rather than cause it.
- Selection: only high-attention events may have observable community data.
- Timestamp leakage: a daily ratio may incorporate activity after the decision point.
- Multiple simultaneous news items may drive both heat and return.
- Corrected disclosures and repeated contracts can be double-counted.
- Small-cap, liquidity, price-limit, and retail-ownership effects can masquerade as
  community effects.
- Deleted or moderated posts create non-random historical missingness.

## Required falsification checks for the next milestone

1. Fundamentals/market baseline versus baseline plus community features.
2. Shift or shuffle community timestamps while retaining event/stock structure.
3. Exclude the most extreme firms and event dates one at a time.
4. Separate KOSPI/KOSDAQ, size, liquidity, and prior-return regimes.
5. Evaluate returns strictly after a feasible decision timestamp.
6. Apply conservative transaction costs and price-limit/holiday rules.
