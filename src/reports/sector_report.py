"""Sector report generator — 11 PDFs (Sprint 5, Day 34).

Each PDF: a sector summary page (median KPIs across the sector) followed by
a table of every company in the sector with 8 metrics each.

Run:  python -m src.reports.sector_report
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
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

NAVY = colors.HexColor("#1F3864")
styles = getSampleStyleSheet()
CELL = ParagraphStyle(
    "cell", parent=styles["Normal"], fontSize=7, leading=9, wordWrap="CJK"
)

METRICS = [
    "return_on_equity_pct",
    "operating_profit_margin_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "free_cash_flow_cr",
    "interest_coverage",
]
METRIC_LABELS = [
    "ROE %",
    "OPM %",
    "NPM %",
    "D/E",
    "Rev CAGR 5yr %",
    "PAT CAGR 5yr %",
    "FCF ₹Cr",
    "ICR",
]


def _fmt(v):
    return f"{v:.2f}" if pd.notna(v) else "N/A"


def build_sector_pdf(sector: str, sector_df: pd.DataFrame, out_path: str):
    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
    )
    elements = []

    header_style = ParagraphStyle(
        "h", parent=styles["Title"], textColor=colors.white, fontSize=16
    )
    header = Table(
        [[Paragraph(f"{sector} — Sector Report", header_style)]], colWidths=[19 * cm]
    )
    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(header)
    elements.append(Spacer(1, 0.4 * cm))

    elements.append(
        Paragraph(f"<b>{len(sector_df)} companies in this sector</b>", styles["Normal"])
    )
    elements.append(Spacer(1, 0.2 * cm))

    available_metrics = [m for m in METRICS if m in sector_df.columns]
    available_labels = [
        lbl for lbl, m in zip(METRIC_LABELS, METRICS) if m in sector_df.columns
    ]

    medians = (
        sector_df[available_metrics].median(numeric_only=True)
        if available_metrics
        else pd.Series(dtype=float)
    )
    med_data = [["Metric", "Sector Median"]] + [
        [Paragraph(lbl, CELL), Paragraph(_fmt(medians.get(m)), CELL)]
        for lbl, m in zip(available_labels, available_metrics)
    ]
    med_table = Table(med_data, colWidths=[8 * cm, 6 * cm])
    med_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(med_table)
    elements.append(Spacer(1, 0.5 * cm))

    elements.append(Paragraph("<b>Companies in this sector</b>", styles["Heading3"]))
    header_row = [Paragraph("Ticker", CELL)] + [
        Paragraph(lbl, CELL) for lbl in available_labels
    ]
    rows = [header_row]
    for _, r in sector_df.iterrows():
        row = [Paragraph(str(r["company_id"]), CELL)] + [
            Paragraph(_fmt(r.get(m)), CELL) for m in available_metrics
        ]
        rows.append(row)

    col_widths = [2.2 * cm] + [2.1 * cm] * len(available_metrics)
    company_table = Table(rows, colWidths=col_widths, repeatRows=1)
    company_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F2F2F2")],
                ),
            ]
        )
    )
    elements.append(company_table)

    doc.build(elements)


def main():
    load_dotenv()
    db = os.getenv("DB_PATH", "data/nifty100.db")
    conn = sqlite3.connect(db)

    fr = pd.read_sql("SELECT * FROM financial_ratios ORDER BY company_id, year", conn)
    fr_latest = fr.sort_values("year").groupby("company_id").tail(1)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    conn.close()

    df = fr_latest.merge(sectors, on="company_id", how="left")

    out_dir = Path("reports/sector")
    out_dir.mkdir(parents=True, exist_ok=True)

    sector_names = sorted(df["broad_sector"].dropna().unique())
    for sector in sector_names:
        sub = df[df["broad_sector"] == sector].sort_values("company_id")
        safe_name = sector.replace(" ", "_").replace("&", "and")
        out_path = out_dir / f"{safe_name}_report.pdf"
        build_sector_pdf(sector, sub, str(out_path))
        size_kb = out_path.stat().st_size / 1024
        print(f"  {sector}: {len(sub)} companies -> {out_path.name} ({size_kb:.0f} KB)")

    print(f"\nTotal sector PDFs: {len(list(out_dir.glob('*.pdf')))}")


if __name__ == "__main__":
    main()
