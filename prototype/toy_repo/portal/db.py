"""A thin wrapper over SQLite that counts statements, so tests can see query patterns."""
import sqlite3
from contextlib import contextmanager


class Database:
    def __init__(self, path=":memory:"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.statements = []

    def query(self, sql, params=()):
        self.statements.append(sql)
        return [dict(row) for row in self.conn.execute(sql, params).fetchall()]

    def execute(self, sql, params=()):
        self.statements.append(sql)
        self.conn.execute(sql, params)

    @contextmanager
    def transaction(self):
        try:
            yield self
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
