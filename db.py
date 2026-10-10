import sqlite3
import os

from dotenv import load_dotenv
load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                stripe_customer_id TEXT,
                subscription_id TEXT,
                status TEXT DEFAULT 'none'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY
            )
        """)


def ensure_user(user_id):
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))


def has_active_plan(user_id):
    if os.environ.get("DEV_BYPASS", "false").lower() == "true":
        return True
    with get_conn() as conn:
        row = conn.execute(
            "SELECT status FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return bool(row and row["status"] == "active")


def get_status(user_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT status FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return row["status"] if row else "none"


def event_seen(event_id):
    """Returns True if already processed; otherwise records it and returns False."""
    with get_conn() as conn:
        try:
            conn.execute("INSERT INTO events (id) VALUES (?)", (event_id,))
            return False
        except sqlite3.IntegrityError:
            return True


def activate_user(user_id, customer_id, subscription_id):
    ensure_user(user_id)
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET stripe_customer_id=?, subscription_id=?, status='active' WHERE id=?",
            (customer_id, subscription_id, user_id),
        )


def set_status_by_subscription(subscription_id, status):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET status=? WHERE subscription_id=?",
            (status, subscription_id),
        )

init_db()