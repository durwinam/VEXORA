# VEXORA 1.0.0

Self-hosted RTL Persian configuration shop and management panel for VPS deployment and source distribution.

## Public routes
- `/shop/` — customer storefront
- `/admin/` — administrator dashboard
- `/health` — local health endpoint

## Included
- Responsive RTL storefront and admin dashboard
- SQLite database with WAL and audit records
- Product/plan catalog, orders and receipt workflow
- Panel registry with encrypted credentials and connectivity check
- Signed admin sessions with bcrypt password hashing
- Login rate limiting
- Nginx reverse proxy with FastAPI bound only to `127.0.0.1:6000`
- HTTP on `8080` and HTTPS on `443` when a valid certificate is available
- Let's Encrypt/Certbot certificate issuance and renewal hook
- Domain certificates and supported IP certificates
- Generated admin credentials and protected installation report
- Daily automatic backups, manual backup and restore
- Update command with source rollback on failed health checks
- Health checks for application, Nginx and public routes
- Management CLI: start, stop, restart, status, logs, health, version, backup, restore, update, uninstall
- Local Persian fonts, SVG icons and emoji-friendly UI
- Copyright attribution for `durwinam`

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/durwinam/VEXORA/main/install.sh -o /tmp/vexora-install.sh && sudo bash /tmp/vexora-install.sh
```

The installer asks for public mode and domain/IP. Public routes are fixed: `/shop/` for customers and `/admin/` for administrators. It creates `/etc/vexora/.env` automatically and never requires `/etc/vexora/.env`.

## Runtime paths
- `/etc/vexora/.env` — runtime configuration and secret key (mode 600)
- `/etc/vexora/INSTALLATION.txt` — installation summary (mode 600)
- `/var/lib/vexora` — database, receipts and backups
- `/var/log/vexora` — log directory
- `/opt/vexora` — application source and virtual environment

## CLI
```text
vexora start
vexora stop
vexora restart
vexora status
vexora logs
vexora health
vexora version
vexora backup
vexora restore
vexora update
vexora uninstall
```

## Security model
The application is intentionally bound to `127.0.0.1:6000`. Nginx is the public entry point. Passwords are bcrypt-hashed, sessions are signed, login attempts are rate limited, uploads are size/type checked, and secrets are stored outside the web root.

## Certificates
Domain certificates use Let's Encrypt HTTP-01 through Certbot. IP address certificates require a recent Certbot release that supports the short-lived IP profile. If HTTPS cannot be activated, VEXORA remains available on HTTP `:8080` and the installer reports the exact certificate status instead of pretending HTTPS succeeded.
