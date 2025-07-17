"""Utility helpers for interacting with the SQLite database."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager

DEFAULT_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "hobbypicker.db")
)


def get_db_path() -> str:
    """Return the path to the SQLite database file."""

    return os.environ.get("HOBBYPICKER_DB", DEFAULT_DB_PATH)


@contextmanager
def connect(db_path: str | None = None) -> sqlite3.Connection:
    """Context manager that yields a SQLite connection and closes it on exit."""

    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    try:
        yield conn
    finally:
        conn.close()
