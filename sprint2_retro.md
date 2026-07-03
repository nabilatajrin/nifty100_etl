# Sprint 2 Retrospective — Financial Ratio Engine

**Sprint goal:** Compute 14+ financial KPIs for every company-year and populate
the `financial_ratios` table, with edge cases handled and cross-checked.

## Outcome — goal met

| Exit criterion | Result |
|----------------|--------|
| KPI unit tests pass | 87 tests, 0 failures ✅ |
| financial_ratios populated | 1,070 rows ✅ |
| Edge cases handled | 6 CAGR + all denominator cases ✅ |
| Cross-check log produced | ratio_edge_cases.log, 18 anomalies ✅ |
| Screener preview returns sensible set | Quality screen in range ✅ |

## What was built

- `src/analytics/ratios.py` — profitability (NPM, OPM, ROE, ROCE, ROA) +
  leverage/efficiency (D/E, ICR, net debt, asset turnover)
- `src/analytics/cagr.py` — CAGR with 6 edge-case handlers
- `src/analytics/cashflow_kpis.py` — FCF, CFO quality, CapEx intensity,
  FCF conversion, 8-pattern capital allocation classifier
- `src/analytics/compute_ratios.py` — engine that populates financial_ratios
- `src/analytics/edge_cases.py` — ROE cross-check + bank carve-out log
- `src/analytics/screener_preview.py` — quality/debt-free/growth screens
- `tests/kpi/` — 37 KPI unit tests (8 + 8 + 10 + 11)
- Outputs: populated `financial_ratios` table, `capital_allocation.csv`,
  `ratio_edge_cases.log`

## What went well

- Every KPI function returns None on invalid denominators, so the whole engine
  ran across 1,070 company-years with no crashes.
- The cross-check log caught genuine source-data errors (TCS ROE stored as 0.52,
  BEL/HAL inflated by near-zero equity years) — exactly its purpose.
- Spot-check on TCS (ROE 38-51%, near-zero D/E, ~10.5% revenue CAGR) matched
  reality, giving confidence the engine is accurate.

## What was challenging

- The CAGR edge cases (turnaround, decline-to-loss, both-negative) needed careful
  sign handling to avoid returning misleading growth rates.
- Some source ROE/ROCE values are on different scales/snapshots than the computed
  values; handled by logging and categorising rather than forcing a match.

## Notes carried forward

- `financial_ratios` has 1,070 rows (not ~1,100) because Sprint 1 removed
  duplicates/TTM/orphans — the clean count is correct.
- BEL/HAL show inflated ROE in specific years (tiny equity base) — worth a
  winsorisation/clip step in a later sprint if these feed rankings.

## Next sprint

Sprint 3 — Screener, Health Scoring & Sector Analytics: build the 18-filter
screener, the 0-100 composite health score, and sector-level aggregates.
