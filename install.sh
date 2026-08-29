VEXORA_VERSION="1.0.0"
#!/usr/bin/env bash

set -euo pipefail

VERSION="1.0.0"
INSTALL_DIR="/opt/vexora"
CONFIG_DIR="/etc/vexora"
DATA_DIR="/var/lib/vexora"
CERT_DIR="${CONFIG_DIR}/certs"
BACKEND_PORT="6000"

info() { echo "[VEXORA] $*"; }
ok() { echo "[  OK  ] $*"; }
warn() { echo "[ WARN ] $*" >&2; }
fail() { echo "[ FAIL ] $*" >&2; exit 1; }

root_check() {
    [[ "${EUID}" -eq 0 ]] || fail "Run this installer as root."
    command -v apt-get >/dev/null || fail "Debian/Ubuntu is required."
}

source_dir() {
    cd "$(dirname "$0")"
    pwd
}

packages() {
    info "Installing required packages..."
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get install -y \
        python3 \
        python3-venv \
        python3-pip \
        nginx \
        certbot \
        curl \
        ca-certificates \
        openssl \
        sqlite3
}

prepare() {
    local src
    src="$(source_dir)"

    [[ -d "${src}/app" ]] || fail "Incomplete VEXORA source: app/ is missing."
    [[ -f "${src}/requirements.txt" ]] || fail "requirements.txt is missing."
    [[ -d "${src}/scripts" ]] || fail "Incomplete VEXORA source: scripts/ is missing."

    install -d -m 0755 "${INSTALL_DIR}"
    install -d -m 0750 "${CONFIG_DIR}"
    install -d -m 0750 "${DATA_DIR}"
    install -d -m 0750 "${CERT_DIR}"
    install -d -m 0755 "${DATA_DIR}/acme"
    install -d -m 0750 /var/log/vexora

    if ! id vexora >/dev/null 2>&1; then
        useradd \
            --system \
            --home "${INSTALL_DIR}" \
            --shell /usr/sbin/nologin \
            vexora
    fi
}

generate_credentials() {
    ADMIN_PASSWORD="$(python3 - <<'PY'
import secrets
import string
alphabet = string.ascii_letters + string.digits
print(''.join(secrets.choice(alphabet) for _ in range(28)))
PY
)"

    SECRET_KEY="$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(64))
PY
)"

    ADMIN_HASH="$(python3 - "${ADMIN_PASSWORD}" <<'PY'
import hashlib
import secrets
import sys
password = sys.argv[1]
salt = secrets.token_hex(16)
digest = hashlib.pbkdf2_hmac(
    'sha256',
    password.encode(),
    salt.encode(),
    310000,
).hex()
print(f'pbkdf2_sha256$310000${salt}${digest}')
PY
)"
}

write_env() {
    cat > "${CONFIG_DIR}/.env" <<EOF2
VEXORA_VERSION=${VERSION}
VEXORA_APP_NAME=VEXORA
VEXORA_HOST=0.0.0.0
VEXORA_PORT=${BACKEND_PORT}
VEXORA_PUBLIC_URL=${PUBLIC_URL}
VEXORA_SECRET_KEY=${SECRET_KEY}
VEXORA_ADMIN_USERNAME=owner
VEXORA_ADMIN_PASSWORD_HASH=${ADMIN_HASH}
VEXORA_DATABASE=${DATA_DIR}/vexora.db
VEXORA_CERT_FILE=${CERT_DIR}/fullchain.pem
VEXORA_KEY_FILE=${CERT_DIR}/privkey.pem
VEXORA_SESSION_DAYS=2
VEXORA_LOG_LEVEL=INFO
EOF2

    chmod 0600 "${CONFIG_DIR}/.env"
}

install_source() {
    local src
    src="$(source_dir)"

    rm -rf "${INSTALL_DIR}/app" "${INSTALL_DIR}/scripts"
    cp -a "${src}/app" "${INSTALL_DIR}/app"
    cp -a "${src}/scripts" "${INSTALL_DIR}/scripts"
    cp "${src}/requirements.txt" "${INSTALL_DIR}/requirements.txt"

    python3 -m venv "${INSTALL_DIR}/.venv"

    "${INSTALL_DIR}/.venv/bin/pip" install \
        --disable-pip-version-check \
        --no-cache-dir \
        -r "${INSTALL_DIR}/requirements.txt"

    chown -R vexora:vexora "${INSTALL_DIR}"
}

identity() {
    echo
    echo "1) Domain"
    echo "2) Public IPv4"
    echo
    read -r -p "Certificate type [1-2]: " IDENTITY_MODE

    case "${IDENTITY_MODE}" in
        1)
            read -r -p "Domain: " CERT_ID
            [[ "${CERT_ID}" =~ ^[A-Za-z0-9.-]+$ ]] || fail "Invalid domain."
            PUBLIC_URL="https://${CERT_ID}"
            ;;
        2)
            read -r -p "Public IPv4: " CERT_ID
            [[ "${CERT_ID}" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] || fail "Invalid IPv4."
            PUBLIC_URL="https://${CERT_ID}"
            ;;
        *)
            fail "Invalid selection."
            ;;
    esac
}

