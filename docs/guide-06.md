# VEXORA Operations Guide 06

This guide is part of the VEXORA PRO source distribution. Keep operational configuration outside the repository and use `/etc/vexora/.env` on deployed servers.

Recommended checks:

- `vexora health`
- `vexora status`
- `vexora logs`
- `nginx -t`

The installer must never overwrite an unrelated service already occupying port 443.
