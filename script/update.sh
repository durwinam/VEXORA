#!/usr/bin/env bash
set -e
cd /opt/vexora
cp -a . /tmp/vexora-update-backup-$(date +%s)
"$PWD/.venv/bin/pip" install -r requirements.txt
systemctl restart vexora
curl -fsS http://127.0.0.1:6000/health
printf '\nUpdate completed.\n'
