# VEXORA Architecture

VEXORA uses a lightweight architecture:

- FastAPI/Python for the backend and API layer.
- HTML templates for server-rendered pages.
- Vanilla CSS and JavaScript for the frontend.
- SQLite for the default local database.
- Separate panel adapters for PasarGuard, 3X-UI and Marzban.
- Systemd for the application service.
- Reverse proxy/HTTPS is handled by the installer.

The frontend intentionally avoids React, Vue, Node build chains and other heavyweight runtime dependencies.
