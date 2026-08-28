import sqlite3, os, json
from pathlib import Path
from contextlib import contextmanager
from .config import settings

SCHEMA = '''
CREATE TABLE IF NOT EXISTS admins(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL, tenant_id INTEGER, active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS tenants(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, slug TEXT UNIQUE NOT NULL, domain TEXT UNIQUE, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS panels(id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER NOT NULL, name TEXT NOT NULL, kind TEXT NOT NULL, base_url TEXT NOT NULL, username TEXT, secret_enc TEXT, verify_tls INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS plans(id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER NOT NULL, panel_id INTEGER NOT NULL, name TEXT NOT NULL, price INTEGER NOT NULL, volume_gb REAL NOT NULL, days INTEGER NOT NULL, enabled INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER NOT NULL, username TEXT, panel_user_id TEXT, plan_id INTEGER, subscription_url TEXT, config_text TEXT, expires_at TEXT, total_bytes INTEGER DEFAULT 0, used_bytes INTEGER DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS receipts(id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER NOT NULL, customer_id INTEGER, amount INTEGER NOT NULL, file_path TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', reviewed_by INTEGER, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, reviewed_at TEXT);
CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY AUTOINCREMENT, actor_admin_id INTEGER, event TEXT NOT NULL, ip TEXT, meta TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
'''

Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
@contextmanager
def db():
    con=sqlite3.connect(settings.db_path, timeout=20)
    con.row_factory=sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    try:
        yield con; con.commit()
    except: con.rollback(); raise
    finally: con.close()

def init_db():
    with db() as c: c.executescript(SCHEMA)

def q(sql,args=()):
    with db() as c: return c.execute(sql,args).fetchall()
def one(sql,args=()):
    with db() as c: return c.execute(sql,args).fetchone()
def exec(sql,args=()):
    with db() as c:
        cur=c.execute(sql,args); return cur.lastrowid

def audit(actor,event,ip,meta=None):
    exec("INSERT INTO audit_logs(actor_admin_id,event,ip,meta) VALUES(?,?,?,?)",(actor,event,ip,json.dumps(meta or {},ensure_ascii=False)))
