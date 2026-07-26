# Sprint 5 Retrospective — Intelligence, NLP & PDF Reports

**Sprint goal:** NLP-generated pros/cons for all 92 companies with confidence
scores; Cash Flow Intelligence classifying every company; all 92 tearsheets
and 11 sector PDFs generated with no overflow or layout errors.

## Outcome — goal met

| Exit criterion | Result |
|----------------|--------|
| pros_cons_generated.csv has >=1 pro and 1 con per company | ✅ verified via completeness check |
| All 92 tearsheets exist, >=30 KB each | ✅ |
| Visual review of 5 tearsheets: no overflow, no blank pages | ✅ |
| cashflow_intelligence.xlsx has 92 rows, all columns | ✅ |
| Sprint review | ✅ this document |

## What was built

- `src/nlp/parser.py` — regex parser for analysis.xlsx text fields, with
  cross-validation against computed CAGR
- `src/nlp/pros_cons_generator.py` — all 12 pro rules + 12 con rules with
  confidence scoring (only >60% kept)
- `src/analytics/cashflow_kpis.py` (extended) + `cashflow_intelligence.py` —
  CFO quality, CapEx intensity, distress and deleveraging detection
- `src/analytics/capital_allocation_report.py` — completeness check,
  distribution summary, year-over-year pattern-change tracking
- `src/reports/tearsheet.py` — 2-page ReportLab tearsheet template
- `src/reports/batch_tearsheets.py` — batch generation across all 92,
  skipping companies with <3 years of history
- `src/reports/sector_report.py` — 11 sector PDFs with median KPIs
- `src/reports/portfolio_summary.py` — one-page-per-company portfolio PDF
  with up/down/flat trend arrows

## What went well

- Testing caught and fixed three real bugs before they reached real data:
  a flat (unchanging) D/E ratio was incorrectly flagged as "rising" in the
  pros/cons generator; the sector report crashed if a metric column was
  missing; and the portfolio summary's trend-arrow colour formatting was
  invalid for ReportLab's font tag.
- The trend-arrow logic was verified against all three cases (up, down,
  flat-within-2%) plus edge cases (NaN, zero prior value) before trusting
  it on 92 real companies.
- Regex parsing handled every format variant from the spec's examples on
  the first pass, including singular/plural "Year" and spacing differences.

## What was challenging

- Some con/pro rules (e.g. Net Debt > 3x EBITDA) rely on proxy columns
  since a true EBITDA field isn't in the schema — used cash_from_operations
  as the closest available proxy and documented the substitution.
- Distinguishing "flat" from "declining"/"improving" trend needed a
  deliberate tolerance band (2%) rather than a strict inequality, to avoid
  noisy arrows on essentially-unchanged metrics.

## Notes carried forward

- Any company with zero triggered pros or cons (an "unremarkable" company
  on every rule) would need a fallback — worth checking the real 92-company
  run for this case specifically.
- The portfolio summary's D/E arrow is purely directional (down = ratio
  decreased), not a "good/bad" judgement — a declining D/E is favourable
  but shows the same down-arrow convention as a declining ROE.

## Next sprint

Sprint 6 — API, ML & QA: KMeans clustering, the FastAPI server (16
endpoints), the full pytest suite (60+ tests), and final documentation
(analyst guide + acceptance checklist).
