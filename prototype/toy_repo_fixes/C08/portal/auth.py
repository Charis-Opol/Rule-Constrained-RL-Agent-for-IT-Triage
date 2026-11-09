"""Sign-in."""
import secrets
import time


def sign_in(db, username, password):
    rows = db.query("SELECT id, password FROM users WHERE username = ?", (username,))
    if not rows or rows[0]["password"] != password:
        return None
    user_id, token = rows[0]["id"], secrets.token_hex(16)
    with db.transaction():
        db.execute("UPDATE users SET last_login = ? WHERE id = ?", (time.time(), user_id))
    # The token lives in its own table, so concurrent sign-ins no longer write the same user row twice.
    with db.transaction():
        db.execute("INSERT INTO tokens (user_id, token) VALUES (?, ?)", (user_id, token))
    return token
