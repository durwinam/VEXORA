# VEXORA PRO 4.0.0

A self-hosted, RTL Persian configuration shop and management panel for VPS deployment and source distribution.

## Included

- Professional responsive storefront and admin dashboard
- SQLite database with WAL and audit records
- Product/plan catalog, orders and receipt workflow
- Panel registry with encrypted credentials and connectivity check
- Signed admin sessions with bcrypt password hashing
- Configurable domain/IP, base path and public ports
- Nginx reverse proxy with internal FastAPI on 127.0.0.1:6000
- Public HTTP fallback on 8080 and HTTPS on 443 when available
- Domain ACME/Certbot integration
- Generated admin username/password and installation report
- Backup, health-check, update, uninstall and CLI helpers
- Copyright attribution for `durwinam`

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/durwinam/VEXORA/main/install.sh | bash
```

The installer asks for public mode and base path. It prints the final URL, generated credentials, and configuration location.

## Runtime paths

- `/etc/vexora/.env` — configuration and secret key
- `/etc/vexora/INSTALLATION.txt` — installation summary
- `/var/lib/vexora` — database, receipts and backups
- `/var/log/vexora` — logs
- `/opt/vexora` — application source and virtualenv

## Important

The application is intentionally bound to `127.0.0.1:6000`. Public access is provided by Nginx. A certificate is never marked as successful unless the ACME command actually succeeds. IP certificate issuance depends on CA support.

## Local UI assets

VEXORA bundles its Persian UI fonts and dashboard SVG icons locally.
The interface does not require a CDN for typography or core icons. Emoji are
rendered through the operating system/browser emoji stack, with graceful
fallbacks when a color emoji font is unavailable.

## Installer 4.1.0 credentials
The installer generates a random owner password during installation and writes a one-time
`/opt/vexora/first-login` bootstrap file. The application consumes and deletes this file after
creating the administrator account. The installer prints the credentials once and stores the
installation summary at `/etc/vexora/INSTALLATION.txt` (mode 600). Runtime configuration is
created automatically at `/etc/vexora/.env`; `.env.example` is not required.
