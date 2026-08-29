#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[[ "$(grep -o "version = \"[0-9.]*\"" pyproject.toml | head -1)" == 'version = "1.0.0"' ]]
grep -q "VERSION=1.0.0" install.sh
grep -q '__version__ = '\''1.0.0'\''' app/__init__.py
grep -q 'VERSION="1.0.0"' app/main.py
grep -q 'VEXORA_SHOP_PATH=/shop/' install.sh
grep -q 'VEXORA_ADMIN_PATH=/admin/' install.sh
grep -q 'VEXORA_PORT=6000' install.sh
grep -q 'listen ${HTTP_PORT}' install.sh
grep -q 'listen 443 ssl' install.sh
grep -q 'certbot certonly --webroot' install.sh
! grep -q 'cp .*\.env.example' install.sh
! grep -q 'DASHBOARD_PATH' install.sh
test -f app/static/css/app.css
test -f app/static/js/app.js
test -f app/static/fonts/NotoKufiArabic-Regular.ttf
echo 'PASS: VEXORA 1.0.0 release audit'
