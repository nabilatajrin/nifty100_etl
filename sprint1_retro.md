# Sprint 1 Retrospective — Data Foundation

**Sprint goal:** Build a fully loaded and validated SQLite database (`nifty100.db`)
with all tables from the 12 source files, with all 16 DQ rules run and CRITICAL
failures resolved.

## Outcome — goal met

| Exit criterion | Target | Result |
|----------------|--------|--------|
| `COUNT(*) FROM companies` | 92 | 92 ✅ |
| `PRAGMA foreign_key_check` | 0 rows | 0 ✅ |
| `load_audit.csv` CRITICAL rejections | 0 | 0 ✅ |
| ETL unit tests | 35+ pass | 50 pass ✅ |
| Manual review of 5 companies | correct | confirmed ✅ |
| All 12 source files loaded | yes | yes ✅ |

## What was built

- `src/etl/normaliser.py` — `normalize_year()` + `normalize_ticker()`
- `src/etl/loader.py` — Excel loader (header=1 core, header=0 supplementary)
- `src/etl/validator.py` — 16 data-quality rules
- `src/etl/db_loader.py` — schema build + clean-as-you-load + load audit
- `src/etl/review.py` — manual review / coverage report
- `db/schema.sql` — 12-table schema with PK/FK constraints
- `tests/` — 50 unit tests (35 normaliser + 15 DQ rules)
- Outputs: `nifty100.db`, `load_audit.csv`, `validation_failures.csv`

## What went well

- Test-first approach on the normaliser caught format edge cases early
  (`Mar 2023 15`, `TTM`) before they reached the database.
- Cleaning at load time (dedupe / drop orphans / drop bad years) turned 628
  flagged CRITICAL issues into a clean database with FK check = 0.
- Row counts matched the spec exactly on first full load.

## What was challenging

- Real data had more year-format variety than the spec's examples
  (interim dates, TTM rows) — needed an extra normaliser pass.
- 8 companies in the time-series tables (WIPRO, ZOMATO, etc.) are outside the
  92-company universe; handled as orphan-FK rejections per DQ-03.

## Data characteristics noted for Sprint 2

- JIOFIN has only 2 years (listed 2023) — exclude from long-term CAGR.
- A few interim balance-sheet rows (e.g. `2024-09`) sit alongside annual rows.
- P&L 1276→1070, BS 1312→1140, CF 1187→1056 after cleaning.

## Next sprint

Sprint 2 — Financial Ratio Engine: compute 50+ KPIs (NPM, OPM, ROE, ROCE, D/E,
CAGR, FCF, etc.) for every company-year and populate the `financial_ratios` table.
