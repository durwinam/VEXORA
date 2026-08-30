#!/usr/bin/env bash
set -Eeuo pipefail

VEXORA_VERSION="1.0.0"
REPO_RAW="https://raw.githubusercontent.com/durwinam/VEXORA/main"
TMP_DIR="$(mktemp -d /tmp/vexora-bootstrap.XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT

fail(){ echo "[ FAIL ] $*" >&2; exit 1; }
[[ "$EUID" -eq 0 ]] || fail "Run this installer as root."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT=""

# Full release installs use the bundled source; raw GitHub installs download it.
if [[ -d "${SCRIPT_DIR}/app" && -f "${SCRIPT_DIR}/requirements.txt" ]]; then
    SOURCE_ROOT="${SCRIPT_DIR}"
else
    command -v curl >/dev/null 2>&1 || { apt-get update -y && apt-get install -y curl ca-certificates; }
    command -v unzip >/dev/null 2>&1 || { apt-get update -y && apt-get install -y unzip; }

    SOURCE_URL="${VEXORA_SOURCE_URL:-${REPO_RAW}/source.zip}"
    echo "[VEXORA] Downloading complete VEXORA ${VEXORA_VERSION} source..."

    curl -fL --retry 4 --retry-delay 2 --connect-timeout 20 \
        "${SOURCE_URL}" \
        -o "${TMP_DIR}/source.zip" \
        || fail "Could not download VEXORA source archive."

    unzip -t "${TMP_DIR}/source.zip" >/dev/null \
        || fail "Downloaded VEXORA source archive is corrupt."

    mkdir -p "${TMP_DIR}/source"
    unzip -q "${TMP_DIR}/source.zip" -d "${TMP_DIR}/source"

    if [[ -d "${TMP_DIR}/source/app" ]]; then
        SOURCE_ROOT="${TMP_DIR}/source"
    else
        candidate="$(find "${TMP_DIR}/source" -type d -name app -print -quit 2>/dev/null || true)"
        [[ -n "${candidate}" ]] || fail "Downloaded VEXORA source is incomplete: app/ is missing."
        SOURCE_ROOT="$(dirname "${candidate}")"
    fi
fi

[[ -d "${SOURCE_ROOT}/app" ]] || fail "Incomplete VEXORA source: app/ is missing."
[[ -f "${SOURCE_ROOT}/scripts/install-core.sh" ]] || fail "Incomplete VEXORA source: scripts/install-core.sh is missing."

exec bash "${SOURCE_ROOT}/scripts/install-core.sh" "$@"
