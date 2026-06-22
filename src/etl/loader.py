"""Excel loader for the NIFTY 100 ETL pipeline (Sprint 1, Day 2).

Core files have metadata in row 0 and real headers in row 1 (header=1).
Supplementary files have headers in row 0 (header=0).
company_id / id is normalised to an upper-case stripped ticker on every load.
"""

from pathlib import Path
import pandas as pd

from .normaliser import normalize_year, normalize_ticker

# Core files: metadata row 0, header row 1
CORE_FILES = [
    "companies.xlsx", "profitandloss.xlsx", "balancesheet.xlsx",
    "cashflow.xlsx", "analysis.xlsx", "documents.xlsx", "prosandcons.xlsx",
]
# Supplementary files: header row 0
SUPP_FILES = [
    "sectors.xlsx", "stock_prices.xlsx", "market_cap.xlsx",
    "financial_ratios.xlsx", "peer_groups.xlsx",
]


def _normalise_common(df: pd.DataFrame) -> pd.DataFrame:
    """Apply ticker + year normalisation to whichever columns are present."""
    # Ticker lives in 'company_id' (child tables) or 'id' (companies master)
    if "company_id" in df.columns:
        df["company_id"] = df["company_id"].map(normalize_ticker)
    if "id" in df.columns and "company_id" not in df.columns:
        # companies.xlsx: 'id' IS the ticker (string). Other tables: 'id' is a row number (int) — skip those.
        if not pd.api.types.is_numeric_dtype(df["id"]):
            df["id"] = df["id"].map(normalize_ticker)

    # Year columns: 'year' (financials) — standardise to YYYY-MM
    if "year" in df.columns:
        df["year"] = df["year"].map(normalize_year)
    return df


def load_excel(path: str | Path, is_core: bool) -> pd.DataFrame:
    """Load one Excel file with the correct header row and normalise key fields."""
    header = 1 if is_core else 0
    df = pd.read_excel(path, header=header)
    # tidy column names
    df.columns = [str(c).strip() for c in df.columns]
    df = _normalise_common(df)
    return df


def load_all(raw_dir: str | Path, supp_dir: str | Path) -> dict[str, pd.DataFrame]:
    """Load every core + supplementary file into a dict keyed by table name."""
    raw_dir, supp_dir = Path(raw_dir), Path(supp_dir)
    frames: dict[str, pd.DataFrame] = {}

    for fname in CORE_FILES:
        fpath = raw_dir / fname
        if fpath.exists():
            table = fname.replace(".xlsx", "")
            frames[table] = load_excel(fpath, is_core=True)
            print(f"loaded core {fname}: {frames[table].shape}")
        else:
            print(f"MISSING core file: {fname}")

    for fname in SUPP_FILES:
        fpath = supp_dir / fname
        if fpath.exists():
            table = fname.replace(".xlsx", "")
            frames[table] = load_excel(fpath, is_core=False)
            print(f"loaded supp {fname}: {frames[table].shape}")
        else:
            print(f"MISSING supplementary file: {fname}")

    return frames


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    raw = os.getenv("DATA_RAW", "data/raw")
    supp = os.getenv("DATA_SUPPORTING", "data/supporting")
    tables = load_all(raw, supp)
    print(f"\nLoaded {len(tables)} tables total.")
