"""Data access layer for hobby and subitem persistence."""

import os
import random
import sqlite3

from infrastructure.db import get_db_path

DB_PATH = get_db_path()

# Ruta de la base de datos utilizada por la aplicación
# Si la variable de entorno `HOBBYPICKER_DEBUG` está presente se imprime la ruta
if os.environ.get("HOBBYPICKER_DEBUG"):
    print("🧭 Base de datos en uso:", DB_PATH)

class ActivityDAO:
    """High level API for reading and writing hobbies in the database."""

    def __init__(self, db_path: str | None = None):
        """Create a new DAO instance and ensure required tables exist."""
        self.db_path = db_path or DB_PATH
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()

    def _create_tables(self) -> None:
        """Create database tables if they do not already exist."""
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
                        FOREIGN KEY (activity_id) REFERENCES activities(id)
                    )"""
        )
        self.conn.commit()

    def get_all_activities(self):
        """Return all registered hobby activities."""
        return self.conn.execute("SELECT id, name FROM activities").fetchall()

    def get_subitems_by_activity(self, activity_id):
        """Return all subitems linked to a hobby."""
        return self.conn.execute(
            "SELECT id, activity_id, name FROM subitems WHERE activity_id = ?",
            (activity_id,),
        ).fetchall()

    def get_random_with_subitems(self):
        """Return a random activity that has subitems."""
        c = self.conn.cursor()
        c.execute(
            """SELECT a.id, a.name FROM activities a
                     WHERE a.done = 0 AND EXISTS (
                         SELECT 1 FROM subitems s WHERE s.activity_id = a.id
                     )"""
        )
        options = c.fetchall()
        return random.choice(options) if options else None

    def get_random_with_subitems_or_alone(self):
        """Return a random activity regardless of having subitems."""
        c = self.conn.cursor()
        c.execute("SELECT id, name FROM activities WHERE done = 0")
        options = c.fetchall()
        return random.choice(options) if options else None

    def get_least_used_activity(self):
        """Return an activity that has been accepted the least."""
        c = self.conn.cursor()
        c.execute(
            "SELECT id, name, accepted_count FROM activities ORDER BY accepted_count ASC"
        )
        options = c.fetchall()
        return (
            random.choice([x for x in options if x[2] == options[0][2]])
            if options
            else None
        )

    def increment_accepted_count(self, activity_id):
        """Increase accepted count for a hobby."""
        self.conn.execute(
            "UPDATE activities SET accepted_count = accepted_count + 1 WHERE id = ?",
            (activity_id,),
        )
        self.conn.commit()

    def accept_activity(self, activity_id):
        """Mark an activity as done."""
        self.conn.execute("UPDATE activities SET done = 1 WHERE id = ?", (activity_id,))
        self.conn.commit()

    def insert_activity(self, name):
        """Insert a new hobby and return its id."""
        c = self.conn.cursor()
        c.execute("INSERT OR IGNORE INTO activities (name) VALUES (?)", (name,))
        self.conn.commit()
        c.execute("SELECT id FROM activities WHERE name = ?", (name,))
        return c.fetchone()[0]

    def insert_subitem(self, activity_id, name):
        """Add a subitem to an existing hobby."""
        self.conn.execute(
            "INSERT INTO subitems (activity_id, name) VALUES (?, ?)",
            (activity_id, name),
        )
        self.conn.commit()

    def delete_subitem(self, subitem_id):
        """Remove a subitem from the database."""
        self.conn.execute("DELETE FROM subitems WHERE id = ?", (subitem_id,))
        self.conn.commit()

    def delete_activity(self, activity_id):
        """Remove an activity and all its subitems."""
        self.conn.execute("DELETE FROM subitems WHERE activity_id = ?", (activity_id,))
        self.conn.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
        self.conn.commit()

    def get_all_with_counts(self):
        """Return all activities along with their accepted counts."""
        return self.conn.execute(
            "SELECT id, name, accepted_count FROM activities"
        ).fetchall()

    def update_subitem(self, subitem_id, new_name):
        """Update the name of a subitem."""
        self.conn.execute(
            "UPDATE subitems SET name = ? WHERE id = ?",
            (new_name, subitem_id),
        )
        self.conn.commit()
