"""2-page company tearsheet PDF generator (Sprint 5, Day 33).

Page 1: navy header, 6 KPI tiles (2 rows x 3), 10-year Revenue/Net Profit
        bar chart, ROE/ROCE dual-axis line chart.
Page 2: Balance Sheet composition stacked bar, Cash Flow waterfall,
        Pros (green bullets), Cons (red bullets), Capital Allocation badge.

All table cells use Paragraph (word-wrap) rather than raw strings, so long
text never overflows a cell.

Run standalone test:  python -m src.reports.tearsheet
"""

import io
import os
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak,
)

NAVY = colors.HexColor("#1F3864")
GREEN = colors.HexColor("#2E7D32")
RED = colors.HexColor("#C62828")
LIGHT_GREY = colors.HexColor("#F2F2F2")

styles = getSampleStyleSheet()
CELL_STYLE = ParagraphStyle("cell", parent=styles["Normal"], fontSize=8, leading=10, wordWrap="CJK")
KPI_LABEL = ParagraphStyle("kpi_label", parent=styles["Normal"], fontSize=9, textColor=colors.white)
KPI_VALUE = ParagraphStyle("kpi_value", parent=styles["Normal"], fontSize=14,
                          textColor=colors.white, fontName="Helvetica-Bold")


def _fmt(val, suffix=""):
    return f"{val:.2f}{suffix}" if pd.notna(val) else "N/A"


def _fig_to_image(fig, width_cm=17, height_cm=7) -> Image:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=width_cm * cm, height=height_cm * cm)


def _kpi_tiles(kpis: dict) -> Table:
    """6 KPI tiles, 2 rows of 3, navy tiles with white text."""
    items = list(kpis.items())
    rows = [items[0:3], items[3:6]]
    data = []
    for row in rows:
        label_row = [Paragraph(k, KPI_LABEL) for k, _ in row]
        value_row = [Paragraph(v, KPI_VALUE) for _, v in row]
        data.append(label_row)
        data.append(value_row)
    t = Table(data, colWidths=[5.6 * cm] * 3, rowHeights=[0.7 * cm, 1.0 * cm] * 2)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.white),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _revenue_profit_chart(pl_h: pd.DataFrame) -> Image:
    hist = pl_h.sort_values("year").tail(10)
    fig, ax = plt.subplots(figsize=(8.5, 3.2))
    x = range(len(hist))
    width = 0.35
    ax.bar([i - width / 2 for i in x], hist["sales"], width, label="Revenue", color="#2E75B6")
    ax.bar([i + width / 2 for i in x], hist["net_profit"], width, label="Net Profit", color="#70AD47")
    ax.set_xticks(list(x))
    ax.set_xticklabels(hist["year"], rotation=45, ha="right", fontsize=7)
    ax.set_title("Revenue & Net Profit — 10 Years", fontsize=10)
    ax.legend(fontsize=7)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    return _fig_to_image(fig)


def _roe_roce_chart(ratio_h: pd.DataFrame) -> Image:
    hist = ratio_h.sort_values("year").tail(10)
    fig, ax = plt.subplots(figsize=(8.5, 3.2))
    ax.plot(hist["year"], hist["return_on_equity_pct"], marker="o", label="ROE %", color="#2E75B6")
    if "return_on_capital_employed_pct" in hist.columns:
        ax.plot(hist["year"], hist["return_on_capital_employed_pct"], marker="s",
                label="ROCE %", color="#C00000")
    ax.set_xticks(range(len(hist))); ax.set_xticklabels(hist["year"], rotation=45, ha="right", fontsize=7)
    ax.set_title("ROE & ROCE Trend — 10 Years", fontsize=10)
    ax.legend(fontsize=7)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    return _fig_to_image(fig)


