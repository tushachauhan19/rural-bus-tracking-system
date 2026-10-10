

import sqlite3
import re
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent / "rural_bus.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    with get_connection() as connection:
        # Create tables if they do not already exist.
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS buses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bus_number TEXT NOT NULL UNIQUE,
                route_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                start_location TEXT,
                end_location TEXT
            );

            CREATE TABLE IF NOT EXISTS drivers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE
            );

            CREATE TABLE IF NOT EXISTS routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_name TEXT NOT NULL,
                start_location TEXT NOT NULL,
                end_location TEXT NOT NULL
            );
        """)

        # Add new columns to an existing buses table safely.
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(buses)"
            ).fetchall()
        }

        if "start_location" not in columns:
            connection.execute(
                "ALTER TABLE buses ADD COLUMN start_location TEXT"
            )

        if "end_location" not in columns:
            connection.execute(
                "ALTER TABLE buses ADD COLUMN end_location TEXT"
            )

        # Migrate existing route names, such as
        # "Tehri to Rishikesh", into separate locations.
        buses = connection.execute("""
            SELECT id, route_name, start_location, end_location
            FROM buses
        """).fetchall()

        for bus in buses:
            route_name = bus["route_name"] or ""
            locations = re.split(
                r"\s+to\s+",
                route_name,
                maxsplit=1,
                flags=re.IGNORECASE
            )

            if len(locations) == 2:
                start = locations[0].strip()
                end = locations[1].strip()

                connection.execute("""
                    UPDATE buses
                    SET start_location = COALESCE(
                            NULLIF(start_location, ''), ?
                        ),
                        end_location = COALESCE(
                            NULLIF(end_location, ''), ?
                        )
                    WHERE id = ?
                """, (start, end, bus["id"]))


if __name__ == "__main__":
    initialize_database()
    print("SQLite database initialized successfully!")
    print(f"Database location: {DATABASE_PATH}")
