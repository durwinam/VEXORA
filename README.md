# VEXORA

VEXORA is a lightweight Persian/English/Russian-ready configuration shop foundation with multi-tenant administration, provider adapters, receipt workflow, Telegram notifications, owner backup, QR generation, and a one-command installer.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/durwinam/VEXORA/main/install.sh -o /tmp/vexora-install.sh && sudo bash /tmp/vexora-install.sh
```

The installer downloads the complete repository archive, creates `/opt/vexora/.venv`, creates a random `VEXORA_SECRET_KEY`, installs a systemd service on port `6000`, and runs a health check.

## CLI

```bash
vexora version
vexora status
vexora health
vexora test
vexora restart
vexora backup
```

## Security

- PBKDF2-SHA256 password hashing.
- HttpOnly/SameSite session cookie.
- Secrets encrypted at rest with a key derived from `VEXORA_SECRET_KEY`.
- systemd hardening and non-root service account.
- Audit logs for authentication and administration events.
- Upload size/type validation for receipts.
- Owner-only backup endpoint and Telegram delivery.

## Providers

The adapter layer supports PasarGuard and Marzban token authentication and a 3X-UI/Sanaei login adapter. 3X-UI client creation requires an inbound mapping because the correct payload depends on the selected inbound transport/security settings; the adapter intentionally refuses to guess those values.

## License

BSD-3-Clause. Copyright/attribution to `durwinam` must be preserved.
