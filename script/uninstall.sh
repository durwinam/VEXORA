#!/usr/bin/env bash
set -e
systemctl disable --now vexora 2>/dev/null || true
rm -f /etc/systemd/system/vexora.service /usr/local/bin/vexora
rm -f /etc/nginx/sites-enabled/vexora.conf /etc/nginx/sites-available/vexora.conf
nginx -t >/dev/null 2>&1 && systemctl reload nginx || true
systemctl daemon-reload
printf 'VEXORA service and nginx configuration removed. Data/config were preserved under /var/lib/vexora and /etc/vexora.\n'
