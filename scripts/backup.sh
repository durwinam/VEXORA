#!/usr/bin/env bash
set -Eeuo pipefail
/opt/vexora/.venv/bin/python -c 'from app.services.backup import make_backup; print(make_backup())'
