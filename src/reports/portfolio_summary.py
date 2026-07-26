"""Portfolio Summary PDF — one page per company (Sprint 5, Day 35).

Companies in alphabetical ticker order. Each page shows company name,
sector, top 6 KPIs, and a trend arrow per KPI: up if it improved in the
latest year, down if it declined, right if flat within 2%.

Run:  python -m src.reports.portfolio_summary
"""

import os
import sqlite3
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak

NAVY = colors.HexColor("#1F3864")
GREEN = colors.HexColor("#2E7D32")
RED = colors.HexColor("#C62828")
GREY = colors.HexColor("#616161")

styles = getSampleStyleSheet()
CELL = ParagraphStyle("cell", parent=styles["Normal"], fontSize=10, leading=13)

KPI_COLS = ["return_on_equity_pct", "operating_profit_margin_pct", "net_profit_margin_pct",
           "debt_to_equity", "revenue_cagr_5yr", "free_cash_flow_cr"]
KPI_LABELS = ["ROE %", "OPM %", "NPM %", "D/E", "Revenue CAGR 5yr %", "FCF ₹Cr"]

FLAT_TOLERANCE_PCT = 2.0


def _trend_arrow(latest, prior) -> tuple:
    """Returns (arrow_char, colour). Flat if within 2% of the prior value."""
    if pd.isna(latest) or pd.isna(prior):
        return "→", GREY
    if prior == 0:
        return ("↑", GREEN) if latest > 0 else ("→", GREY)
    pct_change = abs(latest - prior) / abs(prior) * 100
    if pct_change <= FLAT_TOLERANCE_PCT:
        return "→", GREY
    return ("↑", GREEN) if latest > prior else ("↓", RED)


def build_company_page(ticker: str, name: str, sector: str,
                       latest: pd.Series, prior: pd.Series) -> list:
    elements = []
    header_style = ParagraphStyle("h", parent=styles["Title"], textColor=colors.white, fontSize=16)
    sub_style = ParagraphStyle("s", parent=styles["Normal"], textColor=colors.white, fontSize=10)

    header = Table(
        [[Paragraph(f"{name} ({ticker})", header_style)],
         [Paragraph(f"Sector: {sector or 'N/A'}", sub_style)]],
        colWidths=[17.5 * cm],
    )
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 0.6 * cm))

    rows = [["KPI", "Value", "Trend"]]
    for col, label in zip(KPI_COLS, KPI_LABELS):
        val = latest.get(col)
        prior_val = prior.get(col) if prior is not None else None
        arrow, colour = _trend_arrow(val, prior_val)
        val_str = f"{val:.2f}" if pd.notna(val) else "N/A"
        hexcode = "#%02x%02x%02x" % tuple(int(c * 255) for c in colour.rgb())
        rows.append([Paragraph(label, CELL), Paragraph(val_str, CELL),
                     Paragraph(f'<font color="{hexcode}">{arrow}</font>', CELL)])

    table = Table(rows, colWidths=[8 * cm, 5 * cm, 3 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    return elements


def build_portfolio_summary(out_path: str, db_path: str = None):
    db_path = db_path or os.getenv("DB_PATH", "data/nifty100.db")
    conn = sqlite3.connect(db_path)

    companies = pd.read_sql("SELECT id, company_name FROM companies ORDER BY id", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    sector_map = dict(zip(sectors["company_id"], sectors["broad_sector"]))
    ratios = pd.read_sql("SELECT * FROM financial_ratios ORDER BY company_id, year", conn)
    conn.close()

    doc = SimpleDocTemplate(out_path, pagesize=A4, topMargin=1.5 * cm,
                            bottomMargin=1.5 * cm, leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    elements = []
    n_pages = 0

    for _, row in companies.iterrows():
        ticker, name = row["id"], row["company_name"]
        hist = ratios[ratios["company_id"] == ticker].sort_values("year")
        if hist.empty:
            continue
        latest = hist.iloc[-1]
        prior = hist.iloc[-2] if len(hist) >= 2 else None

        if n_pages > 0:
            elements.append(PageBreak())
        elements.extend(build_company_page(ticker, name, sector_map.get(ticker), latest, prior))
        n_pages += 1

    doc.build(elements)
    return n_pages


def main():
    load_dotenv()
    out_dir = Path("reports/portfolio")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "portfolio_summary.pdf"

    n_pages = build_portfolio_summary(str(out_path))
    size_kb = out_path.stat().st_size / 1024
    print(f"portfolio_summary.pdf: {n_pages} company pages, {size_kb:.0f} KB -> {out_path}")


if __name__ == "__main__":
    main()
