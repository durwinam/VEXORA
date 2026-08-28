#!/usr/bin/env bash
set -Eeuo pipefail
REPO="https://github.com/durwinam/VEXORA/archive/refs/heads/main.tar.gz"
APP="/opt/vexora"; INTERNAL="6000"; ACME="/var/www/vexora-acme"
NGINX="/etc/nginx/sites-available/vexora.conf"
log(){ echo -e "\033[36m[VEXORA]\033[0m $*"; }
die(){ echo -e "\033[31m[ERROR]\033[0m $*" >&2; exit 1; }
[[ $EUID -eq 0 ]] || die "Run as root."
command -v curl >/dev/null || die "curl required"; command -v tar >/dev/null || die "tar required"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
curl -fL --retry 5 --retry-delay 2 "$REPO" -o "$T/v.tar.gz"
tar -xzf "$T/v.tar.gz" -C "$T"; SRC=$(find "$T" -maxdepth 1 -type d -name 'VEXORA-*' -print -quit)
[[ -f "$SRC/app/main.py" ]] || die "Invalid VEXORA archive."

if command -v apt-get >/dev/null; then
 export DEBIAN_FRONTEND=noninteractive
 apt-get update -y
 apt-get install -y python3 python3-venv python3-pip curl ca-certificates openssl nginx
else
 command -v nginx >/dev/null || die "nginx is required."
fi

mkdir -p "$APP/data" "$APP/backups" "$ACME/.well-known/acme-challenge"
if command -v rsync >/dev/null; then
 rsync -a --delete --exclude '.venv/' --exclude '.certbot/' --exclude 'data/' --exclude 'backups/' --exclude '.env' "$SRC/" "$APP/"
else
 find "$SRC" -mindepth 1 -maxdepth 1 ! -name '.env' -exec cp -a {} "$APP/" \;
fi
cd "$APP"; python3 -m venv .venv
source .venv/bin/activate
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt

