# VEXORA

Lightweight configuration sales platform foundation with secure credential storage and isolated panel providers.

## Providers
- PasarGuard
- Sanaei / 3X-UI
- Marzban

The provider adapters are isolated and use the APIs demonstrated by the supplied reference projects. PasarGuard deployments can vary by release; configure the token/endpoint appropriate to your installed build.

## Install
```bash
sudo bash install.sh
```
Default web port: `6000`, shop path: `/shop/`.

## Security
Credentials are encrypted at rest. Passwords are Argon2id hashes. Never commit `.env`, database files, certificates, private keys, bot tokens or panel credentials.

## CLI
```bash
vexora
```

## Development tests
```bash
python -m pytest -q
```

Copyright © 2026 durwinam.
