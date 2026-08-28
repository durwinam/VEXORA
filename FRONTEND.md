# VEXORA Frontend

The UI is intentionally lightweight and server-rendered.

- `app/templates/` — HTML/Jinja pages
- `app/static/css/app.css` — responsive design system
- `app/static/js/app.js` — small vanilla JavaScript layer
- No React/Vue/Node build step is required.

Pages included:
- Shop
- Admin dashboard

The backend should render these templates through FastAPI/Jinja and expose `/static`.
