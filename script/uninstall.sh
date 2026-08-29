#!/usr/bin/env bash
set -Eeuo pipefail
systemctl disable --now vexora 2>/dev/null || true
systemctl disable --now vexora-backup.timer 2>/dev/null || true
rm -f /etc/systemd/system/vexora.service /etc/systemd/system/vexora-backup.service /etc/systemd/system/vexora-backup.timer /usr/local/bin/vexora
rm -f /etc/nginx/sites-enabled/vexora.conf /etc/nginx/sites-enabled/vexora-ssl.conf /etc/nginx/sites-enabled/vexora-acme.conf
rm -rf /usr/local/lib/vexora /opt/vexora
systemctl daemon-reload;nginx -t && systemctl reload nginx || true
echo 'VEXORA application removed; /etc/vexora and /var/lib/vexora preserved.'
