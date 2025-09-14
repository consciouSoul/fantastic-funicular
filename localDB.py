import sqlite3
import os

os.makedirs("data", exist_ok=True)

class LocalSQLite:
    def __init__(self, ver:str):
        self.conn = sqlite3.connect(f"data/submissions_{ver}.db")
        self.cur = self.conn.cursor()
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY,
            code TEXT NOT NULL
        )
        """)
        self.conn.commit()

    def storeCode(self, id, code):
        self.cur.execute("INSERT OR REPLACE INTO submissions (id, code) VALUES (?, ?)", (id, code))
        self.conn.commit()

    def getCode(self, id):
        self.cur.execute("SELECT code FROM submissions WHERE id = ?", (id,))
        row = self.cur.fetchone()
        return row[0] if row else None

    def close(self):
        self.conn.close()

