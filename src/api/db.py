"""Shared DB connection + app metadata for the API (Sprint 6, Day 38).

Kept separate from main.py so routers can import it without a circular
dependency (main.py imports the routers; routers must not import main.py).
"""

import os
import sqlite3
import time

APP_VERSION = "1.0.0"
START_TIME = time.time()


def get_db_path() -> str:
    return os.getenv("DB_PATH", "data/nifty100.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn
