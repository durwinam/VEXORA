import sqlite3
from pathlib import Path

from app.config import settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'admin',
    active INTEGER NOT NULL DEFAULT 1,
    last_login TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL DEFAULT '',
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    phone TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    balance INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    price INTEGER NOT NULL DEFAULT 0,
    volume_gb INTEGER,
    duration_days INTEGER NOT NULL DEFAULT 30,
    devices INTEGER NOT NULL DEFAULT 1,
    badge TEXT DEFAULT '',
    featured INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_code TEXT UNIQUE NOT NULL,
    product_id INTEGER,
    user_id INTEGER,
    customer_name TEXT DEFAULT '',
    amount INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    payment_ref TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    country TEXT DEFAULT '',
    host TEXT DEFAULT '',
    port INTEGER NOT NULL DEFAULT 443,
    status TEXT NOT NULL DEFAULT 'online',
    capacity INTEGER NOT NULL DEFAULT 0,
    used INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'normal',
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT DEFAULT '',
    details TEXT DEFAULT '',
    ip TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def connect() -> sqlite3.Connection:
    path = Path(settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        path,
        timeout=30,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")

    return connection


def initialize() -> None:
    with connect() as db:
        db.executescript(SCHEMA)

        admin = db.execute(
            "SELECT id FROM admins WHERE username = ?",
            (settings.admin_username,),
        ).fetchone()

        if not admin and settings.admin_password_hash:
            db.execute(
                """
                INSERT INTO admins
                (username, password_hash, role)
                VALUES (?, ?, 'owner')
                """,
                (
                    settings.admin_username,
                    settings.admin_password_hash,
                ),
            )

        count = db.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]

        if count == 0:
            db.executemany(
                """
                INSERT INTO products
                (
                    name, description, price, volume_gb,
                    duration_days, devices, badge,
                    featured, sort_order
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        "۱ گیگابایت",
                        "پلن اقتصادی برای استفاده روزمره",
                        11000, 1, 30, 1,
                        "اقتصادی", 0, 1,
                    ),
                    (
                        "۳ گیگابایت",
                        "تعادل مناسب قیمت و حجم",
                        25000, 3, 30, 2,
                        "پرفروش", 1, 2,
                    ),
                    (
                        "۱۰ گیگابایت",
                        "برای مصرف بیشتر و پایدار",
                        65000, 10, 30, 3,
                        "به‌صرفه", 0, 3,
                    ),
                    (
                        "نامحدود",
                        "پلن ویژه برای مصرف بدون نگرانی",
                        120000, None, 30, 5,
                        "ویژه", 0, 4,
                    ),
                ],
            )

        defaults = {
            "site_name": "VEXORA",
            "site_description": "اتصال سریع، امن و پایدار",
            "maintenance": "0",
            "support_enabled": "1",
        }

        for key, value in defaults.items():
            db.execute(
                "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
                (key, value),
            )


def health_check() -> bool:
    with connect() as db:
        db.execute("SELECT 1").fetchone()

    return True
