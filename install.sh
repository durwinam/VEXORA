#!/usr/bin/env bash
set -Eeuo pipefail
APP_DIR=/opt/vexora; CONFIG_DIR=/etc/vexora; DATA_DIR=/var/lib/vexora; LOG_DIR=/var/log/vexora
SERVICE=vexora; INTERNAL_PORT=6000; HTTP_PORT=8080; HTTPS_PORT=443; ACME_PORT=80; VERSION=1.0.0
REPO=https://github.com/durwinam/VEXORA
info(){ printf '\033[36m[VEXORA]\033[0m %s\n' "$*"; }
ok(){ printf '\033[32m[  OK  ]\033[0m %s\n' "$*"; }
warn(){ printf '\033[33m[ WARN ]\033[0m %s\n' "$*"; }
fail(){ printf '\033[31m[ FAIL ]\033[0m %s\n' "$*" >&2; exit 1; }
[[ $EUID -eq 0 ]] || fail 'Installer must run as root.'
command -v apt-get >/dev/null || fail 'This installer requires Debian/Ubuntu.'
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
cat <<BANNER
╔══════════════════════════════════════════════════════════╗
║                    VEXORA ${VERSION}                         ║
║       Configuration Shop • Admin • SSL • Backup          ║
╚══════════════════════════════════════════════════════════╝
BANNER
echo; echo 'Public access mode:'; echo '  1) Domain + HTTPS (Recommended)'; echo '  2) IP + HTTPS'; echo '  3) HTTP :8080'
while :; do read -r -p 'Select [1-3]: ' MODE; case "${MODE// /}" in 1|2|3) MODE=${MODE// /}; break;; *) echo '[ FAIL ] Invalid mode.';; esac; done
is_domain(){ [[ "$1" =~ ^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,63}$ ]] && [[ "$1" != *..* ]]; }
is_ip(){ local IFS=.; read -ra a <<< "$1"; ((${#a[@]}==4)) || return 1; for x in "${a[@]}"; do [[ "$x" =~ ^[0-9]{1,3}$ ]] && ((10#$x<=255)) || return 1; done; }
PUBLIC_HOST=''; SCHEME=http; PUBLIC_PORT=$HTTP_PORT
if [[ $MODE == 1 ]]; then while :; do read -r -p 'Enter your domain: ' PUBLIC_HOST; PUBLIC_HOST=${PUBLIC_HOST//[[:space:]]/}; is_domain "$PUBLIC_HOST" && break; echo '[ FAIL ] Invalid domain.'; done; SCHEME=https; PUBLIC_PORT=$HTTPS_PORT
else while :; do read -r -p 'Enter your public IPv4 address: ' PUBLIC_HOST; PUBLIC_HOST=${PUBLIC_HOST//[[:space:]]/}; is_ip "$PUBLIC_HOST" && break; echo '[ FAIL ] Invalid IPv4.'; done; if [[ $MODE == 2 ]]; then SCHEME=https; PUBLIC_PORT=$HTTPS_PORT; fi; fi
info 'Installing required packages...'; export DEBIAN_FRONTEND=noninteractive
apt-get update -qq; apt-get install -y -qq python3 python3-venv python3-pip nginx curl openssl rsync >/dev/null
id vexora >/dev/null 2>&1 || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin vexora
mkdir -p "$CONFIG_DIR" "$DATA_DIR" "$LOG_DIR" "$APP_DIR"
info 'Installing VEXORA source...'; TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
if [[ -f "$SCRIPT_DIR/app/main.py" && -f "$SCRIPT_DIR/requirements.txt" ]]; then
  SRC=$SCRIPT_DIR
else
  curl -fsSL --retry 4 "$REPO/archive/refs/heads/main.tar.gz" -o "$TMP/v.tar.gz"
  tar -xzf "$TMP/v.tar.gz" -C "$TMP"
  SRC="$TMP/VEXORA-main"
fi
[[ -f "$SRC/app/main.py" && -f "$SRC/requirements.txt" ]] || fail 'Incomplete VEXORA source.'
REQUIRED_SOURCE_FILES=(scripts/backup.sh scripts/update.sh scripts/uninstall.sh scripts/restore.sh scripts/vexora scripts/health-check.sh systemd/vexora-backup.service systemd/vexora-backup.timer)
for rel in "${REQUIRED_SOURCE_FILES[@]}"; do
  [[ -f "$SRC/$rel" ]] || fail "Incomplete VEXORA source: missing $rel. Upload the complete VEXORA project to GitHub."
done
# Never delete the installer source when it is being executed from the app directory.
if [[ "$SRC" != "$APP_DIR" ]]; then
  rm -rf "$APP_DIR"
  mkdir -p "$APP_DIR"
else
  find "$APP_DIR" -mindepth 1 -maxdepth 1 ! -name '.venv' ! -name 'first-login' -exec rm -rf {} +
fi
cp -a "$SRC/." "$APP_DIR/"; rm -rf "$APP_DIR/.venv" "$APP_DIR/app/__pycache__" "$APP_DIR/app/routes/__pycache__" "$APP_DIR/app/services/__pycache__"; find "$APP_DIR" -name '*.pyc' -delete
python3 -m venv "$APP_DIR/.venv"; "$APP_DIR/.venv/bin/pip" install -q --upgrade pip wheel; "$APP_DIR/.venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"
SECRET=$($APP_DIR/.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(48))'); ADMIN_USER=owner; ADMIN_PASS=$($APP_DIR/.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(18))'); COOKIE_SECURE=false; [[ $SCHEME == https ]] && COOKIE_SECURE=true
printf 'USERNAME=%s\nPASSWORD=%s\n' "$ADMIN_USER" "$ADMIN_PASS" > "$APP_DIR/first-login"; chmod 600 "$APP_DIR/first-login"; chown vexora:vexora "$APP_DIR/first-login"
cat > "$CONFIG_DIR/.env" <<EOF
# VEXORA Configuration — version ${VERSION}
VEXORA_VERSION=${VERSION}
VEXORA_HOST=127.0.0.1
VEXORA_PORT=${INTERNAL_PORT}
VEXORA_PUBLIC_HOST=${PUBLIC_HOST}
VEXORA_PUBLIC_PORT=${PUBLIC_PORT}
VEXORA_PUBLIC_SCHEME=${SCHEME}
VEXORA_SHOP_PATH=/shop/
VEXORA_ADMIN_PATH=/admin/
VEXORA_HEALTH_PATH=/health
VEXORA_CONFIG_DIR=${CONFIG_DIR}
VEXORA_DATA_DIR=${DATA_DIR}
VEXORA_LOG_DIR=${LOG_DIR}
VEXORA_SECRET_KEY=${SECRET}
VEXORA_SESSION_HOURS=24
VEXORA_MAX_UPLOAD_MB=10
VEXORA_COOKIE_SECURE=${COOKIE_SECURE}
VEXORA_SSL_ENABLED=false
VEXORA_SSL_CERTFILE=
VEXORA_SSL_KEYFILE=
VEXORA_LOG_LEVEL=INFO
VEXORA_DEBUG=false
VEXORA_TELEGRAM_BOT_TOKEN=
VEXORA_TELEGRAM_CHAT_ID=
VEXORA_BACKUP_ENABLED=true
VEXORA_BACKUP_KEEP=7
VEXORA_LOGIN_RATE_LIMIT=8
EOF
chmod 600 "$CONFIG_DIR/.env"
chown -R vexora:vexora "$APP_DIR" "$DATA_DIR" "$LOG_DIR"
cat > /etc/systemd/system/vexora.service <<EOF
[Unit]
Description=VEXORA Configuration Shop
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=vexora
Group=vexora
WorkingDirectory=$APP_DIR
EnvironmentFile=$CONFIG_DIR/.env
ExecStart=$APP_DIR/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port $INTERNAL_PORT --proxy-headers --forwarded-allow-ips=127.0.0.1
Restart=always
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ReadWritePaths=$DATA_DIR $LOG_DIR $CONFIG_DIR
[Install]
WantedBy=multi-user.target
EOF
mkdir -p /var/www/vexora-acme/.well-known/acme-challenge
rm -f /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/vexora.conf /etc/nginx/sites-enabled/vexora-ssl.conf /etc/nginx/sites-enabled/vexora-acme.conf
cat > /etc/nginx/sites-available/vexora.conf <<EOF
server {
 listen ${HTTP_PORT}; listen [::]:${HTTP_PORT}; server_name ${PUBLIC_HOST};
 client_max_body_size 10M;
 gzip on; gzip_comp_level 5; gzip_min_length 1024; gzip_types text/plain text/css application/json application/javascript application/xml image/svg+xml;
 location /.well-known/acme-challenge/ { root /var/www/vexora-acme; }
 location /static/ { proxy_pass http://127.0.0.1:${INTERNAL_PORT}; proxy_http_version 1.1; proxy_set_header Host \$host; proxy_set_header X-Forwarded-Proto \$scheme; expires 7d; add_header Cache-Control "public, max-age=604800, immutable"; }
 location / { proxy_pass http://127.0.0.1:${INTERNAL_PORT}; proxy_http_version 1.1; proxy_set_header Host \$host; proxy_set_header X-Real-IP \$remote_addr; proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto \$scheme; proxy_set_header X-Forwarded-Host \$host; add_header X-Content-Type-Options nosniff always; add_header X-Frame-Options SAMEORIGIN always; add_header Referrer-Policy strict-origin-when-cross-origin always; }
}
EOF
ln -sf /etc/nginx/sites-available/vexora.conf /etc/nginx/sites-enabled/vexora.conf
systemctl daemon-reload; systemctl enable --now vexora; nginx -t; systemctl enable --now nginx; systemctl reload nginx
CERT_OK=false; HTTPS_ACTIVE=false; CERT_FILE=''; KEY_FILE=''; PORT80_AVAILABLE=true
if [[ $MODE == 1 || $MODE == 2 ]]; then
 info 'Installing Certbot...'; apt-get install -y -qq certbot >/dev/null || warn 'Certbot installation failed.'
 if command -v certbot >/dev/null; then
  PORT80_OWNER=$(ss -lntp 2>/dev/null | awk '$4 ~ /(^|:)80$/ {print $NF}' | head -n1 || true)
  if [[ -z "$PORT80_OWNER" ]]; then
    cat > /etc/nginx/sites-available/vexora-acme.conf <<EOF
server { listen 80; listen [::]:80; server_name ${PUBLIC_HOST}; location /.well-known/acme-challenge/ { root /var/www/vexora-acme; } location / { return 404; } }
EOF
    ln -sf /etc/nginx/sites-available/vexora-acme.conf /etc/nginx/sites-enabled/vexora-acme.conf; nginx -t && systemctl reload nginx
  elif systemctl is-active --quiet nginx; then
    # Nginx already owns port 80: add an exact-host ACME server block instead of failing.
    cat > /etc/nginx/sites-available/vexora-acme.conf <<EOF
server { listen 80; listen [::]:80; server_name ${PUBLIC_HOST}; location /.well-known/acme-challenge/ { root /var/www/vexora-acme; } location / { return 404; } }
EOF
    ln -sf /etc/nginx/sites-available/vexora-acme.conf /etc/nginx/sites-enabled/vexora-acme.conf; nginx -t && systemctl reload nginx
  else
    warn "Port 80 is occupied by another service ($PORT80_OWNER); ACME HTTP-01 cannot run."
    PORT80_AVAILABLE=false
  fi
  if [[ $MODE == 1 ]]; then
    if certbot certonly --webroot -w /var/www/vexora-acme --non-interactive --agree-tos --register-unsafely-without-email --keep-until-expiring --cert-name "$PUBLIC_HOST" -d "$PUBLIC_HOST" >/tmp/vexora-cert.log 2>&1; then CERT_OK=true; else warn 'Domain certificate issuance failed; see /tmp/vexora-cert.log.'; fi
  else
    CERTBOT_OK=false
    if certbot --version 2>&1 | awk '{print $2}' | awk -F. '{exit !($1>5 || ($1==5 && $2>=4))}'; then
      if certbot certonly --webroot -w /var/www/vexora-acme --non-interactive --agree-tos --register-unsafely-without-email --keep-until-expiring --preferred-profile shortlived --cert-name "$PUBLIC_HOST" --ip-address "$PUBLIC_HOST" >/tmp/vexora-cert.log 2>&1; then CERT_OK=true; else warn 'IP certificate issuance failed; see /tmp/vexora-cert.log.'; fi
    else warn 'Certbot 5.4+ is required for IP certificates.'; fi
  fi
 else warn 'Port 80 is unavailable; ACME HTTP-01 cannot run.'; fi
fi
if $CERT_OK; then CERT_FILE="/etc/letsencrypt/live/$PUBLIC_HOST/fullchain.pem"; KEY_FILE="/etc/letsencrypt/live/$PUBLIC_HOST/privkey.pem"; [[ -f "$CERT_FILE" && -f "$KEY_FILE" ]] || CERT_OK=false; fi
if $CERT_OK && ! ss -lnt 2>/dev/null | awk '{print $4}' | grep -Eq '(^|:)443$'; then
 cat > /etc/nginx/sites-available/vexora-ssl.conf <<EOF
server { listen 443 ssl; listen [::]:443 ssl; server_name ${PUBLIC_HOST}; ssl_certificate ${CERT_FILE}; ssl_certificate_key ${KEY_FILE}; ssl_protocols TLSv1.2 TLSv1.3; ssl_session_cache shared:VEXORA_SSL:10m; add_header Strict-Transport-Security "max-age=31536000" always; add_header X-Content-Type-Options nosniff always; add_header X-Frame-Options SAMEORIGIN always; location / { proxy_pass http://127.0.0.1:${INTERNAL_PORT}; proxy_http_version 1.1; proxy_set_header Host \$host; proxy_set_header X-Real-IP \$remote_addr; proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto https; proxy_set_header X-Forwarded-Host \$host; } }
EOF
 ln -sf /etc/nginx/sites-available/vexora-ssl.conf /etc/nginx/sites-enabled/vexora-ssl.conf; nginx -t && systemctl reload nginx
 sed -i "s#VEXORA_PUBLIC_PORT=.*#VEXORA_PUBLIC_PORT=443#; s#VEXORA_PUBLIC_SCHEME=.*#VEXORA_PUBLIC_SCHEME=https#; s#VEXORA_SSL_ENABLED=.*#VEXORA_SSL_ENABLED=true#; s#VEXORA_SSL_CERTFILE=.*#VEXORA_SSL_CERTFILE=$CERT_FILE#; s#VEXORA_SSL_KEYFILE=.*#VEXORA_SSL_KEYFILE=$KEY_FILE#; s#VEXORA_COOKIE_SECURE=.*#VEXORA_COOKIE_SECURE=true#" "$CONFIG_DIR/.env"; HTTPS_ACTIVE=true; systemctl restart vexora
else
  warn 'HTTPS is not active; HTTP :8080 remains available.'
  # Keep runtime/public URL settings consistent with the actual listener.
  sed -i "s#VEXORA_PUBLIC_PORT=.*#VEXORA_PUBLIC_PORT=${HTTP_PORT}#; s#VEXORA_PUBLIC_SCHEME=.*#VEXORA_PUBLIC_SCHEME=http#; s#VEXORA_SSL_ENABLED=.*#VEXORA_SSL_ENABLED=false#; s#VEXORA_SSL_CERTFILE=.*#VEXORA_SSL_CERTFILE=#; s#VEXORA_SSL_KEYFILE=.*#VEXORA_SSL_KEYFILE=#; s#VEXORA_COOKIE_SECURE=.*#VEXORA_COOKIE_SECURE=false#" "$CONFIG_DIR/.env"
fi
if ! $HTTPS_ACTIVE; then CERT_PUBLIC='not-active'; else CERT_PUBLIC="$CERT_FILE"; fi
mkdir -p /etc/letsencrypt/renewal-hooks/deploy /usr/local/lib/vexora
cat > /etc/letsencrypt/renewal-hooks/deploy/vexora-nginx-reload.sh <<'EOF'
#!/usr/bin/env bash
systemctl reload nginx
EOF
chmod 755 /etc/letsencrypt/renewal-hooks/deploy/vexora-nginx-reload.sh
REQUIRED_SCRIPTS=(backup.sh update.sh uninstall.sh restore.sh vexora health-check.sh)
for helper in "${REQUIRED_SCRIPTS[@]}"; do
  [[ -f "$APP_DIR/scripts/$helper" ]] || fail "VEXORA source is missing scripts/$helper. Upload the complete project to GitHub before using the one-line installer."
done
[[ -f "$APP_DIR/systemd/vexora-backup.service" && -f "$APP_DIR/systemd/vexora-backup.timer" ]] || fail 'VEXORA source is missing backup systemd units.'
cp "$APP_DIR/scripts/backup.sh" "$APP_DIR/scripts/update.sh" "$APP_DIR/scripts/uninstall.sh" "$APP_DIR/scripts/restore.sh" /usr/local/lib/vexora/
cp "$APP_DIR/scripts/vexora" /usr/local/bin/vexora; chmod 755 /usr/local/bin/vexora
cp "$APP_DIR/systemd/vexora-backup.service" /etc/systemd/system/vexora-backup.service; cp "$APP_DIR/systemd/vexora-backup.timer" /etc/systemd/system/vexora-backup.timer
systemctl daemon-reload; systemctl enable --now vexora-backup.timer
PUBLIC_URL="http://${PUBLIC_HOST}:${HTTP_PORT}"; $HTTPS_ACTIVE && PUBLIC_URL="https://${PUBLIC_HOST}"
cat > "$CONFIG_DIR/INSTALLATION.txt" <<EOF
VEXORA_VERSION=${VERSION}
PUBLIC_URL=${PUBLIC_URL}
SHOP_URL=${PUBLIC_URL}/shop/
ADMIN_URL=${PUBLIC_URL}/admin/
USERNAME=${ADMIN_USER}
CONFIG=/etc/vexora/.env
CERT=${CERT_FILE:-not-issued}
CERT_STATUS=$([[ "$HTTPS_ACTIVE" == true ]] && echo active || echo not-issued)
KEY=${KEY_FILE:-not-issued}
EOF
chmod 600 "$CONFIG_DIR/INSTALLATION.txt"
rm -f "$APP_DIR/first-login"
sleep 2
if ! curl -fsS --max-time 8 -H "Host: $PUBLIC_HOST" http://127.0.0.1:${HTTP_PORT}/shop/ >/dev/null; then fail 'Nginx public HTTP route check failed.'; fi
if ! curl -fsS --max-time 8 -H "Host: $PUBLIC_HOST" http://127.0.0.1:${HTTP_PORT}/static/css/app.css >/dev/null; then fail 'Nginx public static route check failed.'; fi
if $HTTPS_ACTIVE; then curl -kfsS --max-time 8 -H "Host: $PUBLIC_HOST" https://127.0.0.1:${HTTPS_PORT}/shop/ >/dev/null || fail 'Nginx public HTTPS route check failed.'; fi
if ! "$APP_DIR/scripts/health-check.sh"; then journalctl -u vexora -n 80 --no-pager; fail 'Installation failed health checks.'; fi
ok 'Installation completed successfully.'
printf '%s\n' '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
printf '🌐 Public : %s\n🛒 Shop   : %s/shop/\n🔐 Admin  : %s/admin/\n👤 User   : %s\n🔑 Pass   : %s\n📜 Cert   : %s\n📜 Public : %s\n⚙ Config : %s\n📄 Info   : %s\n🧩 CLI    : vexora\n' "$PUBLIC_URL" "$PUBLIC_URL" "$PUBLIC_URL" "$ADMIN_USER" "$ADMIN_PASS" "${CERT_FILE:-not-issued}" "${CERT_PUBLIC:-not-active}" "$CONFIG_DIR/.env" "$CONFIG_DIR/INSTALLATION.txt"
printf '%s\n' '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
