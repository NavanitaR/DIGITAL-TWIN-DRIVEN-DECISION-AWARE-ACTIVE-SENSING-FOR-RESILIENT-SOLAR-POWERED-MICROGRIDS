import json
import sqlite3
import threading


class Store:
    def __init__(self, path="microgrid.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.lock = threading.Lock()
        self.conn.executescript(
            "CREATE TABLE IF NOT EXISTS samples(id INTEGER PRIMARY KEY, mode TEXT, data TEXT); CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, data TEXT);"
        )

    def sample(self, mode, data):
        with self.lock:
            self.conn.execute(
                "INSERT INTO samples(mode,data) VALUES(?,?)",
                (mode, json.dumps(data, allow_nan=False)),
            )
            self.conn.commit()

    def event(self, data):
        with self.lock:
            self.conn.execute("INSERT INTO events(data) VALUES(?)", (json.dumps(data),))
            self.conn.commit()

    def history(self, limit=300):
        with self.lock:
            rows = self.conn.execute(
                "SELECT data FROM samples ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [json.loads(row[0]) for row in reversed(rows)]

    def events(self):
        with self.lock:
            return [
                json.loads(r[0])
                for r in self.conn.execute(
                    "SELECT data FROM events ORDER BY id DESC LIMIT 200"
                )
            ]
