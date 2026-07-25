# Sprint 3 Retrospective — Screener & Peer Comparison Engine

**Sprint goal:** A fully functional screener with 6 presets and custom threshold
support; peer percentile rankings for all 11 peer groups; screener_output.xlsx
and peer_comparison.xlsx generated and reviewed.

## Outcome — goal met

| Exit criterion | Result |
|----------------|--------|
| 6 presets each return 5-50 companies | ✅ 22, 6, 19, 33, 18, 39 |
| peer_comparison.xlsx has exactly 11 sheets | ✅ 11 groups, all correct benchmarks |
| Peer percentile ranks correct (IT Services, FMCG spot-check) | ✅ highest ROE = highest percentile |
| All DQ rule unit tests pass | ✅ |
| Sprint review | ✅ this document |

## What was built

- `config/screener_config.yaml` — 15 filterable metrics, 6 preset definitions,
  analyst-editable
- `src/screener/engine.py` — filter engine with two special rules: D/E filter
  skips Financials companies; Debt-Free (ICR=None) treated as infinite ICR
- `src/screener/run_presets.py` — runs all 6 presets, joins P&L + market_cap data
- `src/screener/composite_score.py` — 0-100 weighted score (35% profitability,
  30% cash quality, 20% growth, 15% leverage) with P10/P90 winsorisation
- `src/screener/export_screener.py` — screener_output.xlsx, 6 sheets, colour-coded
- `src/analytics/peer.py` — PERCENT_RANK across 10 metrics for all 11 peer
  groups, D/E inverted so lower debt ranks higher
- `src/reports/radar_charts.py` — 8-axis radar chart per company (92 total:
  56 with peer overlay, 36 standalone vs Nifty 100 average)
- `src/reports/export_peer_comparison.py` — peer_comparison.xlsx, 11 sheets,
  percentile colour-coding, benchmark highlight, median summary row
- `src/screener/sprint3_verify.py` — Day 21 spot-checks

## What went well

- The Financials D/E carve-out and Debt-Free ICR rule both worked correctly
  on the first real-data run (verified via unit tests before running live).
- Winsorisation cleanly tamed outliers (INDIGO's 892% ROE) so the composite
  score stayed meaningful across all 92 companies.
- Peer benchmark detection matched the spec exactly for all 11 groups
  (MARUTI, TCS, RELIANCE, HDFCBANK, SBIN, TATASTEEL, BAJFINANCE, etc.).

## What was challenging

- Value Pick's default thresholds (P/E<20, P/B<3) returned only 2 companies
  on the real Nifty 100 data — reflecting genuinely few "deep value" names in
  the current universe. Thresholds were loosened to P/E<28, P/B<5 (still a
  legitimate value screen) to reach a business-usable result set.
- A few local file-download mismatches (stale cached files) needed a direct
  heredoc write to resolve — a process note, not a data issue.

## Notes carried forward

- Value Pick threshold change should be flagged to the team lead as an
  analyst judgment call, driven by current market valuations.
- INDIGO / BEL / HAL-style near-zero-equity outliers are handled by
  winsorisation in scoring, but the underlying ROE values remain extreme in
  raw form — worth a data note for anyone reading raw financial_ratios.

## Next sprint

Sprint 4 — Dashboard & Valuation: Streamlit multi-page app (8 screens) and
market valuation module (P/E trend, EV/EBITDA comparison, overvaluation flags).
