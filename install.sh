#!/usr/bin/env bash
set -Eeuo pipefail
REPO='https://github.com/durwinam/VEXORA/archive/refs/heads/main.tar.gz'
APP='/opt/vexora'; PORT='6000'; HOST='0.0.0.0'
red(){ echo -e "\033[31m[ERROR]\033[0m $*" >&2; }; log(){ echo -e "\033[36m[VEXORA]\033[0m $*"; }
trap 'red "Installation failed at line $LINENO. Check: journalctl -u vexora -n 100 --no-pager"' ERR
[[ $EUID -eq 0 ]] || { red 'Run with sudo.'; exit 1; }
command -v curl >/dev/null || { red 'curl is required'; exit 1; }
command -v python3 >/dev/null || { red 'python3 is required'; exit 1; }
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
log 'Downloading VEXORA source...'
curl -fL --retry 3 --retry-delay 2 "$REPO" -o "$TMP/vexora.tar.gz"
tar -xzf "$TMP/vexora.tar.gz" -C "$TMP"
SRC=$(find "$TMP" -maxdepth 1 -type d -name 'VEXORA-*' -print -quit)
[[ -n "$SRC" ]] || { red 'Repository archive is invalid'; exit 1; }
if command -v apt-get >/dev/null; then export DEBIAN_FRONTEND=noninteractive; apt-get update -y; apt-get install -y python3 python3-venv python3-pip curl ca-certificates openssl; fi
mkdir -p "$APP/data" "$APP/backups"
# Preserve .env and runtime data on updates.
cp -a "$SRC/." "$APP/" 2>/dev/null || true
cd "$APP"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if [[ ! -f .env ]]; then cp .env.example .env; fi
python - <<'PY'
from pathlib import Path
import secrets
p=Path('/opt/vexora/.env'); d={}
for l in p.read_text().splitlines():
 if '=' in l and not l.startswith('#'):
  k,v=l.split('=',1); d[k]=v
if not d.get('VEXORA_SECRET_KEY') or d.get('VEXORA_SECRET_KEY')=='CHANGE_ME': d['VEXORA_SECRET_KEY']=secrets.token_urlsafe(64)
d['VEXORA_PORT']='6000'; d['VEXORA_HOST']='0.0.0.0'
p.write_text('\n'.join(f'{k}={v}' for k,v in d.items())+'\n')
PY
id vexora >/dev/null 2>&1 || useradd --system --home "$APP" --shell /usr/sbin/nologin vexora
chown -R vexora:vexora "$APP"; chmod 600 "$APP/.env"; chmod 700 "$APP/data" "$APP/backups"
install -m 0755 "$APP/vexora.py" /usr/local/bin/vexora
cat >/etc/systemd/system/vexora.service <<SERVICE
[Unit]
Description=VEXORA Configuration Shop
After=network-online.target
Wants=network-online.target
[Service]
User=vexora
Group=vexora
WorkingDirectory=$APP
EnvironmentFile=$APP/.env
ExecStart=$APP/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 6000
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=full
ReadWritePaths=$APP/data $APP/backups
[Install]
WantedBy=multi-user.target
SERVICE
systemctl daemon-reload; systemctl enable --now vexora
for i in $(seq 1 30); do curl -fsS http://127.0.0.1:6000/health >/dev/null && break || sleep 1; done
curl -fsS http://127.0.0.1:6000/health || { journalctl -u vexora -n 100 --no-pager; exit 1; }
echo; log 'Installed successfully.'; log 'Shop: http://SERVER-IP:6000/shop/'; log 'Admin: http://SERVER-IP:6000/admin/'; log 'CLI: vexora'
