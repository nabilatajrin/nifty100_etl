# NIFTY 100 Financial Intelligence Platform

A production-grade financial analytics platform covering all 92 Nifty 100
companies — ETL pipeline, financial ratio engine, investment screener, peer
comparison, and an interactive Streamlit dashboard.

## Quick Start

```bash
# 1. Activate the virtual environment
source venv/Scripts/activate      # Windows Git Bash
# source venv/bin/activate        # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Build the database (loads all 12 source files)
python -m src.etl.db_loader

# 4. Compute the financial ratios
python -m src.analytics.compute_ratios

# 5. Run the test suite
pytest tests/ -v

# 6. Launch the dashboard
streamlit run src/dashboard/app.py
```

The dashboard opens at **http://localhost:8501**.

## Dashboard — 8 Screens

| Screen | What it shows |
|--------|---------------|
| 🏠 Home | 6 summary KPI tiles, sector breakdown donut, top-5 companies by composite score, year selector |
| 🏢 Company Profile | Search any of the 92 tickers — KPI tiles, 10-year revenue/profit chart, ROE/ROCE trend, pros & cons |
| 🔎 Screener | 10 threshold sliders, 6 one-click presets (Quality, Value, Growth, Dividend, Debt-Free, Turnaround), live results table, CSV export |
| 🆚 Peer Comparison | Pick a peer group, see a radar chart (company vs. group average) and a side-by-side table with the benchmark row highlighted |
| 📈 Trend Analysis | Overlay up to 3 metrics over a 10-year history with year-over-year % change on hover |
| 🏭 Sector Analysis | Revenue-vs-ROE bubble chart (bubble size = market cap) and sector median KPI bars |
| 🗺️ Capital Allocation Map | Treemap of all 92 companies grouped by their 8 capital-allocation patterns |
| 📄 Annual Reports | Company report links by year, with a red badge for broken/404 URLs |

**Note:** stock price and market capitalisation data (`stock_prices`, `market_cap`) are **simulated** for this project and are labelled as such throughout the dashboard and reports.

## Project Structure

```
nifty100_etl/
├── data/               # nifty100.db (SQLite, gitignored) + raw Excel (gitignored)
├── src/
│   ├── etl/            # loader, normaliser, validator, db_loader
│   ├── analytics/       # ratios, cagr, cashflow_kpis, compute_ratios, valuation, peer
│   ├── screener/        # filter engine, composite score, presets, Excel export
│   ├── dashboard/       # Streamlit app.py, cached db.py, pages/, qa_integration.py
│   └── reports/         # radar_charts.py, peer comparison Excel export
├── tests/               # pytest — ETL, DQ rules, KPI formulas, screener
├── config/               screener_config.yaml — analyst-editable thresholds
├── db/                   schema.sql — 12-table SQLite schema
├── output/               generated reports (Excel, CSV) — gitignored
├── reports/              radar_charts/ (92 PNGs) — committed
└── notebooks/            exploratory_queries.sql
```

## Running Tests

```bash
pytest tests/ -v
```

Current suite covers ETL normalisation, all 16 data-quality rules, KPI formula
edge cases (ROE, D/E, CAGR, cash-flow), and the screener's special rules
(Financials D/E carve-out, Debt-Free ICR handling).

## Key Design Notes

- **Header rows**: core Excel files use `pd.read_excel(path, header=1)`;
  supplementary files use `header=0`.
- **Ticker normalisation**: `company_id` is always stripped and upper-cased
  before any join.
- **Currency**: all monetary values are in ₹ Crore.
- **D/E screener filter**: Financials-sector companies are automatically
  excluded from D/E threshold checks (high leverage is structurally normal
  for banks/NBFCs/insurers).
- **CAGR edge cases**: a negative base year returns `TURNAROUND` rather than
  a misleading growth number; a zero-interest company shows `Debt Free`
  rather than dividing by zero.

## Sprint Progress

| Sprint | Focus | Status |
|--------|-------|--------|
| 1 | Data Foundation (ETL, validation, SQLite) | ✅ Complete |
| 2 | Financial Ratio Engine | ✅ Complete |
| 3 | Screener & Peer Comparison | ✅ Complete |
| 4 | Dashboard & Valuation | ✅ Complete |
| 5 | Intelligence & Reports | ⏳ |
| 6 | API, ML & QA | ⏳ |
