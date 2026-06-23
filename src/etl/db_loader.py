"""Build nifty100.db from schema.sql and load cleaned data (Sprint 1, Day 4-5).

Cleaning applied at load time so the DB ends up with zero CRITICAL issues:
  - drop rows with unparseable year (PARSE_ERROR / not YYYY-MM)
  - deduplicate (company_id, year), keeping the last occurrence
  - drop orphan rows whose company_id is not in companies
Writes output/load_audit.csv with per-table row counts and rejections.
"""

from pathlib import Path
import sqlite3
import time
import re
import pandas as pd

from .loader import load_all

YEAR_RE = re.compile(r"^\d{4}-\d{2}$")

# Map loaded table name -> target DB table + which columns the table keeps.
# Time-series tables have a (company_id, year) PK and get deduped.
TIMESERIES = {"profitandloss", "balancesheet", "cashflow",
              "financial_ratios", "market_cap"}
# Tables keyed by company_id only
COMPANY_KEYED = {"sectors"}


def _audit_row(table, rows_in, rows_out, rejected, runtime):
    return {"table": table, "rows_in": rows_in, "rows_out": rows_out,
            "rejected": rejected, "runtime_s": round(runtime, 3)}


def clean_table(name: str, df: pd.DataFrame, valid_ids: set) -> tuple[pd.DataFrame, int]:
    """Apply year/dedup/orphan cleaning. Returns (clean_df, rejected_count)."""
    start_rows = len(df)
    df = df.copy()

    # Drop orphan FK rows (company_id not in companies) — skip the companies table itself
    if "company_id" in df.columns and valid_ids:
        df = df[df["company_id"].isin(valid_ids)]

    # Year cleaning for tables that have a year column
    if "year" in df.columns:
        df = df[df["year"].astype(str).str.match(YEAR_RE)]

    # Deduplicate time-series tables on (company_id, year), keep last
    if name in TIMESERIES and {"company_id", "year"}.issubset(df.columns):
        df = df.drop_duplicates(subset=["company_id", "year"], keep="last")
    elif name in COMPANY_KEYED and "company_id" in df.columns:
        df = df.drop_duplicates(subset=["company_id"], keep="last")

    rejected = start_rows - len(df)
    return df, rejected


def build_database(tables: dict[str, pd.DataFrame],
                   db_path: str | Path = "data/nifty100.db",
                   schema_path: str | Path = "db/schema.sql",
                   audit_path: str | Path = "output/load_audit.csv") -> None:
    db_path, schema_path, audit_path = Path(db_path), Path(schema_path), Path(audit_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    if db_path.exists():
        db_path.unlink()  # fresh build

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")

    # Create the schema
    conn.executescript(schema_path.read_text())
    print(f"Schema created in {db_path}")

    valid_ids = set(tables["companies"]["id"]) if "companies" in tables else set()

    # Load companies FIRST (parent table), then the rest
    load_order = ["companies", "sectors", "profitandloss", "balancesheet",
                  "cashflow", "financial_ratios", "market_cap", "stock_prices",
                  "analysis", "documents", "prosandcons", "peer_groups"]

    audit = []
    for name in load_order:
        if name not in tables:
            continue
        t0 = time.time()
        df = tables[name]
        rows_in = len(df)

        if name == "companies":
            clean, rejected = df.copy(), 0
        else:
            clean, rejected = clean_table(name, df, valid_ids)

        # Only keep columns that exist in the DB table to avoid insert errors
        cols_in_db = [r[1] for r in conn.execute(f"PRAGMA table_info({name})")]
        keep = [c for c in clean.columns if c in cols_in_db]
        clean = clean[keep]

        clean.to_sql(name, conn, if_exists="append", index=False)
        runtime = time.time() - t0
        audit.append(_audit_row(name, rows_in, len(clean), rejected, runtime))
        print(f"  {name}: in={rows_in} out={len(clean)} rejected={rejected}")

    conn.commit()

    # FK integrity check
    fk_problems = conn.execute("PRAGMA foreign_key_check;").fetchall()
    print(f"\nForeign key check: {len(fk_problems)} problems")

    # companies count check
    n_comp = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    print(f"companies row count: {n_comp}")

    conn.close()

    pd.DataFrame(audit).to_csv(audit_path, index=False)
    print(f"\nLoad audit saved -> {audit_path}")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    raw = os.getenv("DATA_RAW", "data/raw")
    supp = os.getenv("DATA_SUPPORTING", "data/supporting")
    db = os.getenv("DB_PATH", "data/nifty100.db")

    tables = load_all(raw, supp)
    build_database(tables, db_path=db)
