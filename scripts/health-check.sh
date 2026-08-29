#!/usr/bin/env bash
set -euo pipefail
curl -fsS --max-time 8 http://127.0.0.1:6000/health >/dev/null
curl -fsS --max-time 8 http://127.0.0.1:6000/shop/ >/dev/null
curl -fsS --max-time 8 http://127.0.0.1:6000/admin/ >/dev/null
curl -fsS --max-time 8 http://127.0.0.1:6000/static/css/app.css >/dev/null
nginx -t >/dev/null
echo 'VEXORA health: OK'
