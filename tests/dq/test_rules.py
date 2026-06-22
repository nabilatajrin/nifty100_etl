"""Tests that each DQ rule triggers correctly on crafted violation records."""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from etl.validator import validate


def _base_tables():
    """Minimal clean tables that pass all rules; tests mutate copies."""
    companies = pd.DataFrame({"id": ["TCS", "INFY"]})
    years = ["2020-03", "2021-03", "2022-03", "2023-03", "2024-03"]
    pl = pd.DataFrame({
        "company_id": ["TCS"] * 5, "year": years,
        "sales": [100, 110, 120, 130, 140],
        "operating_profit": [25, 27, 30, 32, 35],
        "opm_percentage": [25.0, 24.5, 25.0, 24.6, 25.0],
        "tax_percentage": [25, 25, 25, 25, 25],
        "dividend_payout": [40, 40, 40, 40, 40],
        "eps": [10, 11, 12, 13, 14],
        "net_profit": [20, 22, 24, 26, 28],
    })
    bs = pd.DataFrame({
        "company_id": ["TCS"] * 5, "year": years,
        "total_assets": [1000] * 5, "total_liabilities": [1000] * 5,
        "fixed_assets": [200] * 5,
    })
    cf = pd.DataFrame({
        "company_id": ["TCS"] * 5, "year": years,
        "operating_activity": [30] * 5, "investing_activity": [-10] * 5,
        "financing_activity": [-15] * 5, "net_cash_flow": [5] * 5,
    })
    # INFY also needs 5 years to satisfy DQ-16
    for df in (pl, bs, cf):
        infy = df.copy(); infy["company_id"] = "INFY"
        df_all = pd.concat([df, infy], ignore_index=True)
        df.drop(df.index, inplace=True)
        for c in df_all.columns:
            df[c] = df_all[c]
    return {"companies": companies, "profitandloss": pl,
            "balancesheet": bs, "cashflow": cf}


def _issues(failures, severity=None, field_contains=None):
    f = failures
    if severity:
        f = f[f["severity"] == severity]
    if field_contains:
        f = f[f["field"].str.contains(field_contains, na=False)]
    return f


def test_dq01_duplicate_company_pk():
    t = _base_tables()
    t["companies"] = pd.DataFrame({"id": ["TCS", "TCS"]})
    f = validate(t)
    dq01 = f[(f["severity"] == "CRITICAL") & (f["issue"].str.contains("company PK", na=False))]
    assert not dq01.empty

def test_dq02_duplicate_annual_pk():
    t = _base_tables()
    dup = t["profitandloss"].iloc[[0]].copy()
    t["profitandloss"] = pd.concat([t["profitandloss"], dup], ignore_index=True)
    f = validate(t)
    assert not _issues(f, "CRITICAL", "company_id,year").empty

def test_dq03_orphan_fk():
    t = _base_tables()
    orphan = t["profitandloss"].iloc[[0]].copy()
    orphan["company_id"] = "GHOST"
    t["profitandloss"] = pd.concat([t["profitandloss"], orphan], ignore_index=True)
    f = validate(t)
    assert not _issues(f, "CRITICAL", "company_id").empty

def test_dq04_bs_imbalance():
    t = _base_tables()
    t["balancesheet"].loc[0, "total_liabilities"] = 1200  # 20% off
    f = validate(t)
    assert not _issues(f, "WARNING", "total_assets").empty

def test_dq05_opm_mismatch():
    t = _base_tables()
    t["profitandloss"].loc[0, "opm_percentage"] = 80.0  # way off
    f = validate(t)
    assert not _issues(f, "WARNING", "opm_percentage").empty

def test_dq06_zero_sales():
    t = _base_tables()
    t["profitandloss"].loc[0, "sales"] = 0
    f = validate(t)
    assert not _issues(f, "WARNING", "sales").empty

def test_dq07_bad_year():
    t = _base_tables()
    t["profitandloss"].loc[0, "year"] = "PARSE_ERROR"
    f = validate(t)
    assert not _issues(f, "CRITICAL", "year").empty

def test_dq08_bad_ticker():
    t = _base_tables()
    t["companies"] = pd.DataFrame({"id": ["X", "INFY"]})  # 'X' too short
    f = validate(t)
    assert not _issues(f, "CRITICAL", "companies.id").empty

def test_dq09_net_cash_mismatch():
    t = _base_tables()
    t["cashflow"].loc[0, "net_cash_flow"] = 999  # far from CFO+CFI+CFF=5
    f = validate(t)
    assert not _issues(f, "WARNING", "net_cash_flow").empty

def test_dq10_negative_fixed_assets():
    t = _base_tables()
    t["balancesheet"].loc[0, "fixed_assets"] = -50
    f = validate(t)
    assert not _issues(f, "WARNING", "fixed_assets").empty

def test_dq11_tax_out_of_range():
    t = _base_tables()
    t["profitandloss"].loc[0, "tax_percentage"] = 80
    f = validate(t)
    assert not _issues(f, "WARNING", "tax_percentage").empty

def test_dq12_dividend_over_cap():
    t = _base_tables()
    t["profitandloss"].loc[0, "dividend_payout"] = 250
    f = validate(t)
    assert not _issues(f, "WARNING", "dividend_payout").empty

def test_dq14_eps_sign():
    t = _base_tables()
    t["profitandloss"].loc[0, "eps"] = -5  # negative while profit positive
    f = validate(t)
    assert not _issues(f, "WARNING", "eps").empty

def test_dq16_insufficient_coverage():
    t = _base_tables()
    # cut TCS down to 2 years
    pl = t["profitandloss"]
    t["profitandloss"] = pl[~((pl["company_id"] == "TCS") &
                              (pl["year"].isin(["2022-03", "2023-03", "2024-03"])))].copy()
    f = validate(t)
    assert not _issues(f, "WARNING", "coverage").empty

def test_clean_data_minimal_criticals():
    """A clean dataset should produce zero CRITICAL violations."""
    t = _base_tables()
    f = validate(t)
    assert _issues(f, "CRITICAL").empty