def _balance_sheet_chart(bs_h: pd.DataFrame) -> Image:
    hist = bs_h.sort_values("year").tail(10)
    fig, ax = plt.subplots(figsize=(8.5, 3.2))
    equity = hist["equity_capital"].fillna(0) + hist["reserves"].fillna(0)
    ax.bar(hist["year"], equity, label="Equity", color="#2E75B6")
    ax.bar(hist["year"], hist["borrowings"].fillna(0), bottom=equity,
          label="Borrowings", color="#C00000")
    other = hist.get("other_liabilities", pd.Series(0, index=hist.index)).fillna(0)
    ax.bar(hist["year"], other, bottom=equity + hist["borrowings"].fillna(0),
          label="Other Liabilities", color="#A6A6A6")
    ax.set_xticks(range(len(hist))); ax.set_xticklabels(hist["year"], rotation=45, ha="right", fontsize=7)
    ax.set_title("Balance Sheet Composition — 10 Years", fontsize=10)
    ax.legend(fontsize=7)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    return _fig_to_image(fig)


def _cashflow_waterfall(cf_latest: pd.Series) -> Image:
    labels = ["CFO", "CFI", "CFF", "Net Cash Flow"]
    vals = [cf_latest.get("operating_activity", 0) or 0,
           cf_latest.get("investing_activity", 0) or 0,
           cf_latest.get("financing_activity", 0) or 0,
           cf_latest.get("net_cash_flow", 0) or 0]
    colors_ = ["#2E7D32" if v >= 0 else "#C62828" for v in vals]
    fig, ax = plt.subplots(figsize=(8.5, 3.2))
    ax.bar(labels, vals, color=colors_)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_title("Cash Flow — Latest Year (₹ Cr)", fontsize=10)
    ax.tick_params(labelsize=8)
    fig.tight_layout()
    return _fig_to_image(fig, width_cm=17, height_cm=6)


def build_tearsheet(ticker: str, company_name: str, sector: str,
                    ratio_h: pd.DataFrame, pl_h: pd.DataFrame, bs_h: pd.DataFrame,
                    cf_h: pd.DataFrame, pros: list, cons: list,
                    capital_label: str, out_path: str) -> None:
    doc = SimpleDocTemplate(out_path, pagesize=A4,
                            topMargin=1.2 * cm, bottomMargin=1.2 * cm,
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    elements = []

    # ---- Header bar ----
    header_style = ParagraphStyle("header", parent=styles["Title"], textColor=colors.white,
                                  fontSize=18, leading=22)
    sub_style = ParagraphStyle("sub", parent=styles["Normal"], textColor=colors.white, fontSize=10)
    header_table = Table(
        [[Paragraph(f"{company_name} ({ticker})", header_style)],
         [Paragraph(f"Sector: {sector or 'N/A'}", sub_style)]],
        colWidths=[17.5 * cm],
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.4 * cm))

    # ---- KPI tiles ----
    latest = ratio_h.sort_values("year").iloc[-1] if not ratio_h.empty else pd.Series(dtype=float)
    kpis = {
        "ROE": _fmt(latest.get("return_on_equity_pct"), "%"),
        "ROCE": _fmt(latest.get("return_on_capital_employed_pct"), "%"),
        "NPM": _fmt(latest.get("net_profit_margin_pct"), "%"),
        "D/E": _fmt(latest.get("debt_to_equity")),
        "Revenue CAGR 5yr": _fmt(latest.get("revenue_cagr_5yr"), "%"),
        "FCF (₹ Cr)": _fmt(latest.get("free_cash_flow_cr")),
    }
    elements.append(_kpi_tiles(kpis))
    elements.append(Spacer(1, 0.4 * cm))

    # ---- Charts, page 1 ----
    if not pl_h.empty:
        elements.append(_revenue_profit_chart(pl_h))
    if not ratio_h.empty:
        elements.append(_roe_roce_chart(ratio_h))

    elements.append(PageBreak())

    # ---- Page 2 ----
    if not bs_h.empty:
        elements.append(_balance_sheet_chart(bs_h))
        elements.append(Spacer(1, 0.3 * cm))
    if not cf_h.empty:
        cf_latest = cf_h.sort_values("year").iloc[-1]
        elements.append(_cashflow_waterfall(cf_latest))
        elements.append(Spacer(1, 0.3 * cm))

    # Pros / Cons
    pros_style = ParagraphStyle("pros", parent=styles["Normal"], textColor=GREEN, fontSize=9)
    cons_style = ParagraphStyle("cons", parent=styles["Normal"], textColor=RED, fontSize=9)

    elements.append(Paragraph("<b>Pros</b>", styles["Heading3"]))
    if pros:
        for p in pros:
            elements.append(Paragraph(f"&#10003; {p}", pros_style))
    else:
        elements.append(Paragraph("No pros recorded.", styles["Normal"]))
    elements.append(Spacer(1, 0.2 * cm))

    elements.append(Paragraph("<b>Cons</b>", styles["Heading3"]))
    if cons:
        for c in cons:
            elements.append(Paragraph(f"&#10007; {c}", cons_style))
    else:
        elements.append(Paragraph("No cons recorded.", styles["Normal"]))
    elements.append(Spacer(1, 0.3 * cm))

    # Capital allocation badge
    badge = Table([[Paragraph(f"Capital Allocation: {capital_label or 'N/A'}",
                              ParagraphStyle("badge", textColor=colors.white, fontSize=11,
                                            fontName="Helvetica-Bold"))]],
                  colWidths=[10 * cm])
    badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(badge)

    doc.build(elements)


