#!/usr/bin/env bash

set -euo pipefail


BACKUP_DIR="/var/backups/vexora"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"


mkdir -p "${BACKUP_DIR}"


tar     --exclude='*.pyc'     -czf "${BACKUP_DIR}/vexora-${TIMESTAMP}.tar.gz"     /etc/vexora     /var/lib/vexora


echo "[ OK ] Backup created:"
echo "${BACKUP_DIR}/vexora-${TIMESTAMP}.tar.gz"
