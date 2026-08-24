# Research Decisions

- NAVER Search Trend supports daily, weekly, and monthly relative ratios. The strategy uses only
  complete days and calls it cross-border search attention.
- Alpaca paper options and multi-leg orders are supported. The CLI remains the primary account
  and data boundary; official paper REST is the documented fallback for a multi-leg submission.
- OpenAI Responses Structured Outputs are used so invalid model output fails closed.
- Direct REST clients reuse `httpx`, keeping the Vercel function below its current bundle limit.
- Historical validation uses chronological windows and underlying returns; it does not claim a
  backtested option P&L where historical option coverage is unavailable.
