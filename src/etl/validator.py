"""Schema validator — 16 data-quality rules for the NIFTY 100 ETL pipeline.

Each rule appends violations to a list of dicts with:
  company_id, year, field, issue, severity  (CRITICAL / WARNING / INFO)
Results are written to output/validation_failures.csv.
"""

from pathlib import Path
import pandas as pd

from .normaliser import normalize_year, PARSE_ERROR

CRITICAL, WARNING, INFO = "CRITICAL", "WARNING", "INFO"


def _add(rows, company_id, year, field, issue, severity):
    rows.append({
        "company_id": company_id, "year": year,
        "field": field, "issue": issue, "severity": severity,
    })


def validate(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Run all 16 DQ rules on the loaded tables; return a failures DataFrame."""
    rows: list[dict] = []

    companies = tables.get("companies")
    pl = tables.get("profitandloss")
    bs = tables.get("balancesheet")
    cf = tables.get("cashflow")
    docs = tables.get("documents")

    valid_ids = set(companies["id"]) if companies is not None else set()

    # DQ-01 Company PK uniqueness (CRITICAL)
    if companies is not None:
        if len(companies) != companies["id"].nunique():
            dupes = companies[companies["id"].duplicated(keep=False)]["id"].unique()
            for cid in dupes:
                _add(rows, cid, None, "id", "Duplicate company PK", CRITICAL)

    # DQ-02 Annual PK uniqueness (company_id, year) (CRITICAL)
    for name, df in [("profitandloss", pl), ("balancesheet", bs), ("cashflow", cf)]:
        if df is not None and {"company_id", "year"}.issubset(df.columns):
            dup = df[df.duplicated(subset=["company_id", "year"], keep=False)]
            for _, r in dup.iterrows():
                _add(rows, r["company_id"], r["year"], f"{name}.(company_id,year)",
                     "Duplicate annual PK", CRITICAL)

    # DQ-03 FK integrity — child company_id must exist in companies (CRITICAL)
    for name, df in [("profitandloss", pl), ("balancesheet", bs), ("cashflow", cf)]:
        if df is not None and "company_id" in df.columns and valid_ids:
            orphans = df[~df["company_id"].isin(valid_ids)]
            for _, r in orphans.iterrows():
                _add(rows, r["company_id"], r.get("year"), f"{name}.company_id",
                     "Orphan FK — no matching company", CRITICAL)

    # DQ-04 Balance Sheet balance |assets - liabilities| / assets < 1% (WARNING)
    if bs is not None and {"total_assets", "total_liabilities"}.issubset(bs.columns):
        a = pd.to_numeric(bs["total_assets"], errors="coerce")
        l = pd.to_numeric(bs["total_liabilities"], errors="coerce")
        diff = (a - l).abs() / a.replace(0, pd.NA)
        for idx in bs.index[diff > 0.01]:
            _add(rows, bs.at[idx, "company_id"], bs.at[idx, "year"],
                 "balancesheet.total_assets", "BS does not balance >1%", WARNING)

    # DQ-05 OPM cross-check |opm - op/sales*100| < 1 (WARNING)
    if pl is not None and {"opm_percentage", "operating_profit", "sales"}.issubset(pl.columns):
        op = pd.to_numeric(pl["operating_profit"], errors="coerce")
        sales = pd.to_numeric(pl["sales"], errors="coerce")
        opm = pd.to_numeric(pl["opm_percentage"], errors="coerce")
        computed = op / sales.replace(0, pd.NA) * 100
        for idx in pl.index[(opm - computed).abs() > 1.0]:
            _add(rows, pl.at[idx, "company_id"], pl.at[idx, "year"],
                 "profitandloss.opm_percentage", "OPM mismatch >1%", WARNING)

    # DQ-06 Positive sales (WARNING)
    if pl is not None and "sales" in pl.columns:
        sales = pd.to_numeric(pl["sales"], errors="coerce")
        for idx in pl.index[sales <= 0]:
            _add(rows, pl.at[idx, "company_id"], pl.at[idx, "year"],
                 "profitandloss.sales", "Sales <= 0", WARNING)

    # DQ-07 Year format — must be YYYY-MM after normalisation (CRITICAL)
    for name, df in [("profitandloss", pl), ("balancesheet", bs), ("cashflow", cf)]:
        if df is not None and "year" in df.columns:
            bad = df[~df["year"].astype(str).str.fullmatch(r"\d{4}-\d{2}")]
            for _, r in bad.iterrows():
                _add(rows, r["company_id"], r["year"], f"{name}.year",
                     "Year not YYYY-MM", CRITICAL)

    # DQ-08 Ticker format — length 2..12 (CRITICAL)
    if companies is not None:
        for cid in companies["id"]:
            if not (isinstance(cid, str) and 2 <= len(cid) <= 12):
                _add(rows, cid, None, "companies.id",
                     "Ticker length out of range", CRITICAL)

    # DQ-09 Net cash check |net - (CFO+CFI+CFF)| <= 10 (WARNING)
    if cf is not None and {"operating_activity", "investing_activity",
                           "financing_activity", "net_cash_flow"}.issubset(cf.columns):
        s = (pd.to_numeric(cf["operating_activity"], errors="coerce")
             + pd.to_numeric(cf["investing_activity"], errors="coerce")
             + pd.to_numeric(cf["financing_activity"], errors="coerce"))
        net = pd.to_numeric(cf["net_cash_flow"], errors="coerce")
        for idx in cf.index[(net - s).abs() > 10]:
            _add(rows, cf.at[idx, "company_id"], cf.at[idx, "year"],
                 "cashflow.net_cash_flow", "Net cash != CFO+CFI+CFF (>10 Cr)", WARNING)

    # DQ-10 Non-negative fixed assets (WARNING)
    if bs is not None and "fixed_assets" in bs.columns:
        fa = pd.to_numeric(bs["fixed_assets"], errors="coerce")
        for idx in bs.index[fa < 0]:
            _add(rows, bs.at[idx, "company_id"], bs.at[idx, "year"],
                 "balancesheet.fixed_assets", "Negative fixed assets", WARNING)

    # DQ-11 Tax rate range 0..60 (WARNING)
    if pl is not None and "tax_percentage" in pl.columns:
        tax = pd.to_numeric(pl["tax_percentage"], errors="coerce")
        for idx in pl.index[(tax < 0) | (tax > 60)]:
            _add(rows, pl.at[idx, "company_id"], pl.at[idx, "year"],
                 "profitandloss.tax_percentage", "Tax rate outside 0-60%", WARNING)

    # DQ-12 Dividend payout cap <= 200 (WARNING)
    if pl is not None and "dividend_payout" in pl.columns:
        dp = pd.to_numeric(pl["dividend_payout"], errors="coerce")
        for idx in pl.index[dp > 200]:
            _add(rows, pl.at[idx, "company_id"], pl.at[idx, "year"],
                 "profitandloss.dividend_payout", "Dividend payout >200%", WARNING)

    # DQ-13 URL validity — flag obviously missing URLs (WARNING)
    # (Network HEAD checks are slow/unreliable; flag null/blank URLs here.)
    if docs is not None and "Annual_Report" in docs.columns:
        for idx in docs.index[docs["Annual_Report"].isna()
                              | (docs["Annual_Report"].astype(str).str.strip() == "")]:
            _add(rows, docs.at[idx, "company_id"], docs.at[idx, "Year"]
                 if "Year" in docs.columns else None,
                 "documents.Annual_Report", "Missing annual report URL", WARNING)

    # DQ-14 EPS sign consistency — eps>0 if net_profit>0 (WARNING)
    if pl is not None and {"eps", "net_profit"}.issubset(pl.columns):
        eps = pd.to_numeric(pl["eps"], errors="coerce")
        npft = pd.to_numeric(pl["net_profit"], errors="coerce")
        for idx in pl.index[(npft > 0) & (eps <= 0)]:
            _add(rows, pl.at[idx, "company_id"], pl.at[idx, "year"],
                 "profitandloss.eps", "EPS<=0 while net_profit>0", WARNING)

    # DQ-15 BSE/ASE balance — strict assets == liabilities (INFO)
    if bs is not None and {"total_assets", "total_liabilities"}.issubset(bs.columns):
        a = pd.to_numeric(bs["total_assets"], errors="coerce")
        l = pd.to_numeric(bs["total_liabilities"], errors="coerce")
        for idx in bs.index[a != l]:
            _add(rows, bs.at[idx, "company_id"], bs.at[idx, "year"],
                 "balancesheet", "Assets != liabilities (strict)", INFO)

    # DQ-16 Coverage check — each company >=5 yrs of P&L/BS/CF (WARNING)
    for name, df in [("profitandloss", pl), ("balancesheet", bs), ("cashflow", cf)]:
        if df is not None and {"company_id", "year"}.issubset(df.columns):
            counts = df.groupby("company_id")["year"].nunique()
            for cid, n in counts.items():
                if n < 5:
                    _add(rows, cid, None, f"{name}.coverage",
                         f"Only {n} yrs of {name} (<5)", WARNING)

    return pd.DataFrame(rows, columns=["company_id", "year", "field", "issue", "severity"])


def run_and_save(tables: dict[str, pd.DataFrame],
                 out_path: str | Path = "output/validation_failures.csv") -> pd.DataFrame:
    """Run validation and write results to CSV. Returns the failures DataFrame."""
    failures = validate(tables)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    failures.to_csv(out_path, index=False)

    counts = failures["severity"].value_counts().to_dict() if not failures.empty else {}
    print(f"Validation complete: {len(failures)} issues found.")
    print(f"  CRITICAL: {counts.get('CRITICAL', 0)}")
    print(f"  WARNING:  {counts.get('WARNING', 0)}")
    print(f"  INFO:     {counts.get('INFO', 0)}")
    print(f"  saved -> {out_path}")
    return failures


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from .loader import load_all

    load_dotenv()
    raw = os.getenv("DATA_RAW", "data/raw")
    supp = os.getenv("DATA_SUPPORTING", "data/supporting")
    tables = load_all(raw, supp)
    run_and_save(tables)
