#!/usr/bin/env bash
set -Eeuo pipefail

REPO='https://github.com/durwinam/VEXORA/archive/refs/heads/main.tar.gz'
APP='/opt/vexora'
PORT='6000'
HOST='0.0.0.0'

red(){ echo -e "\033[31m[ERROR]\033[0m $*" >&2; }
log(){ echo -e "\033[36m[VEXORA]\033[0m $*"; }
fail(){ red "$*"; exit 1; }

[[ $EUID -eq 0 ]] || fail 'Run with sudo.'
command -v curl >/dev/null || fail 'curl is required.'
command -v python3 >/dev/null || fail 'python3 is required.'
command -v tar >/dev/null || fail 'tar is required.'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

log 'Downloading VEXORA source from GitHub...'
curl -fL --retry 3 --retry-delay 2 "$REPO" -o "$TMP/vexora.tar.gz"
tar -xzf "$TMP/vexora.tar.gz" -C "$TMP"

SRC="$(find "$TMP" -maxdepth 1 -type d -name 'VEXORA-*' -print -quit)"
[[ -n "$SRC" ]] || fail 'Repository archive is invalid.'
[[ -f "$SRC/requirements.txt" ]] || fail 'requirements.txt is missing from the repository.'
[[ -f "$SRC/app/main.py" ]] || fail 'app/main.py is missing from the repository.'

if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    log 'Installing system dependencies...'
    apt-get update -y
    apt-get install -y python3 python3-venv python3-pip curl ca-certificates openssl
fi

log "Installing VEXORA into $APP..."
mkdir -p "$APP"

# Preserve runtime data and an existing .env during updates.
if command -v rsync >/dev/null 2>&1; then
    rsync -a \
      --exclude '.venv/' \
      --exclude 'data/' \
      --exclude 'backups/' \
      --exclude '.env' \
      "$SRC/" "$APP/"
else
    find "$SRC" -mindepth 1 -maxdepth 1 ! -name '.env' -exec cp -a {} "$APP/" \;
fi

mkdir -p "$APP/data" "$APP/backups"

cd "$APP"

if [[ ! -d .venv ]]; then
    log 'Creating Python virtual environment...'
    python3 -m venv .venv
fi

source "$APP/.venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Never require .env.example. Generate a valid .env automatically.
if [[ ! -f "$APP/.env" ]]; then
    log 'Creating secure environment configuration...'
    cat > "$APP/.env" <<EOF
VEXORA_VERSION=1.0.0
VEXORA_HOST=0.0.0.0
VEXORA_PORT=6000
VEXORA_SHOP_PATH=/shop/
VEXORA_ADMIN_PATH=/admin/
EOF
fi

python - <<'PY'
from pathlib import Path
import secrets

p = Path('/opt/vexora/.env')
data = {}

for line in p.read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        data[k.strip()] = v.strip()

if not data.get('VEXORA_SECRET_KEY') or data['VEXORA_SECRET_KEY'] in {
    'CHANGE_ME', 'CHANGE_ME_TO_A_LONG_RANDOM_VALUE'
}:
    data['VEXORA_SECRET_KEY'] = secrets.token_urlsafe(64)

data.setdefault('VEXORA_VERSION', '1.0.0')
data['VEXORA_HOST'] = '0.0.0.0'
data['VEXORA_PORT'] = '6000'
data.setdefault('VEXORA_SHOP_PATH', '/shop/')
data.setdefault('VEXORA_ADMIN_PATH', '/admin/')

p.write_text(
    ''.join(f'{k}={v}\n' for k, v in data.items()),
    encoding='utf-8'
)
PY

id vexora >/dev/null 2>&1 || useradd --system --home "$APP" --shell /usr/sbin/nologin vexora

chown -R vexora:vexora "$APP"
chmod 750 "$APP"
chmod 700 "$APP/data" "$APP/backups"
chmod 600 "$APP/.env"

install -m 0755 "$APP/vexora.py" /usr/local/bin/vexora

cat > /etc/systemd/system/vexora.service <<SERVICE
[Unit]
Description=VEXORA Configuration Shop
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
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

systemctl daemon-reload
systemctl enable vexora
systemctl restart vexora

log 'Checking VEXORA health...'
HEALTHY=0
for i in $(seq 1 30); do
    if curl -fsS --max-time 2 http://127.0.0.1:6000/health >/tmp/vexora-health.json 2>/dev/null; then
        HEALTHY=1
        break
    fi
    sleep 1
done

if [[ "$HEALTHY" -ne 1 ]]; then
    red 'VEXORA did not pass the local health check.'
    systemctl --no-pager --full status vexora || true
    journalctl -u vexora -n 100 --no-pager || true
    exit 1
fi

echo
log 'Installation completed successfully.'
log 'Shop:  http://SERVER-IP:6000/shop/'
log 'Admin: http://SERVER-IP:6000/admin/'
log 'CLI:   vexora'
cat /tmp/vexora-health.json
