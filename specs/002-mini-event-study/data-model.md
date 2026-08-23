# Data Model: Mini Event Study

## Run directory

```text
data/processed/mini_event_study/<run-id>/
├── manifest.json
├── disclosure_audit.csv
├── selected_events.csv
├── attention.csv
├── stock_prices.csv
├── market_indices.csv
├── outcomes.csv
├── report.md
└── raw/
    ├── opendart/
    ├── naver/
    └── public_data/
```

The entire tree is ignored by Git. `manifest.json` uses schema version `1` and maps every
raw artifact to its source, collection timestamp, SHA-256, and byte size.

## DisclosureAuditRow

```text
receipt_number,received_date,ticker,raw_ticker,corporation_name,report_name,market_class,
selected,disposition,source_document_sha256
```

`disposition` is a stable value such as `selected`, `correction`, `subsidiary_notice`,
`unlisted`, `wrong_market`, `wrong_report_family`, or `document_parse_failed`.

## SupplyContractEvent

```text
receipt_number,received_date,ticker,corporation_name,report_name,market_class,
contract_amount_krw,recent_revenue_krw,reported_revenue_ratio_percent,
computed_revenue_ratio_percent,ratio_difference_percentage_points,
source_document_sha256,collected_at
```

Numeric fields are decimal text in CSV. The reported and computed ratios are separate.

## AttentionWindowResult

```text
receipt_number,ticker,window_start,window_end,baseline_start,baseline_end,
event_start,event_end,baseline_observed_days,event_observed_days,
baseline_median_ratio,event_mean_ratio,attention_excess,missing_reason,
source_snapshot_sha256,collected_at
```

Starting definition:

```text
attention_excess = log1p(event_mean_ratio) - log1p(baseline_median_ratio)
baseline = receipt date -14 through -3 calendar days
event    = receipt date +0 through +2 calendar days
```

Both subwindows come from one API response. A completely absent or all-zero baseline makes
the result missing because the starting normalization is not informative enough.

## PublicStockPriceRow

```text
date,ticker,name,market,open,high,low,close,volume,trading_value,
listed_shares,market_cap,source_snapshot_sha256,collected_at
```

## MarketIndexRow

```text
date,index_name,open,high,low,close,volume,trading_value,
source_snapshot_sha256,collected_at
```

## MiniEventStudyRow

One row per selected event. `h0`, `h1`, `h3`, and `h5` mean decision-day close and 1, 3,
and 5 subsequent observed trading-day closes, all measured from decision-day open.

```text
receipt_number,ticker,market_class,received_date,decision_date,
contract_revenue_ratio,attention_excess,
raw_return_h0,raw_return_h1,raw_return_h3,raw_return_h5,
market_return_h0,market_return_h1,market_return_h3,market_return_h5,
abnormal_return_h0,abnormal_return_h1,abnormal_return_h3,abnormal_return_h5,
price_missing_reason,index_missing_reason
```

## Time rules

- OpenDART receipt dates have no intraday time and remain Korean calendar dates.
- The decision day is the first actual stock-price row with `date > received_date`.
- All collection timestamps are timezone-aware UTC.
- Daily rows are never forward-filled and market/index dates must match exactly.