def _test_run():
    """Standalone smoke test on 5 companies from different sectors."""
    import os
    db = os.getenv("DB_PATH", "data/nifty100.db")
    conn = sqlite3.connect(db)

    test_tickers = ["TCS", "HDFCBANK", "RELIANCE", "SUNPHARMA", "TATASTEEL"]
    out_dir = Path("reports/tearsheets")
    out_dir.mkdir(parents=True, exist_ok=True)

    for ticker in test_tickers:
        comp = pd.read_sql("SELECT company_name FROM companies WHERE id=?", conn, params=(ticker,))
        if comp.empty:
            print(f"  SKIP {ticker}: not found in companies table")
            continue
        name = comp.iloc[0]["company_name"]
        sector = pd.read_sql("SELECT broad_sector FROM sectors WHERE company_id=?",
                             conn, params=(ticker,))
        sector = sector.iloc[0]["broad_sector"] if not sector.empty else ""

        ratio_h = pd.read_sql("SELECT * FROM financial_ratios WHERE company_id=? ORDER BY year",
                              conn, params=(ticker,))
        pl_h = pd.read_sql("SELECT * FROM profitandloss WHERE company_id=? ORDER BY year",
                           conn, params=(ticker,))
        bs_h = pd.read_sql("SELECT * FROM balancesheet WHERE company_id=? ORDER BY year",
                           conn, params=(ticker,))
        cf_h = pd.read_sql("SELECT * FROM cashflow WHERE company_id=? ORDER BY year",
                           conn, params=(ticker,))

        pros_cons_path = Path("output/pros_cons_generated.csv")
        pros, cons, capital_label = [], [], None
        if pros_cons_path.exists():
            pc = pd.read_csv(pros_cons_path)
            pros = pc[(pc.company_id == ticker) & (pc.type == "pro")]["text"].tolist()
            cons = pc[(pc.company_id == ticker) & (pc.type == "con")]["text"].tolist()

        cap_path = Path("output/capital_allocation.csv")
        if cap_path.exists():
            cap = pd.read_csv(cap_path)
            row = cap[cap.company_id == ticker].sort_values("year").tail(1)
            if not row.empty:
                capital_label = row.iloc[0]["pattern_label"]

        out_path = out_dir / f"{ticker}_tearsheet.pdf"
        build_tearsheet(ticker, name, sector, ratio_h, pl_h, bs_h, cf_h,
                        pros, cons, capital_label, str(out_path))
        size_kb = out_path.stat().st_size / 1024
        print(f"  {ticker}: {out_path} ({size_kb:.0f} KB)")

    conn.close()


if __name__ == "__main__":
    _test_run()
