"""One test per planted bug; each fails until its fix is applied."""
import datetime

import pytest

from portal import auth, cache, http, payments, results
from portal.db import Database


@pytest.fixture
def db():
    d = Database()
    d.conn.executescript("""
        CREATE TABLE students (id INTEGER PRIMARY KEY, name TEXT, class_id INTEGER);
        CREATE TABLE marks (student_id INTEGER, course TEXT, mark INTEGER);
        CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT,
                            last_login REAL, refresh_token TEXT);
        CREATE TABLE tokens (user_id INTEGER, token TEXT);
        INSERT INTO students VALUES (1, 'Amina', 7), (2, 'Brian', 7), (3, 'Cate', 7);
        INSERT INTO marks VALUES (1, 'CS101', 71), (1, 'CS102', 64), (2, 'CS101', 58), (3, 'CS102', 80);
        INSERT INTO users VALUES (1, 'amina', 'pw', NULL, NULL);
    """)
    d.statements.clear()
    return d


def test_c01_gateway_call_has_a_timeout(monkeypatch):
    seen = {}
    monkeypatch.setattr(http, "post", lambda url, data, timeout=None: seen.setdefault("timeout", timeout) or "ok")
    payments.pay_tuition(1, 100)
    assert seen["timeout"] is not None and seen["timeout"] <= 15


def test_c01_gateway_timeout_is_reported(monkeypatch):
    def slow(url, data, timeout=None):
        raise http.Timeout()
    monkeypatch.setattr(http, "post", slow)
    with pytest.raises(payments.PaymentUnavailable):
        payments.pay_tuition(1, 100)


def test_c04_class_results_use_a_fixed_number_of_queries(db):
    out = results.class_results(db, 7)
    assert out[0] == {"student": "Amina", "marks": {"CS101": 71, "CS102": 64}}
    assert len(out) == 3 and out[2]["marks"] == {"CS102": 80}
    assert len(db.statements) <= 2


def test_c05_values_with_dates_are_cached():
    store = {}
    cache.put(store, "profile:1", {"name": "Amina", "updated": datetime.date(2026, 11, 3)})
    assert cache.get(store, "profile:1") == {"name": "Amina", "updated": "2026-11-03"}


def test_c08_sign_in_writes_the_user_row_once(db):
    token = auth.sign_in(db, "amina", "pw")
    assert token
    user_writes = [s for s in db.statements if s.startswith("UPDATE users")]
    assert len(user_writes) == 1
    assert db.query("SELECT token FROM tokens WHERE user_id = 1") == [{"token": token}]
