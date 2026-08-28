#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="/opt/vexora"
CONFIG_DIR="/etc/vexora"
DATA_DIR="/var/lib/vexora"
LOG_DIR="/var/log/vexora"
SERVICE="vexora"
INTERNAL_PORT=6000
HTTP_PORT=8080
HTTPS_PORT=443
REPO="https://github.com/durwinam/VEXORA"

info(){ printf '\033[36m[VEXORA]\033[0m %s\n' "$*"; }
ok(){ printf '\033[32m[  OK  ]\033[0m %s\n' "$*"; }
warn(){ printf '\033[33m[ WARN ]\033[0m %s\n' "$*"; }
fail(){ printf '\033[31m[ FAIL ]\033[0m %s\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || fail "Installer must run as root."
command -v curl >/dev/null || fail "curl is required."
command -v python3 >/dev/null || fail "python3 is required."

cat <<'BANNER'
╔════════════════════════════════════════════════════════════╗
║                    VEXORA PRO 4.1.0                       ║
║        Configuration Shop • Management • SSL              ║
╚════════════════════════════════════════════════════════════╝
BANNER

echo
echo "Public access mode:"
echo "  1) Domain + HTTPS (Recommended)"
echo "  2) IP + HTTPS"
echo "  3) HTTP :8080"

while true; do
  read -r -p "Select [1-3] (default: 1): " MODE
  MODE="${MODE//[$' \t\r\n']/}"
  MODE="${MODE:-1}"
  case "$MODE" in
    1|2|3) break ;;
    *) echo "[ FAIL ] Invalid mode. Please enter 1, 2 or 3." ;;
  esac
done

PUBLIC_HOST=""
PUBLIC_SCHEME="http"
PUBLIC_PORT="$HTTP_PORT"

case "$MODE" in
  1)
    read -r -p "Domain: " PUBLIC_HOST
    [[ "$PUBLIC_HOST" =~ ^[A-Za-z0-9.-]+$ ]] || fail "Invalid domain."
    PUBLIC_SCHEME="https"; PUBLIC_PORT="$HTTPS_PORT" ;;
  2)
    read -r -p "Public IPv4: " PUBLIC_HOST
    [[ "$PUBLIC_HOST" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] || fail "Invalid IPv4."
    PUBLIC_SCHEME="https"; PUBLIC_PORT="$HTTPS_PORT" ;;
  3) : ;;
esac

SHOP_PATH="/shop/"
ADMIN_PATH="/admin/"
if [[ "$BASE_PATH" != "/" ]]; then
  SHOP_PATH="${BASE_PATH}shop/"
  ADMIN_PATH="${BASE_PATH}admin/"
fi

info "Installing required packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip nginx curl openssl >/dev/null
id vexora >/dev/null 2>&1 || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin vexora
mkdir -p "$APP_DIR" "$CONFIG_DIR" "$DATA_DIR" "$LOG_DIR"

info "Downloading VEXORA source..."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
curl -fsSL --retry 4 --retry-delay 2 "$REPO/archive/refs/heads/main.tar.gz" -o "$tmp/vexora.tar.gz"
tar -xzf "$tmp/vexora.tar.gz" -C "$tmp"
SRC="$tmp/VEXORA-main"
[[ -f "$SRC/app/main.py" && -f "$SRC/requirements.txt" ]] || fail "Incomplete repository."
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"
cp -a "$SRC/." "$APP_DIR/"
find "$APP_DIR" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$APP_DIR" -type f -name '*.pyc' -delete

info "Creating isolated Python environment..."
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip wheel -q
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt" -q

SECRET="$($APP_DIR/.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(48))')"
COOKIE_SECURE=false
[[ "$PUBLIC_SCHEME" == "https" ]] && COOKIE_SECURE=true
cat > "$CONFIG_DIR/.env" <<EOF
VEXORA_VERSION=4.1.0
VEXORA_HOST=127.0.0.1
VEXORA_PORT=$INTERNAL_PORT
VEXORA_PUBLIC_HOST=$PUBLIC_HOST
VEXORA_PUBLIC_PORT=$PUBLIC_PORT
VEXORA_PUBLIC_SCHEME=$PUBLIC_SCHEME
VEXORA_BASE_PATH=$BASE_PATH
VEXORA_SHOP_PATH=$SHOP_PATH
VEXORA_ADMIN_PATH=$ADMIN_PATH
VEXORA_HEALTH_PATH=/health
VEXORA_CONFIG_DIR=$CONFIG_DIR
VEXORA_DATA_DIR=$DATA_DIR
VEXORA_LOG_DIR=$LOG_DIR
VEXORA_SECRET_KEY=$SECRET
VEXORA_SESSION_HOURS=24
VEXORA_MAX_UPLOAD_MB=10
VEXORA_COOKIE_SECURE=$COOKIE_SECURE
VEXORA_TELEGRAM_BOT_TOKEN=
VEXORA_TELEGRAM_CHAT_ID=
EOF
chmod 600 "$CONFIG_DIR/.env"
cp "$APP_DIR/.env.example" "$CONFIG_DIR/.env.example"
chown -R vexora:vexora "$APP_DIR" "$DATA_DIR" "$LOG_DIR"

