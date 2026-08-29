#!/usr/bin/env bash
set -Eeuo pipefail
APP_DIR="/opt/vexora"
cd "$APP_DIR"
echo "[VEXORA] Updating application..."
if [[ -d .venv ]]; then
  .venv/bin/pip install -r requirements.txt
fi
systemctl daemon-reload
systemctl restart vexora
systemctl restart nginx
systemctl --no-pager --full status vexora || true
echo "[VEXORA] Update completed."
