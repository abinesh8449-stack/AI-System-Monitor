"""
Database Inspector Utility for AI-Powered System Monitor
Usage:
    python view_db.py
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "monitoring.db"

def inspect_database():
    if not DB_PATH.exists():
        print(f"Database not found at: {DB_PATH}")
        return

    print("=" * 70)
    print(f" DATABASE LOCATION: {DB_PATH}")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row["name"] for row in cursor.fetchall()]

    print(f"\nDiscovered {len(tables)} tables:\n")
    for idx, table in enumerate(tables, 1):
        cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
        count = cursor.fetchone()["count"]

        cursor.execute(f"PRAGMA table_info({table});")
        columns = [col["name"] for col in cursor.fetchall()]

        print(f" {idx}. TABLE: {table.upper()} ({count} records)")
        print(f"    Columns: {', '.join(columns)}")

        # Print latest 2 sample rows
        cursor.execute(f"SELECT * FROM {table} ORDER BY 1 DESC LIMIT 2")
        rows = cursor.fetchall()
        if rows:
            print(f"    Latest Sample:")
            for r in rows:
                row_dict = dict(r)
                # truncate long strings for clean terminal display
                truncated = {k: (str(v)[:45] + '...' if len(str(v)) > 45 else v) for k, v in row_dict.items()}
                print(f"      -> {truncated}")
        print("-" * 70)

    conn.close()

if __name__ == "__main__":
    inspect_database()
