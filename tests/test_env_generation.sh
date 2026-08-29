#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/install.sh"
bash -n "$SCRIPT"
grep -q 'cat > "$CONFIG_DIR/.env"' "$SCRIPT"
grep -q 'chmod 600 "$CONFIG_DIR/.env"' "$SCRIPT"
! grep -Eq 'cp .*\.env\.example' "$SCRIPT"
echo "PASS: .env is generated automatically"
