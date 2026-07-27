"""Analyst Guide PDF generator (Sprint 6, Day 44).

Produces docs/analyst_guide.pdf covering: dashboard screen-by-screen usage,
the screener, generating tearsheets, calling the API with curl examples,
and troubleshooting. Target: at least 10 pages.

Run:  python -m src.docs.analyst_guide
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
    ListFlowable,
    ListItem,
)

NAVY = colors.HexColor("#1F3864")
styles = getSampleStyleSheet()

H1 = ParagraphStyle(
    "H1", parent=styles["Title"], fontSize=20, textColor=NAVY, spaceAfter=14
)
H2 = ParagraphStyle(
    "H2", parent=styles["Heading2"], textColor=NAVY, spaceBefore=10, spaceAfter=6
)
BODY = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10.5, leading=15)
CODE = ParagraphStyle(
    "Code",
    parent=styles["Code"],
    fontSize=9,
    backColor=colors.HexColor("#F2F2F2"),
    leftIndent=10,
    spaceBefore=4,
    spaceAfter=8,
    leading=13,
)


def _section(title: str) -> list:
    return [Paragraph(title, H2)]


def _cover_page() -> list:
    elements = []
    elements.append(Spacer(1, 6 * cm))
    title_style = ParagraphStyle(
        "cover_title", parent=styles["Title"], fontSize=28, textColor=NAVY, alignment=1
    )
    sub_style = ParagraphStyle(
        "cover_sub", parent=styles["Normal"], fontSize=13, alignment=1, spaceBefore=10
    )
    elements.append(Paragraph("Nifty 100 Financial Intelligence Platform", title_style))
    elements.append(Paragraph("Analyst Guide", sub_style))
    elements.append(Spacer(1, 1 * cm))
    elements.append(Paragraph("Version 1.0 — Sprint 6", sub_style))
    elements.append(PageBreak())
    return elements


def _toc_page() -> list:
    items = [
        "1. Introduction & Platform Overview",
        "2. Getting Started — Setup in Under 30 Minutes",
        "3. Dashboard Guide — Home Screen",
        "4. Dashboard Guide — Company Profile Screen",
        "5. Dashboard Guide — Financial Screener",
        "6. Dashboard Guide — Peer Comparison",
        "7. Dashboard Guide — Trend, Sector & Capital Allocation Screens",
        "8. Dashboard Guide — Annual Reports Screen",
        "9. Generating PDF Tearsheets & Reports",
        "10. Using the REST API — curl Examples",
        "11. Troubleshooting Common Issues",
        "12. Glossary of Key Terms",
    ]
    elements = [Paragraph("Table of Contents", H1)]
    elements.append(
        ListFlowable([ListItem(Paragraph(i, BODY)) for i in items], bulletType="bullet")
    )
    elements.append(PageBreak())
    return elements


def _introduction() -> list:
    e = _section("1. Introduction & Platform Overview")
    e.append(
        Paragraph(
            "The Nifty 100 Financial Intelligence Platform is a self-contained analytics "
            "system covering all 92 Nifty 100 companies with data-availability history. "
            "It combines a cleaned SQLite database, a computed financial-ratio engine, "
            "an investment screener, peer comparison tools, a Streamlit dashboard, and a "
            "REST API — all built from 12 source datasets.",
            BODY,
        )
    )
    e.append(Spacer(1, 0.3 * cm))
    e.append(
        Paragraph(
            "This guide is written for analysts who will use the dashboard and API "
            "day-to-day, not for the engineers who built the pipeline. Screenshots are "
            "described in words where a live screen capture isn't included, since screen "
            "layouts may be refreshed between releases.",
            BODY,
        )
    )
    e.append(PageBreak())
    return e


def _getting_started() -> list:
    e = _section("2. Getting Started — Setup in Under 30 Minutes")
    steps = [
        ("Clone or unzip the project", "unzip nifty100_project.zip -d nifty100/"),
        (
            "Create a virtual environment",
            "python -m venv venv\nsource venv/Scripts/activate",
        ),
        ("Install dependencies", "pip install -r requirements.txt"),
        ("Build the database", "python -m src.etl.db_loader"),
        ("Compute financial ratios", "python -m src.analytics.compute_ratios"),
        ("Run the test suite", "pytest tests/ -v"),
        ("Launch the dashboard", "streamlit run src/dashboard/app.py"),
        ("Launch the API (separate terminal)", "uvicorn src.api.main:app --port 8000"),
    ]
    for i, (label, cmd) in enumerate(steps, 1):
        e.append(Paragraph(f"<b>Step {i}: {label}</b>", BODY))
        e.append(Paragraph(cmd.replace("\n", "<br/>"), CODE))
    e.append(
        Paragraph(
            "If setup succeeds, the dashboard opens automatically at "
            "http://localhost:8501 and the API documentation is available at "
            "http://localhost:8000/docs.",
            BODY,
        )
    )
    e.append(PageBreak())
    return e


def _dashboard_screen(title: str, body_lines: list) -> list:
    e = _section(title)
    for line in body_lines:
        e.append(Paragraph(line, BODY))
        e.append(Spacer(1, 0.15 * cm))
    e.append(PageBreak())
    return e


def _tearsheets_section() -> list:
    e = _section("9. Generating PDF Tearsheets & Reports")
    e.append(
        Paragraph(
            "Company tearsheets, sector reports, and the portfolio summary are "
            "pre-generated batch outputs, not created live from the dashboard. To "
            "regenerate them after a data refresh:",
            BODY,
        )
    )
    e.append(Paragraph("python -m src.reports.batch_tearsheets", CODE))
    e.append(Paragraph("python -m src.reports.sector_report", CODE))
    e.append(Paragraph("python -m src.reports.portfolio_summary", CODE))
    e.append(
        Paragraph(
            "Tearsheets land in reports/tearsheets/, sector reports in "
            "reports/sector/, and the portfolio summary in reports/portfolio/. "
            "A company with fewer than 3 years of history is skipped and logged "
            "to output/skipped_tearsheets.csv rather than causing an error.",
            BODY,
        )
    )
    e.append(PageBreak())
    return e


def _api_section() -> list:
    e = _section("10. Using the REST API — curl Examples")
    examples = [
        ("Health check", "curl http://localhost:8000/api/v1/health"),
        ("List all companies", "curl http://localhost:8000/api/v1/companies"),
        ("Filter by sector", 'curl "http://localhost:8000/api/v1/companies?sector=IT"'),
        ("Company profile", "curl http://localhost:8000/api/v1/companies/TCS"),
        (
            "Company ratios history",
            "curl http://localhost:8000/api/v1/companies/TCS/ratios",
        ),
        (
            "Run the screener",
            'curl "http://localhost:8000/api/v1/screener?min_roe=15&max_de=1"',
        ),
        ("Sector summary", "curl http://localhost:8000/api/v1/sectors"),
        ("Peer group data", 'curl "http://localhost:8000/api/v1/peers/IT%20Services"'),
        (
            "Download a tearsheet",
            "curl -o TCS.pdf http://localhost:8000/api/v1/companies/TCS/tearsheet",
        ),
    ]
    for label, cmd in examples:
        e.append(Paragraph(f"<b>{label}</b>", BODY))
        e.append(Paragraph(cmd, CODE))
    e.append(
        Paragraph(
            "The full interactive API documentation (OpenAPI / Swagger UI) is "
            "available at http://localhost:8000/docs whenever the API server is "
            "running, and lets you try every endpoint directly from the browser.",
            BODY,
        )
    )
    e.append(PageBreak())
    return e


def _troubleshooting() -> list:
    e = _section("11. Troubleshooting Common Issues")
    issues = [
        (
            "Dashboard shows 'No data available'",
            "Confirm the database has been built (python -m src.etl.db_loader) and the "
            "financial_ratios table is populated (python -m src.analytics.compute_ratios).",
        ),
        (
            "Port already in use",
            "Another process is likely using port 8501 or 8000. Stop it, or run with a "
            "different port: streamlit run src/dashboard/app.py --server.port 8502",
        ),
        (
            "'Ticker not found' for a company you expect to exist",
            "Tickers are case-sensitive and normalised to upper-case, no spaces. Search "
            "by company name instead if unsure of the exact ticker.",
        ),
        (
            "Tearsheet download returns 404",
            "The PDF hasn't been generated yet for that company, or it was skipped for "
            "having fewer than 3 years of history. Check output/skipped_tearsheets.csv.",
        ),
        (
            "Screener returns 0 companies",
            "Thresholds may be too strict for the current data. Try the preset buttons "
            "first, then loosen one filter at a time.",
        ),
        (
            "API returns HTTP 500",
            "Check the DB_PATH environment variable points at the correct database file, "
            "and that the database has been built.",
        ),
    ]
    for problem, fix in issues:
        e.append(Paragraph(f"<b>Issue:</b> {problem}", BODY))
        e.append(Paragraph(f"<b>Fix:</b> {fix}", BODY))
        e.append(Spacer(1, 0.25 * cm))
    e.append(PageBreak())
    return e


def _glossary() -> list:
    e = _section("12. Glossary of Key Terms")
    terms = [
        ("ROE", "Return on Equity — net profit divided by shareholder equity."),
        ("ROCE", "Return on Capital Employed — a broader profitability measure."),
        ("D/E", "Debt-to-Equity — a leverage ratio; 0 means debt-free."),
        ("CAGR", "Compound Annual Growth Rate — annualised growth over a period."),
        (
            "FCF",
            "Free Cash Flow — cash generated after operating and investing activity.",
        ),
        (
            "ICR",
            "Interest Coverage Ratio — ability to service debt from operating profit.",
        ),
        ("Peer Group", "A set of comparable companies used for relative ranking."),
        (
            "Composite Score",
            "A 0-100 weighted quality score combining profitability, "
            "cash quality, growth, and leverage.",
        ),
    ]
    data = [[Paragraph(f"<b>{t}</b>", BODY), Paragraph(d, BODY)] for t, d in terms]
    table = Table(data, colWidths=[3 * cm, 13 * cm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    e.append(table)
    return e


def build_analyst_guide(out_path: str = "docs/analyst_guide.pdf") -> int:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    elements = []
    elements += _cover_page()
    elements += _toc_page()
    elements += _introduction()
    elements += _getting_started()
    elements += _dashboard_screen(
        "3. Dashboard Guide — Home Screen",
        [
            "The Home screen is the landing page, showing 6 summary KPI tiles "
            "(average ROE, median P/E, median D/E, total companies, median revenue "
            "CAGR, and debt-free company count), a sector-breakdown donut chart, and "
            "a top-5 companies table by composite quality score.",
            "Use the year selector in the sidebar to view metrics as of an earlier year.",
        ],
    )
    elements += _dashboard_screen(
        "4. Dashboard Guide — Company Profile Screen",
        [
            "Search any of the 92 companies by name or ticker. The profile shows a "
            "company card (sector, description), 6 KPI tiles, a 10-year revenue and "
            "profit chart, an ROE/ROCE trend line, and pros/cons as coloured badges.",
            "If a ticker cannot be found, a friendly message appears rather than an error.",
        ],
    )
    elements += _dashboard_screen(
        "5. Dashboard Guide — Financial Screener",
        [
            "Use the 10 sidebar sliders to set your own thresholds, or click one of the "
            "6 preset buttons (Quality, Value, Growth, Dividend, Debt-Free, Turnaround) "
            "to auto-fill sensible starting values.",
            "The results table updates live as you move a slider. Use the CSV download "
            "button to export the current result set.",
            "Note: the Debt-to-Equity filter automatically excludes Financials-sector "
            "companies, since high leverage is structurally normal for banks and NBFCs.",
        ],
    )
    elements += _dashboard_screen(
        "6. Dashboard Guide — Peer Comparison",
        [
            "Select a peer group from the dropdown to see a radar chart comparing a "
            "chosen company against its peer group average across 8 metrics, plus a "
            "side-by-side table with the benchmark company highlighted in gold.",
        ],
    )
    elements += _dashboard_screen(
        "7. Dashboard Guide — Trend, Sector & Capital Allocation",
        [
            "Trend Analysis overlays up to 3 metrics over a 10-year history with "
            "year-over-year change shown on hover.",
            "Sector Analysis shows a revenue-vs-ROE bubble chart and sector median bars.",
            "Capital Allocation Map is a treemap grouping all companies into 8 "
            "capital-allocation patterns (Reinvestor, Distress Signal, etc.) — click a "
            "pattern to see the company list.",
        ],
    )
    elements += _dashboard_screen(
        "8. Dashboard Guide — Annual Reports Screen",
        [
            "Search a company to see its available annual report links by year, with "
            "a red 'Report unavailable' badge if a link no longer resolves.",
        ],
    )
    elements += _tearsheets_section()
    elements += _api_section()
    elements += _troubleshooting()
    elements += _glossary()

    doc.build(elements)

    try:
        from pypdf import PdfReader

        n_pages = len(PdfReader(out_path).pages)
    except Exception:
        n_pages = None
    return n_pages


if __name__ == "__main__":
    n_pages = build_analyst_guide()
    print(
        f"analyst_guide.pdf generated: {n_pages} pages "
        f"({'PASS' if n_pages and n_pages >= 10 else 'CHECK — need >=10 pages'})"
    )
