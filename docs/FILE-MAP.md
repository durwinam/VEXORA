# File map

`install.sh` — complete first-run deployment flow.

`app/main.py` — FastAPI application entry point.

`app/config.py` — runtime configuration.

`app/security.py` — password hashing and verification.

`app/auth.py` — signed administrator session handling.

`app/database.py` — SQLite connection and health helpers.

`app/routes/shop.py` — public shop routes.

`app/routes/admin.py` — administrator routes and mutations.

`app/templates/` — server-rendered UI.

`app/static/css/app.css` — complete responsive design system.

`app/static/js/app.js` — interactive storefront behavior.

`nginx/vexora.conf` — public TLS reverse proxy.

`systemd/vexora.service` — service definition.

`scripts/backup.sh` — verified backup.

`scripts/restore.sh` — verified restore.

`scripts/update.sh` — controlled update.

`scripts/uninstall.sh` — controlled removal.
