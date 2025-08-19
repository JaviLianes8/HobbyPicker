import os
import sqlite3

DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "hobbypicker.db")
)

if os.environ.get("HOBBYPICKER_DEBUG"):
    print("🧭 Base de datos en uso:", DB_PATH)

class Database:
    """Handle database connection and initialization."""

    def __init__(self, path: str = DB_PATH):
        self.conn = sqlite3.connect(path)
        self._create_tables()

    def _create_tables(self) -> None:
        c = self.conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS activities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE,
                        done INTEGER DEFAULT 0,
                        accepted_count INTEGER DEFAULT 0
                    )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS subitems (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        activity_id INTEGER,
                        name TEXT,
                        accepted_count INTEGER DEFAULT 0,
                        FOREIGN KEY (activity_id) REFERENCES activities(id)
                    )"""
        )
        try:
            c.execute(
                "ALTER TABLE subitems ADD COLUMN accepted_count INTEGER DEFAULT 0"
            )
        except sqlite3.OperationalError:
            pass
        self.conn.commit()
