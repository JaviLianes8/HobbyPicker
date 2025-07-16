import sqlite3
import random
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "hobbypicker.db"))
DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "hobbypicker.db")
)

# Ruta de la base de datos utilizada por la aplicación
# Si la variable de entorno `HOBBYPICKER_DEBUG` está presente se imprime la ruta
if os.environ.get("HOBBYPICKER_DEBUG"):
    print("🧭 Base de datos en uso:", DB_PATH)
class ActivityDAO:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self._create_tables()

    def _create_tables(self):
        c = self.conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS activities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE,
                        done INTEGER DEFAULT 0,
                        accepted_count INTEGER DEFAULT 0
                    )""")
        c.execute("""CREATE TABLE IF NOT EXISTS subitems (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        activity_id INTEGER,
                        name TEXT,
                        FOREIGN KEY (activity_id) REFERENCES activities(id)
                    )""")
        self.conn.commit()

    def get_all_activities(self):
        return self.conn.execute("SELECT id, name FROM activities").fetchall()

    def get_subitems_by_activity(self, activity_id):
        return self.conn.execute(
            "SELECT id, activity_id, name FROM subitems WHERE activity_id = ?", (activity_id,)
        ).fetchall()

    def get_random_with_subitems(self):
        c = self.conn.cursor()
        c.execute("""SELECT a.id, a.name FROM activities a
                     WHERE a.done = 0 AND EXISTS (
                         SELECT 1 FROM subitems s WHERE s.activity_id = a.id
                     )""")
        options = c.fetchall()
        return random.choice(options) if options else None

    def get_random_with_subitems_or_alone(self):
        c = self.conn.cursor()
        c.execute("SELECT id, name FROM activities WHERE done = 0")
        options = c.fetchall()
        return random.choice(options) if options else None

    def get_least_used_activity(self):
        c = self.conn.cursor()
        c.execute("SELECT id, name, accepted_count FROM activities ORDER BY accepted_count ASC")
        options = c.fetchall()
        return random.choice([x for x in options if x[2] == options[0][2]]) if options else None

    def increment_accepted_count(self, activity_id):
        self.conn.execute("UPDATE activities SET accepted_count = accepted_count + 1 WHERE id = ?", (activity_id,))
        self.conn.commit()

    def accept_activity(self, activity_id):
        self.conn.execute("UPDATE activities SET done = 1 WHERE id = ?", (activity_id,))
        self.conn.commit()

    def insert_activity(self, name):
        c = self.conn.cursor()
        c.execute("INSERT OR IGNORE INTO activities (name) VALUES (?)", (name,))
        self.conn.commit()
        c.execute("SELECT id FROM activities WHERE name = ?", (name,))
        return c.fetchone()[0]

    def insert_subitem(self, activity_id, name):
        self.conn.execute("INSERT INTO subitems (activity_id, name) VALUES (?, ?)", (activity_id, name))
        self.conn.commit()

    def delete_subitem(self, subitem_id):
        self.conn.execute("DELETE FROM subitems WHERE id = ?", (subitem_id,))
        self.conn.commit()

    def delete_activity(self, activity_id):
        self.conn.execute("DELETE FROM subitems WHERE activity_id = ?", (activity_id,))
        self.conn.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
        self.conn.commit()

    def get_all_with_counts(self):
        return self.conn.execute("SELECT id, name, accepted_count FROM activities").fetchall()
    
    def update_subitem(self, subitem_id, new_name):
        self.conn.execute("UPDATE subitems SET name = ? WHERE id = ?", (new_name, subitem_id))
        self.conn.commit()