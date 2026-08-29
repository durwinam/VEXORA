#!/usr/bin/env bash
set -Eeuo pipefail
ZIP=${1:-}
[[ -f "$ZIP" ]] || { echo 'Usage: vexora restore /path/to/backup.zip' >&2; exit 2; }
python3 - "$ZIP" <<'PY'
import sys,zipfile
p=sys.argv[1]
with zipfile.ZipFile(p) as z:
    names=set(z.namelist())
    if 'data/vexora.db' not in names: raise SystemExit('Invalid VEXORA backup: database missing')
PY
systemctl stop vexora
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
unzip -q "$ZIP" -d "$TMP"
cp "$TMP/data/vexora.db" /var/lib/vexora/vexora.db
if [[ -f "$TMP/config/.env" ]]; then install -m 600 "$TMP/config/.env" /etc/vexora/.env; fi
chown -R vexora:vexora /var/lib/vexora
systemctl start vexora;sleep 2;/opt/vexora/scripts/health-check.sh
echo 'VEXORA restore complete.'
