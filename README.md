# VEXORA 1.0.0

VEXORA is a modular configuration shop with a protected administration panel.

## Routes

- `/` redirects directly to `/shop/`.
- `/shop/` is public.
- `/admin/` requires authentication.
- `/admin/login` is the administrator login.
- `/health` is the local service health endpoint.

## Runtime

The Python application listens on `0.0.0.0:6000`.

Public access is HTTPS-only through Nginx on port `443` and a second HTTPS port selected by the installer.

Port `8080` is not used.

## Installation

The installer creates `/etc/vexora/.env` automatically.

It does not require `.env.example` to exist.

A valid public certificate is required before the installation is considered successful.

## Source style

Project source is intentionally readable and modular.

Python, HTML, CSS and shell files use normal multi-line formatting.
