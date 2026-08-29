#!/usr/bin/env bash
set -Eeuo pipefail

VEXORA_VERSION="1.0.0"
VEXORA_REPO="https://github.com/durwinam/VEXORA"
VEXORA_BRANCH="main"
VEXORA_INSTALL_DIR="/opt/vexora"
VEXORA_TMP_DIR="/tmp/vexora-${VEXORA_VERSION}-$$"

log()  { printf '[VEXORA] %s\n' "$*"; }
ok()   { printf '[  OK  ] %s\n' "$*"; }
warn() { printf '[ WARN ] %s\n' "$*"; }
fail() { printf '[ FAIL ] %s\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || fail "Run this installer with sudo/root."

command -v curl >/dev/null 2>&1 || {
    apt-get update
    apt-get install -y curl ca-certificates
}

command -v unzip >/dev/null 2>&1 || {
    apt-get update
    apt-get install -y unzip
}

rm -rf "$VEXORA_TMP_DIR"
mkdir -p "$VEXORA_TMP_DIR"

ARCHIVE_URL="${VEXORA_REPO}/archive/refs/heads/${VEXORA_BRANCH}.zip"
ARCHIVE="$VEXORA_TMP_DIR/vexora-source.zip"

log "Downloading VEXORA ${VEXORA_VERSION} source..."
curl -fL --retry 3 --retry-delay 2 --connect-timeout 15 --max-time 300 \
    "$ARCHIVE_URL" -o "$ARCHIVE" || fail "Could not download VEXORA source."

unzip -q "$ARCHIVE" -d "$VEXORA_TMP_DIR/source" ||
    fail "Downloaded VEXORA archive could not be extracted."

SOURCE_ROOT="$(find "$VEXORA_TMP_DIR/source" -mindepth 1 -maxdepth 2 -type d -name app -print -quit | xargs -r dirname)"

[[ -n "$SOURCE_ROOT" && -d "$SOURCE_ROOT/app" ]] ||
    fail "Downloaded VEXORA source is incomplete: app/ is missing."

for required in \
    install.sh \
    app/main.py \
    scripts/backup.sh \
    scripts/restore.sh \
    scripts/update.sh \
    scripts/uninstall.sh
do
    [[ -e "$SOURCE_ROOT/$required" ]] ||
        fail "Downloaded VEXORA source is incomplete: $required is missing."
done

# Prevent recursive bootstrap execution: this block is the remote entry point.
if [[ "$SOURCE_ROOT" != "$VEXORA_INSTALL_DIR" ]]; then
    rm -rf "$VEXORA_INSTALL_DIR"
    mkdir -p "$VEXORA_INSTALL_DIR"
    cp -a "$SOURCE_ROOT"/. "$VEXORA_INSTALL_DIR"/
fi

chmod +x "$VEXORA_INSTALL_DIR"/install.sh
find "$VEXORA_INSTALL_DIR/scripts" -type f -name '*.sh' -exec chmod +x {} \;

# The downloaded source is now complete. Continue with the real installer.
export VEXORA_SOURCE_ROOT="$VEXORA_INSTALL_DIR"
export VEXORA_BOOTSTRAP_COMPLETE="1"

if [[ -f "$VEXORA_INSTALL_DIR/scripts/install-core.sh" ]]; then
    exec bash "$VEXORA_INSTALL_DIR/scripts/install-core.sh"
fi

# Backward-compatible fallback: execute the same installer with bootstrap guard.
if grep -q 'VEXORA_BOOTSTRAP_COMPLETE' "$VEXORA_INSTALL_DIR/install.sh"; then
    exec env VEXORA_BOOTSTRAP_COMPLETE=1 bash "$VEXORA_INSTALL_DIR/install.sh"
fi

fail "Core installer was not found in the downloaded VEXORA source."