cat > "/etc/systemd/system/$SERVICE.service" <<EOF
[Unit]
Description=VEXORA PRO Configuration Shop
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=vexora
Group=vexora
WorkingDirectory=$APP_DIR
EnvironmentFile=$CONFIG_DIR/.env
ExecStart=$APP_DIR/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port $INTERNAL_PORT
Restart=always
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ReadWritePaths=$DATA_DIR $LOG_DIR $CONFIG_DIR
[Install]
WantedBy=multi-user.target
EOF

info "Configuring Nginx reverse proxy..."
rm -f /etc/nginx/sites-enabled/default
cat > /etc/nginx/sites-available/vexora.conf <<EOF
server {
    listen $HTTP_PORT;
    listen [::]:$HTTP_PORT;
    server_name ${PUBLIC_HOST:-_};
    location / {
        proxy_pass http://127.0.0.1:$INTERNAL_PORT;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
ln -sf /etc/nginx/sites-available/vexora.conf /etc/nginx/sites-enabled/vexora.conf

CERT_OK=false
if [[ "$MODE" == "1" ]]; then
  if ss -lnt 2>/dev/null | awk '{print $4}' | grep -Eq '(^|:)443$'; then
    warn "443 is occupied; HTTPS will not replace the existing service."
  else
    apt-get install -y -qq certbot python3-certbot-nginx >/dev/null || true
    if certbot certonly --nginx --non-interactive --agree-tos --register-unsafely-without-email -d "$PUBLIC_HOST" >/tmp/vexora-cert.log 2>&1; then
      CERT_OK=true
      cat > /etc/nginx/sites-available/vexora-ssl.conf <<EOF
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name $PUBLIC_HOST;
    ssl_certificate /etc/letsencrypt/live/$PUBLIC_HOST/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$PUBLIC_HOST/privkey.pem;
    location / {
        proxy_pass http://127.0.0.1:$INTERNAL_PORT;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
EOF
      ln -sf /etc/nginx/sites-available/vexora-ssl.conf /etc/nginx/sites-enabled/vexora-ssl.conf
      systemctl enable --now certbot.timer >/dev/null 2>&1 || true
    else
      warn "Certificate issuance failed; see /tmp/vexora-cert.log. HTTP :8080 remains available."
    fi
  fi
elif [[ "$MODE" == "2" ]]; then
  warn "IP HTTPS requires a CA that issues IP certificates. No fake certificate is created. HTTP :8080 remains available."
fi

nginx -t >/dev/null || fail "Nginx configuration test failed."
systemctl daemon-reload
systemctl enable --now "$SERVICE"
systemctl reload nginx

info "Running health checks..."
healthy=false
for _ in {1..20}; do
  if curl -fsS "http://127.0.0.1:$INTERNAL_PORT/health" >/tmp/vexora-health.json; then healthy=true; break; fi
  sleep 1
done
$healthy || { journalctl -u "$SERVICE" -n 80 --no-pager; fail "VEXORA did not become healthy."; }

# Retrieve credentials from the first-start log. The application prints them once, then they remain in the journal.
USERNAME="$(journalctl -u "$SERVICE" --no-pager | sed -n 's/.*VEXORA_FIRST_LOGIN username=\([^ ]*\) password=.*/\1/p' | tail -1)"
PASSWORD="$(journalctl -u "$SERVICE" --no-pager | sed -n 's/.*VEXORA_FIRST_LOGIN username=[^ ]* password=\([^ ]*\).*/\1/p' | tail -1)"
USERNAME="${USERNAME:-owner}"
PASSWORD="${PASSWORD:-See journalctl -u vexora for the first generated password}"

if $CERT_OK; then
  PUBLIC_URL="https://$PUBLIC_HOST${BASE_PATH%/}"
else
  PUBLIC_URL="http://${PUBLIC_HOST:-SERVER-IP}:$HTTP_PORT${BASE_PATH%/}"
fi
CRED_FILE="$CONFIG_DIR/INSTALLATION.txt"
cat > "$CRED_FILE" <<EOF
VEXORA PRO 4.1.0

Public URL : $PUBLIC_URL
Shop       : ${PUBLIC_URL%/}/shop/
Admin      : ${PUBLIC_URL%/}/admin/

Username   : $USERNAME
Password   : $PASSWORD

Config     : $CONFIG_DIR/.env
Install    : $CRED_FILE
Data       : $DATA_DIR
Logs       : $LOG_DIR
Service    : $SERVICE
Internal   : 127.0.0.1:$INTERNAL_PORT
HTTP       : :$HTTP_PORT
HTTPS      : :$HTTPS_PORT
EOF
chmod 600 "$CRED_FILE"

ok "Installation completed successfully."
printf '\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
printf '🌐 Public : %s\n' "$PUBLIC_URL"
printf '🛒 Shop   : %s/shop/\n' "${PUBLIC_URL%/}"
printf '🔐 Admin  : %s/admin/\n' "${PUBLIC_URL%/}"
printf '\n👤 User   : %s\n' "$USERNAME"
printf '🔑 Pass   : %s\n' "$PASSWORD"
printf '\n⚙ Config : %s/.env\n' "$CONFIG_DIR"
printf '📄 Info   : %s\n' "$CRED_FILE"
printf '🧩 CLI    : vexora\n'
printf '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'

