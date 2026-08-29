#!/usr/bin/env bash

set -euo pipefail


BACKUP="${1:-}"


if [[ ! -f "${BACKUP}" ]]; then
    echo "Usage: $0 /path/to/backup.tar.gz" >&2
    exit 1
fi


systemctl stop vexora || true


tar     -xzf "${BACKUP}"     -C /


chown -R vexora:vexora /var/lib/vexora 2>/dev/null || true

chmod 0600 /etc/vexora/.env 2>/dev/null || true


systemctl start vexora


echo "[ OK ] Backup restored."
