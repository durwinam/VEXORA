#!/usr/bin/env bash

set -euo pipefail


systemctl disable --now vexora 2>/dev/null || true

rm -f /etc/systemd/system/vexora.service

systemctl daemon-reload


rm -f /etc/nginx/sites-enabled/vexora.conf
rm -f /etc/nginx/sites-available/vexora.conf


nginx -t
systemctl reload nginx || true


rm -rf /opt/vexora
rm -rf /var/lib/vexora
rm -rf /etc/vexora


if id vexora >/dev/null 2>&1; then
    userdel vexora || true
fi


echo "[ OK ] VEXORA removed."
