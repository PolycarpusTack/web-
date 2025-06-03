
"""
A simple test script to check if SQLite3 is working correctly.
"""
import sqlite3

def test_sqlite():
    print(f"SQLite3 version: {sqlite3.sqlite_version}")
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
    cursor.execute("INSERT INTO test (name) VALUES (?)", ("Test User",))
    cursor.execute("SELECT * FROM test")
    print(cursor.fetchall())
    conn.close()
    print("SQLite3 test completed successfully!")

if __name__ == "__main__":
    test_sqlite()