certificate() {
    info "Obtaining mandatory Let's Encrypt certificate..."

    systemctl stop nginx 2>/dev/null || true

    if [[ "${IDENTITY_MODE}" == "1" ]]; then
        certbot certonly \
            --standalone \
            --non-interactive \
            --agree-tos \
            --register-unsafely-without-email \
            -d "${CERT_ID}" || fail "Domain certificate issuance failed."
    else
        local version
        version="$(certbot --version 2>&1 | awk '{print $2}')"

        python3 - "${version}" <<'PY' || fail "Certbot 5.4+ is required for IP certificates."
import sys
parts = []
for item in sys.argv[1].split('.')[:3]:
    digits = ''.join(c for c in item if c.isdigit())
    parts.append(int(digits or 0))
while len(parts) < 3:
    parts.append(0)
raise SystemExit(0 if tuple(parts) >= (5, 4, 0) else 1)
PY

        certbot certonly \
            --standalone \
            --non-interactive \
            --agree-tos \
            --register-unsafely-without-email \
            --preferred-profile shortlived \
            --ip-address "${CERT_ID}" || fail "IP certificate issuance failed."
    fi

    CERT_LIVE_DIR="/etc/letsencrypt/live/${CERT_ID}"

    [[ -s "${CERT_LIVE_DIR}/fullchain.pem" ]] || fail "Certificate file missing."
    [[ -s "${CERT_LIVE_DIR}/privkey.pem" ]] || fail "Private key missing."

    install -m 0644 "${CERT_LIVE_DIR}/fullchain.pem" "${CERT_DIR}/fullchain.pem"
    install -m 0600 "${CERT_LIVE_DIR}/privkey.pem" "${CERT_DIR}/privkey.pem"
}

alternate_port() {
    for port in 8443 9443 10443 2053 2083 2087 2096; do
        if ! ss -lnt | grep -qE ":${port}[[:space:]]"; then
            ALT_HTTPS_PORT="${port}"
            return
        fi
    done

    fail "No free HTTPS alternative port found."
}

nginx_config() {
    local src
    src="$(source_dir)"

    sed \
        -e "s/listen 8443 ssl/listen ${ALT_HTTPS_PORT} ssl/" \
        -e "s/listen \[::\]:8443 ssl/listen [::]:${ALT_HTTPS_PORT} ssl/" \
        "${src}/nginx/vexora.conf" \
        > /etc/nginx/sites-available/vexora.conf

    rm -f /etc/nginx/sites-enabled/default

    ln -sf \
        /etc/nginx/sites-available/vexora.conf \
        /etc/nginx/sites-enabled/vexora.conf

    nginx -t || fail "Nginx configuration test failed."
}

service_config() {
    local src
    src="$(source_dir)"

    install -m 0644 \
        "${src}/systemd/vexora.service" \
        /etc/systemd/system/vexora.service

    systemctl daemon-reload
}

database() {
    cd "${INSTALL_DIR}"
    set -a
    source "${CONFIG_DIR}/.env"
    set +a

    "${INSTALL_DIR}/.venv/bin/python" \
        -c "from app.database import initialize; initialize()" \
        || fail "Database initialization failed."
}

start_backend() {
    systemctl enable vexora
    systemctl restart vexora

    for _ in $(seq 1 25); do
        if curl \
            --fail \
            --silent \
            --show-error \
            --max-time 2 \
            "http://127.0.0.1:${BACKEND_PORT}/health" \
            >/dev/null; then
            return
        fi
        sleep 1
    done

    journalctl -u vexora -n 120 --no-pager >&2 || true
    fail "Backend health check failed."
}

start_nginx() {
    systemctl enable nginx
    systemctl restart nginx
    systemctl is-active --quiet nginx || fail "Nginx did not start."
}

public_check() {
    curl \
        --fail \
        --silent \
        --show-error \
        --max-time 15 \
        --resolve "${CERT_ID}:443:127.0.0.1" \
        "https://${CERT_ID}/shop/" \
        >/dev/null || fail "Public HTTPS shop check failed."

    curl \
        --fail \
        --silent \
        --show-error \
        --max-time 15 \
        --resolve "${CERT_ID}:${ALT_HTTPS_PORT}:127.0.0.1" \
        "https://${CERT_ID}:${ALT_HTTPS_PORT}/shop/" \
        >/dev/null || fail "Alternative HTTPS shop check failed."
}

report() {
    cat > "${CONFIG_DIR}/INSTALLATION.txt" <<EOF2
VEXORA ${VERSION}

Public : ${PUBLIC_URL}
Shop   : ${PUBLIC_URL}/shop/
Admin  : ${PUBLIC_URL}/admin/
HTTPS  : 443
HTTPS2 : ${ALT_HTTPS_PORT}
Backend: 0.0.0.0:${BACKEND_PORT}

User   : owner
Pass   : ${ADMIN_PASSWORD}

Cert   : ${CERT_DIR}/fullchain.pem
Config : ${CONFIG_DIR}/.env
EOF2

    chmod 0600 "${CONFIG_DIR}/INSTALLATION.txt"
}

main() {
    root_check
    packages
    prepare
    generate_credentials
    identity
    alternate_port
    write_env
    install_source
    database
    certificate
    service_config
    nginx_config
    start_backend
    start_nginx
    public_check
    report

    ok "Installation completed successfully."
    echo "Public : ${PUBLIC_URL}"
    echo "Shop   : ${PUBLIC_URL}/shop/"
    echo "Admin  : ${PUBLIC_URL}/admin/"
    echo "HTTPS  : 443"
    echo "HTTPS2 : ${ALT_HTTPS_PORT}"
    echo "User   : owner"
    echo "Pass   : ${ADMIN_PASSWORD}"
}

main "$@"

# SSL target selection
source "$SOURCE_ROOT/scripts/ssl-setup.sh"
