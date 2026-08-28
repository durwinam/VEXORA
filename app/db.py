import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .config import settings

SCHEMA = '''
CREATE TABLE IF NOT EXISTS admins(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'owner', active INTEGER NOT NULL DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS panels(id INTEGER PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL, base_url TEXT NOT NULL, username TEXT DEFAULT '', secret_enc TEXT DEFAULT '', verify_tls INTEGER NOT NULL DEFAULT 1, enabled INTEGER NOT NULL DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS plans(id INTEGER PRIMARY KEY, name TEXT NOT NULL, panel_id INTEGER NOT NULL, price INTEGER NOT NULL DEFAULT 0, volume_gb REAL NOT NULL DEFAULT 0, days INTEGER NOT NULL DEFAULT 30, enabled INTEGER NOT NULL DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(panel_id) REFERENCES panels(id));
CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, plan_id INTEGER NOT NULL, customer_name TEXT NOT NULL, customer_contact TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(plan_id) REFERENCES plans(id));
CREATE TABLE IF NOT EXISTS receipts(id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL, amount INTEGER NOT NULL, file_path TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', reviewed_by INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP, reviewed_at TEXT, FOREIGN KEY(order_id) REFERENCES orders(id));
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, action TEXT NOT NULL, actor_id INTEGER, detail TEXT DEFAULT '', ip TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
'''

@contextmanager
def connection():
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with connection() as db:
        db.executescript(SCHEMA)

def one(sql, args=()):
    with connection() as db:
        row = db.execute(sql, args).fetchone()
        return dict(row) if row else None

def all_rows(sql, args=()):
    with connection() as db:
        return [dict(r) for r in db.execute(sql, args).fetchall()]

def execute(sql, args=()):
    with connection() as db:
        cur = db.execute(sql, args)
        return cur.lastrowid

def audit(action, actor_id=None, detail='', ip=''):
    execute('INSERT INTO audit(action,actor_id,detail,ip) VALUES(?,?,?,?)', (action, actor_id, detail, ip))
