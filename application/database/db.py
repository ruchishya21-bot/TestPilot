import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE_PATH = BASE_DIR / "application" / "database" / "testpilot.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():

    connection = get_db_connection()

    schema_path = BASE_DIR / "application" / "database" / "schema.sql"

    with open(schema_path, "r", encoding="utf-8") as file:
        connection.executescript(file.read())

    connection.commit()
    connection.close()