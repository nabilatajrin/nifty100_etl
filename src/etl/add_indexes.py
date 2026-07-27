"""SQLite query optimisation — add indexes (Sprint 6, Day 43).

Adds indexes on company_id and year for the large time-series tables, and
measures a representative query's speed before/after.

Run:  python -m src.etl.add_indexes
"""

import os
import sqlite3
import time

INDEX_TABLES = ["profitandloss", "balancesheet", "cashflow", "financial_ratios",
                "stock_prices", "market_cap"]


def add_indexes(conn: sqlite3.Connection) -> list:
    """Creates (company_id) and (company_id, year) indexes where the columns
    exist. Returns the list of index names created."""
    created = []
    for table in INDEX_TABLES:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
        if not cols:
            continue  # table doesn't exist in this build

        if "company_id" in cols:
            idx_name = f"idx_{table}_company_id"
            conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}(company_id)")
            created.append(idx_name)

        if "company_id" in cols and "year" in cols:
            idx_name2 = f"idx_{table}_company_year"
            conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name2} ON {table}(company_id, year)")
            created.append(idx_name2)

    conn.commit()
    return created


def time_query(conn: sqlite3.Connection, sql: str, params: tuple = (), n_runs: int = 20) -> float:
    """Average time (ms) of running the same query n_runs times."""
    start = time.perf_counter()
    for _ in range(n_runs):
        conn.execute(sql, params).fetchall()
    elapsed = time.perf_counter() - start
    return (elapsed / n_runs) * 1000


def main():
    db = os.getenv("DB_PATH", "data/nifty100.db")
    conn = sqlite3.connect(db)

    test_sql = "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year"
    before_ms = time_query(conn, test_sql, ("TCS",))
    print(f"Query time BEFORE indexing: {before_ms:.3f} ms/run")

    created = add_indexes(conn)
    print(f"\nIndexes created/confirmed: {len(created)}")
    for idx in created:
        print(f"  {idx}")

    after_ms = time_query(conn, test_sql, ("TCS",))
    print(f"\nQuery time AFTER indexing: {after_ms:.3f} ms/run")

    if before_ms > 0:
        pct = (before_ms - after_ms) / before_ms * 100
        print(f"Change: {pct:+.1f}%")

    conn.close()


if __name__ == "__main__":
    main()
