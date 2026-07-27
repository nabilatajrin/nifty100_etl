"""Unit tests for the Excel loader (Sprint 6, Day 41) — 10 cases.

Verifies the loader reads correct row counts and column names for both
core (header=1) and supplementary (header=0) files, and that normalisation
is applied on load.
"""

import sys
from pathlib import Path

import pandas as pd
from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from etl.loader import load_excel, load_all


def _make_core_file(path: Path, headers: list, rows: list) -> None:
    """Row 0 = metadata, row 1 = headers (matches real core file structure)."""
    wb = Workbook()
    ws = wb.active
    ws.append(["metadata row — ignored"])
    ws.append(headers)
    for r in rows:
        ws.append(r)
    wb.save(path)


def _make_supp_file(path: Path, headers: list, rows: list) -> None:
    """Row 0 = headers directly (supplementary file structure)."""
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for r in rows:
        ws.append(r)
    wb.save(path)


def test_core_file_correct_row_count(tmp_path):
    f = tmp_path / "companies.xlsx"
    _make_core_file(f, ["id", "company_name"], [["tcs", "TCS"], ["infy", "Infosys"]])
    df = load_excel(f, is_core=True)
    assert len(df) == 2


def test_core_file_correct_columns(tmp_path):
    f = tmp_path / "companies.xlsx"
    _make_core_file(f, ["id", "company_name", "face_value"], [["tcs", "TCS", 1]])
    df = load_excel(f, is_core=True)
    assert list(df.columns) == ["id", "company_name", "face_value"]


def test_core_file_skips_metadata_row(tmp_path):
    f = tmp_path / "companies.xlsx"
    _make_core_file(f, ["id", "company_name"], [["tcs", "TCS"]])
    df = load_excel(f, is_core=True)
    # metadata row must not appear as a data row
    assert "metadata row — ignored" not in df.values


def test_supplementary_file_header_row0(tmp_path):
    f = tmp_path / "sectors.xlsx"
    _make_supp_file(f, ["company_id", "broad_sector"], [["TCS", "IT"], ["INFY", "IT"]])
    df = load_excel(f, is_core=False)
    assert len(df) == 2 and list(df.columns) == ["company_id", "broad_sector"]


def test_ticker_normalised_on_load(tmp_path):
    f = tmp_path / "companies.xlsx"
    _make_core_file(f, ["id", "company_name"], [["  tcs  ", "TCS"]])
    df = load_excel(f, is_core=True)
    assert df["id"].iloc[0] == "TCS"


def test_company_id_normalised_on_load(tmp_path):
    f = tmp_path / "profitandloss.xlsx"
    _make_core_file(
        f, ["id", "company_id", "year", "sales"], [[1, "  tcs  ", "Mar-23", 1000]]
    )
    df = load_excel(f, is_core=True)
    assert df["company_id"].iloc[0] == "TCS"


def test_year_normalised_on_load(tmp_path):
    f = tmp_path / "profitandloss.xlsx"
    _make_core_file(
        f, ["id", "company_id", "year", "sales"], [[1, "TCS", "Mar-23", 1000]]
    )
    df = load_excel(f, is_core=True)
    assert df["year"].iloc[0] == "2023-03"


def test_row_id_not_treated_as_ticker(tmp_path):
    """Numeric 'id' column (row number) in child tables should stay numeric,
    not get run through ticker normalisation."""
    f = tmp_path / "profitandloss.xlsx"
    _make_core_file(
        f, ["id", "company_id", "year", "sales"], [[42, "TCS", "Mar-23", 1000]]
    )
    df = load_excel(f, is_core=True)
    assert df["id"].iloc[0] == 42


def test_load_all_reports_missing_file(tmp_path, capsys):
    raw_dir = tmp_path / "raw"
    supp_dir = tmp_path / "supp"
    raw_dir.mkdir()
    supp_dir.mkdir()
    # no files created -> load_all should report missing, not crash
    tables = load_all(raw_dir, supp_dir)
    captured = capsys.readouterr()
    assert "MISSING" in captured.out
    assert tables == {}


def test_load_all_loads_multiple_files(tmp_path):
    raw_dir = tmp_path / "raw"
    supp_dir = tmp_path / "supp"
    raw_dir.mkdir()
    supp_dir.mkdir()

    _make_core_file(
        raw_dir / "companies.xlsx",
        ["id", "company_name"],
        [["tcs", "TCS"], ["infy", "Infosys"]],
    )
    _make_supp_file(
        supp_dir / "sectors.xlsx", ["company_id", "broad_sector"], [["TCS", "IT"]]
    )

    tables = load_all(raw_dir, supp_dir)
    assert "companies" in tables and len(tables["companies"]) == 2
    assert "sectors" in tables and len(tables["sectors"]) == 1
