#!/usr/bin/env bash
set -Eeuo pipefail
APP=/opt/vexora; TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
"$APP/.venv/bin/python" -c 'from app.services.backup import make_backup; print("Database backup:",make_backup())'
tar -czf "$TMP/source-before-update.tar.gz" --exclude='.venv' --exclude='*.db' --exclude='first-login' -C "$APP" .
curl -fsSL --retry 4 https://github.com/durwinam/VEXORA/archive/refs/heads/main.tar.gz -o "$TMP/v.tar.gz"
tar -xzf "$TMP/v.tar.gz" -C "$TMP"; SRC="$TMP/VEXORA-main"; test -f "$SRC/app/main.py"
rsync -a --delete --exclude '.venv/' --exclude '*.db' --exclude 'first-login' "$SRC/" "$APP/"
if ! "$APP/.venv/bin/pip" install -q -r "$APP/requirements.txt" || ! systemctl restart vexora || ! sleep 2 || ! "$APP/scripts/health-check.sh"; then
  echo '[ WARN ] Update health check failed; restoring previous source.' >&2
  systemctl stop vexora || true
  find "$APP" -mindepth 1 -maxdepth 1 ! -name .venv ! -name first-login -exec rm -rf {} +
  tar -xzf "$TMP/source-before-update.tar.gz" -C "$APP"
  systemctl start vexora
  sleep 2
  "$APP/scripts/health-check.sh"
  echo '[ FAIL ] Update rolled back.' >&2
  exit 1
fi
echo 'VEXORA update complete.'
