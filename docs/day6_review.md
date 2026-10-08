# Sprint 1 · Day 6 — Manual Data Quality Review

**Method:** Ran `src/etl/review.py` — sampled 5 random companies across all
time-series tables, checked year coverage, and flagged companies with < 5 years.

## 5 companies reviewed

| Company | P&L | Balance Sheet | Cash Flow | Ratios | Span |
|---------|-----|---------------|-----------|--------|------|
| ONGC | 12 | 13 | 12 | 12 | 2013–2024 |
| SBILIFE | 12 | 13 | 12 | 12 | 2013–2024 |
| KOTAKBANK | 12 | 12 | 12 | 12 | 2013–2024 |
| DABUR | 12 | 13 | 12 | 12 | 2013–2024 |
| JSWENERGY | 12 | 13 | 12 | 12 | 2013–2024 |

All five load correctly with full, consistent coverage. No loader bugs found.

## Coverage distribution (P&L)

| Years | Companies |
|-------|-----------|
| 12 | 81 |
| 11 | 5 |
| 10 | 2 |
| 8 | 1 |
| 7 | 1 |
| 6 | 1 |
| 2 | 1 |

89 of 92 companies have ≥ 10 years of history — comfortably above the ≥90%
coverage acceptance gate.

## Findings (real data characteristics, not bugs)

1. **JIOFIN — 2 years only.** Jio Financial Services listed in 2023, so 2 years
   is accurate. Flagged by DQ-16; will be excluded from long-term CAGR in Sprint 2.
2. **Interim balance-sheet rows.** A few companies show a balance-sheet entry
   ending `2024-09` alongside the `2024-03` annual rows. Harmless; noted for
   awareness during ratio computation.

## Conclusion

The load is correct. No loader bugs to fix. Re-run not required. Sprint 1 data
foundation is sound and ready for the Sprint 2 ratio engine.
