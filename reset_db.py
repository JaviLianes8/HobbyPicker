"""Utility script to reset the application's database."""

from data.activity_dao import ActivityDAO
from infrastructure.db import connect


def reset_database() -> None:
    """Drop existing tables and recreate them."""
    with connect() as conn:
        c = conn.cursor()
        c.execute("DROP TABLE IF EXISTS subitems")
        c.execute("DROP TABLE IF EXISTS activities")
        conn.commit()

    # Creating a DAO will recreate the tables
    ActivityDAO()


if __name__ == "__main__":
    reset_database()
    print("Database reset completed.")
