# Data Model: Crowd Excess Feasibility

## Canonical time and lineage

- API timestamps and community observations are timezone-aware and normalized to UTC.
- KRX daily rows use an exchange-local `date` because no intraday time is implied.
- Every file-backed row carries `source_file` and `source_sha256`.
- Every observation distinguishes `observed_at` from `collected_at` where applicable.

## DisclosureRecord

| Field | Type | Rule |
|---|---|---|
| receipt_number | string | 14 digits; stable DART viewer identifier |
| corporation_code | string | 8 digits |
| stock_code | string/null | six digits when listed |
| raw_stock_code | string | original OpenDART value, including non-common alphanumeric codes |
| corporation_name | string | submitted name |
| report_name | string | correction prefixes retained |
| received_date | date | DART receipt date; not an intraday timestamp |
| market_class | enum | KOSPI, KOSDAQ, KONEX, OTHER |

## KRX canonical CSVs

`krx_prices.csv`:

```text
date,ticker,name,open,high,low,close,volume,trading_value
```

`krx_investor_flows.csv`:

```text
date,ticker,retail_net_value,foreign_net_value,institution_net_value
```

Values are KRW unless input metadata says otherwise. This milestone does not infer units
from ambiguous column labels.

## CommunityObservation

```text
source,post_id_hash,ticker,posted_at,author_hash,sentiment_score,
emotion_intensity,is_duplicate,reply_count,like_count,collected_at,collection_basis
```

- `sentiment_score`: -1 to +1.
- `emotion_intensity`: 0 to 1, independent of direction.
- `collection_basis`: `manual_observation`, `official_api`, `licensed_export`, or
  `consented_dataset`.
- Post text and raw user IDs are intentionally absent.

## CommunityHeat

The starting score retains components rather than only one scalar:

```text
activity_z              35%
participation_z         20%
sentiment_extremity_z   20%
disagreement_z          15%
engagement_z            10%
duplicate penalty       25% * duplicate_ratio
```

Weights are a preregistered starting recipe, not learned evidence.

## CrowdExcessResult

```text
actual_heat
predicted_normal_heat
crowd_excess = actual_heat - predicted_normal_heat
```

The baseline design matrix contains only information available by the decision timestamp:
contract magnitude, prior abnormal return, prior volatility, log market cap, market return,
and an after-hours indicator.
