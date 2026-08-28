#!/usr/bin/env bash
set -Eeuo pipefail

# VEXORA one-command installer
# Recommended:
# curl -fsSL https://raw.githubusercontent.com/durwinam/VEXORA/main/install.sh -o /tmp/vexora-install.sh && sudo bash /tmp/vexora-install.sh

REPO_RAW="https://raw.githubusercontent.com/durwinam/VEXORA/main"
APP_DIR="${VEXORA_APP_DIR:-/opt/vexora}"
SERVICE_NAME="vexora"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PORT="${VEXORA_PORT:-6000}"
HOST="${VEXORA_HOST:-0.0.0.0}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log(){ echo -e "${BLUE}[VEXORA]${NC} $*"; }
ok(){ echo -e "${GREEN}[OK]${NC} $*"; }
warn(){ echo -e "${YELLOW}[WARN]${NC} $*"; }
die(){ echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "Run with sudo: sudo bash /tmp/vexora-install.sh"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# If this script is run from a local clone/extracted package, use it.
# If downloaded as a standalone installer, bootstrap the repository files.
if [[ ! -f "$SCRIPT_DIR/requirements.txt" || ! -f "$SCRIPT_DIR/app/main.py" ]]; then
    command -v curl >/dev/null 2>&1 || die "curl is required."
    command -v python3 >/dev/null 2>&1 || die "Python 3 is required."

    TMP_ROOT="$(mktemp -d /tmp/vexora-bootstrap.XXXXXX)"
    trap 'rm -rf "$TMP_ROOT"' EXIT

    log "Downloading VEXORA release files from GitHub..."
    curl -fL --retry 3 --retry-delay 2 \
      "$REPO_RAW/requirements.txt" -o "$TMP_ROOT/requirements.txt"
    curl -fL --retry 3 --retry-delay 2 \
      "$REPO_RAW/.env.example" -o "$TMP_ROOT/.env.example"

    # GitHub tarball gives us the complete repository without requiring git.
    command -v tar >/dev/null 2>&1 || die "tar is required."
    curl -fL --retry 3 --retry-delay 2 \
      "https://github.com/durwinam/VEXORA/archive/refs/heads/main.tar.gz" \
      -o "$TMP_ROOT/vexora.tar.gz"

    tar -xzf "$TMP_ROOT/vexora.tar.gz" -C "$TMP_ROOT"
    SOURCE_DIR="$(find "$TMP_ROOT" -maxdepth 1 -type d -name 'VEXORA-*' -print -quit)"
    [[ -n "$SOURCE_DIR" && -f "$SOURCE_DIR/app/main.py" ]] || die "Downloaded VEXORA source is incomplete."
else
    SOURCE_DIR="$SCRIPT_DIR"
fi

command -v python3 >/dev/null 2>&1 || die "Python 3 is required."

if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    log "Installing system dependencies..."
    apt-get update -y
    apt-get install -y python3 python3-venv python3-pip curl ca-certificates openssl
else
    warn "apt-get not found; required system packages must already exist."
fi

log "Installing VEXORA into ${APP_DIR}..."
mkdir -p "$APP_DIR"

# Preserve runtime data and local secrets during reinstall/update.
if command -v rsync >/dev/null 2>&1; then
    rsync -a \
      --exclude '.venv/' \
      --exclude 'data/' \
      --exclude 'backups/' \
      --exclude '.env' \
      "$SOURCE_DIR/" "$APP_DIR/"
else
    cp -a "$SOURCE_DIR/." "$APP_DIR/"
fi

mkdir -p "$APP_DIR/data" "$APP_DIR/backups"
touch "$APP_DIR/backups/.gitkeep"
cd "$APP_DIR"

if [[ ! -d .venv ]]; then
    log "Creating Python virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if [[ ! -f .env ]]; then
    cp .env.example .env 2>/dev/null || touch .env
fi

python - <<'PY'
from pathlib import Path
import secrets

p = Path(".env")
lines = p.read_text(encoding="utf-8").splitlines() if p.exists() else []
data = {}
for line in lines:
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        data[k.strip()] = v

defaults = {
    "VEXORA_VERSION": "1.0.0",
    "VEXORA_HOST": "0.0.0.0",
    "VEXORA_PORT": "6000",
    "VEXORA_SHOP_PATH": "/shop/",
    "VEXORA_ADMIN_PATH": "/admin/",
}
if not data.get("VEXORA_SECRET_KEY") or data.get("VEXORA_SECRET_KEY") in {"CHANGE_ME", "CHANGE_ME_TO_A_LONG_RANDOM_VALUE"}:
    data["VEXORA_SECRET_KEY"] = secrets.token_urlsafe(64)

for k, v in defaults.items():
    data.setdefault(k, v)

p.write_text("".join(f"{k}={v}\n" for k, v in data.items()), encoding="utf-8")
PY

if ! id vexora >/dev/null 2>&1; then
    useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin vexora
fi

chown -R vexora:vexora "$APP_DIR"
chmod 750 "$APP_DIR"
chmod 700 "$APP_DIR/data" "$APP_DIR/backups"
chmod 600 "$APP_DIR/.env"

install -m 0755 "$APP_DIR/vexora.py" /usr/local/bin/vexora

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=VEXORA Configuration Shop
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=vexora
Group=vexora
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/.venv/bin/uvicorn app.main:app --host ${HOST} --port ${PORT}
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
ReadWritePaths=${APP_DIR}/data ${APP_DIR}/backups

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME" >/dev/null
systemctl restart "$SERVICE_NAME"

log "Running local health check..."
for _ in $(seq 1 30); do
    if curl -fsS --max-time 2 "http://127.0.0.1:${PORT}/health" >/tmp/vexora_health.json 2>/dev/null; then
        ok "VEXORA is running."
        cat /tmp/vexora_health.json
        echo
        ok "Shop: http://SERVER-IP:${PORT}/shop/"
        ok "Health: http://SERVER-IP:${PORT}/health"
        ok "CLI: vexora"
        exit 0
    fi
    sleep 1
done

systemctl --no-pager --full status "$SERVICE_NAME" || true
journalctl -u "$SERVICE_NAME" -n 80 --no-pager || true
die "VEXORA failed its local health check."
