#!/usr/bin/env bash
set -u
APP_URL="${1:-http://127.0.0.1:6000}"
fail=0
printf '[1/5] systemd: '; systemctl is-active --quiet vexora && echo OK || { echo FAIL; fail=1; }
printf '[2/5] backend: '; curl -fsS "$APP_URL/health" >/dev/null && echo OK || { echo FAIL; fail=1; }
printf '[3/5] nginx syntax: '; nginx -t >/dev/null 2>&1 && echo OK || { echo FAIL; fail=1; }
printf '[4/5] port 6000: '; ss -lnt | grep -q ':6000 ' && echo OK || { echo FAIL; fail=1; }
printf '[5/5] config: '; test -f /etc/vexora/.env && echo OK || { echo FAIL; fail=1; }
exit "$fail"
