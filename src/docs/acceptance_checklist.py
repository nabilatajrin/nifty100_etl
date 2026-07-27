"""Final acceptance checklist PDF (Sprint 6, Day 45).

Checks whether each of the 23 deliverables exists on disk and generates
docs/acceptance_checklist.pdf documenting the result, ready for team-lead
sign-off.

Run:  python -m src.docs.acceptance_checklist
"""

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

NAVY = colors.HexColor("#1F3864")
GREEN = colors.HexColor("#C6EFCE")
RED = colors.HexColor("#FFC7CE")
styles = getSampleStyleSheet()
CELL = ParagraphStyle("cell", parent=styles["Normal"], fontSize=8, leading=10)

DELIVERABLES = [
    ("D-01", "Sprint 1", "nifty100.db", "data/nifty100.db"),
    ("D-02", "Sprint 1", "load_audit.csv", "output/load_audit.csv"),
    ("D-03", "Sprint 1", "validation_failures.csv", "output/validation_failures.csv"),
    ("D-04", "Sprint 1", "exploratory_queries.sql", "notebooks/exploratory_queries.sql"),
    ("D-05", "Sprint 2", "financial_ratios table", "data/nifty100.db"),
    ("D-06", "Sprint 2", "capital_allocation.csv", "output/capital_allocation.csv"),
    ("D-07", "Sprint 3", "screener_output.xlsx", "output/screener_output.xlsx"),
    ("D-08", "Sprint 3", "screener_config.yaml", "config/screener_config.yaml"),
    ("D-09", "Sprint 3", "peer_comparison.xlsx", "output/peer_comparison.xlsx"),
    ("D-10", "Sprint 3", "92 Radar Charts", "reports/radar_charts"),
    ("D-11", "Sprint 4", "Streamlit Dashboard", "src/dashboard/app.py"),
    ("D-12", "Sprint 4", "valuation_summary.xlsx", "output/valuation_summary.xlsx"),
    ("D-13", "Sprint 5", "cashflow_intelligence.xlsx", "output/cashflow_intelligence.xlsx"),
    ("D-14", "Sprint 5", "pros_cons_generated.csv", "output/pros_cons_generated.csv"),
    ("D-15", "Sprint 5", "analysis_parsed.csv", "output/analysis_parsed.csv"),
    ("D-16", "Sprint 5", "92 Company Tearsheets", "reports/tearsheets"),
    ("D-17", "Sprint 5", "11 Sector Reports", "reports/sector"),
    ("D-18", "Sprint 5", "Portfolio Summary PDF", "reports/portfolio/portfolio_summary.pdf"),
    ("D-19", "Sprint 6", "cluster_labels.csv", "output/cluster_labels.csv"),
    ("D-20", "Sprint 6", "FastAPI Server", "src/api/main.py"),
    ("D-21", "Sprint 6", "pytest_report.html", "reports/pytest_report.html"),
    ("D-22", "Sprint 6", "analyst_guide.pdf", "docs/analyst_guide.pdf"),
    ("D-23", "Sprint 6", "acceptance_checklist.pdf", "docs/acceptance_checklist.pdf"),
]


def check_deliverable(path_str: str) -> tuple:
    """Returns (present: bool, detail: str)."""
    p = Path(path_str)
    if p.is_dir():
        n = len(list(p.glob("*")))
        return n > 0, f"{n} files"
    if p.exists():
        size_kb = p.stat().st_size / 1024
        return True, f"{size_kb:.0f} KB"
    return False, "not found"


def build_checklist(out_path: str = "docs/acceptance_checklist.pdf"):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(out_path, pagesize=A4, topMargin=1.5 * cm,
                            bottomMargin=1.5 * cm, leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    elements = []

    title_style = ParagraphStyle("title", parent=styles["Title"], textColor=NAVY, fontSize=18)
    elements.append(Paragraph("Nifty 100 Financial Intelligence Platform", title_style))
    elements.append(Paragraph("Acceptance Checklist — Final Sign-Off (Day 45)", styles["Heading2"]))
    elements.append(Paragraph(f"Generated: {date.today().isoformat()}", styles["Normal"]))
    elements.append(Spacer(1, 0.5 * cm))

    header = ["ID", "Sprint", "Deliverable", "Location", "Status", "Detail"]
    rows = [header]

    n_present = 0
    for did, sprint, name, path in DELIVERABLES:
        present, detail = check_deliverable(path)
        n_present += present
        status = "Present" if present else "Missing"
        rows.append([did, sprint, Paragraph(name, CELL), Paragraph(path, CELL), status, detail])

    table = Table(rows, colWidths=[1.3 * cm, 1.8 * cm, 4.5 * cm, 5 * cm, 2.2 * cm, 2.5 * cm],
                 repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    for i, (did, sprint, name, path) in enumerate(DELIVERABLES, start=1):
        present, _ = check_deliverable(path)
        style_cmds.append(("BACKGROUND", (4, i), (4, i), GREEN if present else RED))
    table.setStyle(TableStyle(style_cmds))
    elements.append(table)

    elements.append(Spacer(1, 0.6 * cm))
    summary_style = ParagraphStyle("summary", parent=styles["Normal"], fontSize=11)
    elements.append(Paragraph(
        f"<b>{n_present} / {len(DELIVERABLES)} deliverables present.</b>", summary_style))
    elements.append(Spacer(1, 1 * cm))

    elements.append(Paragraph("Sign-Off", styles["Heading3"]))
    sign_table = Table(
        [["Role", "Name", "Signature", "Date"],
         ["Project Manager / Team Lead", "", "", ""],
         ["Data Engineering Lead", "", "", ""],
         ["Analytics Lead", "", "", ""],
         ["QA Lead", "", "", ""]],
        colWidths=[5 * cm, 4 * cm, 4 * cm, 3 * cm],
    )
    sign_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
    ]))
    elements.append(sign_table)

    doc.build(elements)
    return n_present, len(DELIVERABLES)


if __name__ == "__main__":
    n_present, total = build_checklist()
    print(f"acceptance_checklist.pdf generated: {n_present}/{total} deliverables present")