echo "1) Domain + HTTPS [Recommended]"
echo "2) IP + HTTPS"
echo "3) HTTP :8080"
read -r -p "Select [1]: " MODE; MODE=${MODE:-1}
read -r -p "Path [/vexora/]: " BASE; BASE=${BASE:-/vexora/}
[[ "$BASE" == /* ]] || BASE="/$BASE"; [[ "$BASE" == */ ]] || BASE="$BASE/"
read -r -p "Domain or public IP [auto]: " HOST
HOST=${HOST:-$(curl -4fsS --max-time 5 https://api.ipify.org || hostname -I | awk '{print $1}')}

# Preserve an existing .env but update deployment keys.
python3 - "$APP/.env" "$BASE" "$HOST" "$MODE" <<'PY'
import sys,secrets
from pathlib import Path
p=Path(sys.argv[1]); base=sys.argv[2]; host=sys.argv[3]; mode=sys.argv[4]
d={}
if p.exists():
 for l in p.read_text().splitlines():
  if '=' in l and not l.lstrip().startswith('#'):
   k,v=l.split('=',1); d[k]=v
d.update(VEXORA_VERSION='2.0.0',VEXORA_HOST='127.0.0.1',VEXORA_PORT='6000',
 VEXORA_BASE_PATH=base,VEXORA_SHOP_PATH=base+'shop/',VEXORA_ADMIN_PATH=base+'admin/',
 VEXORA_PUBLIC_HOST=host,VEXORA_PUBLIC_PORT='443',
 VEXORA_PUBLIC_SCHEME='https' if mode in ('1','2') else 'http')
if not d.get('VEXORA_SECRET_KEY') or d['VEXORA_SECRET_KEY']=='CHANGE_ME': d['VEXORA_SECRET_KEY']=secrets.token_urlsafe(64)
p.write_text(''.join(f'{k}={v}\n' for k,v in d.items()))
PY

id vexora >/dev/null 2>&1 || useradd --system --home "$APP" --shell /usr/sbin/nologin vexora
chown -R vexora:vexora "$APP"; chmod 750 "$APP"; chmod 700 "$APP/data" "$APP/backups"; chmod 600 "$APP/.env"
install -m 0755 "$APP/vexora.py" /usr/local/bin/vexora
cat >/etc/systemd/system/vexora.service <<EOF
[Unit]
Description=VEXORA Configuration Shop
After=network-online.target
Wants=network-online.target
[Service]
User=vexora
Group=vexora
WorkingDirectory=$APP
EnvironmentFile=$APP/.env
ExecStart=$APP/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 6000
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=full
ReadWritePaths=$APP/data $APP/backups
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload; systemctl enable vexora; systemctl restart vexora

# Public port: never take over an occupied 443.
HTTPS=0
if ! ss -lnt 2>/dev/null | awk '{print $4}' | grep -Eq '(^|:)443$'; then HTTPS=1; fi
# HTTP challenge/fallback always uses 8080 here; if port 80 is free we add a tiny ACME listener.
cat >/etc/nginx/sites-available/vexora.conf <<EOF
server {
 listen 8080;
 listen [::]:8080;
 server_name $HOST _;
 client_max_body_size 20m;
 location ^~ /.well-known/acme-challenge/ { root $ACME; }
 location $BASE {
  proxy_pass http://127.0.0.1:6000;
  proxy_http_version 1.1;
  proxy_set_header Host \$host;
  proxy_set_header X-Real-IP \$remote_addr;
  proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto \$scheme;
 }
}
EOF
mkdir -p /etc/nginx/sites-enabled
ln -sf "$NGINX" /etc/nginx/sites-enabled/vexora.conf
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
# Before certificate exists, only enable the 8080 server.
if [[ "$HTTPS" == 1 ]]; then
 sed -i '/server {$/{x;p;x;}' /dev/null 2>/dev/null || true
fi
nginx -t && systemctl reload nginx

# Certbot in an isolated venv; no dependency on old distro certbot.
CB="$APP/.certbot"; python3 -m venv "$CB"; "$CB/bin/pip" -q install --upgrade pip certbot
CERTBOT="$CB/bin/certbot"
# Port 80 is needed for ACME http-01. Create an ACME-only listener if free.
if ! ss -lnt 2>/dev/null | awk '{print $4}' | grep -Eq '(^|:)80$'; then
 cat >/etc/nginx/conf.d/vexora-acme.conf <<EOF
server { listen 80; listen [::]:80; server_name $HOST _; location ^~ /.well-known/acme-challenge/ { root $ACME; } location / { return 404; } }
EOF
 nginx -t && systemctl reload nginx
fi

ISSUED=0
if [[ "$MODE" == "1" ]]; then
 if "$CERTBOT" certonly --webroot -w "$ACME" -d "$HOST" --non-interactive --agree-tos --register-unsafely-without-email --keep-until-expiring; then ISSUED=1; fi
elif [[ "$MODE" == "2" ]]; then
 if "$CERTBOT" certonly --webroot -w "$ACME" --preferred-profile shortlived --ip-address "$HOST" --non-interactive --agree-tos --register-unsafely-without-email --keep-until-expiring; then ISSUED=1; fi
fi

# If 443 is free and cert was issued, validate and load TLS server. Otherwise keep 8080.
if [[ "$HTTPS" == 1 && "$ISSUED" == 1 ]]; then
 cat >>/etc/nginx/sites-available/vexora.conf <<EOF
server {
 listen 443 ssl;
 listen [::]:443 ssl;
 server_name $HOST _;
 ssl_certificate /etc/letsencrypt/live/$HOST/fullchain.pem;
 ssl_certificate_key /etc/letsencrypt/live/$HOST/privkey.pem;
 client_max_body_size 20m;
 location $BASE {
  proxy_pass http://127.0.0.1:6000;
  proxy_http_version 1.1;
  proxy_set_header Host \$host;
  proxy_set_header X-Real-IP \$remote_addr;
  proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto https;
 }
}
EOF
 nginx -t && systemctl reload nginx
fi
cat >/etc/systemd/system/vexora-cert-renew.service <<EOF
[Unit]
Description=VEXORA certificate renewal
[Service]
Type=oneshot
ExecStart=$CERTBOT renew --quiet --deploy-hook /usr/sbin/nginx\ -s\ reload
EOF
cat >/etc/systemd/system/vexora-cert-renew.timer <<EOF
[Unit]
Description=VEXORA certificate renewal timer
[Timer]
OnBootSec=15m
OnUnitActiveSec=6h
Persistent=true
[Install]
WantedBy=timers.target
EOF
systemctl daemon-reload; systemctl enable --now vexora-cert-renew.timer

for i in $(seq 1 30); do curl -fsS http://127.0.0.1:6000/health >/tmp/vexora-health.json 2>/dev/null && break; sleep 1; done
curl -fsS http://127.0.0.1:6000/health >/dev/null || { journalctl -u vexora -n 100 --no-pager; exit 1; }
echo
log "Internal: http://127.0.0.1:6000"
if [[ "$ISSUED" == 1 && "$HTTPS" == 1 ]]; then log "Public: https://$HOST$BASE"; else log "Public fallback: http://$HOST:8080$BASE"; fi
log "CLI: vexora"
