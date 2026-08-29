#!/usr/bin/env bash

set -u

PASS=0
FAIL=0

check() {
    local label="$1"
    shift

    if "$@" >/dev/null 2>&1; then
        printf '[ OK ] %s\n' "$label"
        PASS=$((PASS + 1))
    else
        printf '[FAIL] %s\n' "$label"
        FAIL=$((FAIL + 1))
    fi
}

check "VEXORA service is active" systemctl is-active vexora
check "Nginx is active" systemctl is-active nginx
check "Backend health endpoint" curl --fail --silent --max-time 5 http://127.0.0.1:6000/health
check "Shop endpoint" curl --fail --silent --max-time 5 http://127.0.0.1:6000/shop/
check "Environment exists" test -s /etc/vexora/.env
check "Certificate exists" test -s /etc/vexora/certs/fullchain.pem
check "Private key exists" test -s /etc/vexora/certs/privkey.pem
check "Port 6000 is listening" bash -c 'ss -lnt | grep -q ":6000 "'
check "Port 8080 is not configured" bash -c '! grep -R "8080" /etc/nginx/sites-enabled/vexora.conf 2>/dev/null'

printf '\nPassed: %s\n' "$PASS"
printf 'Failed: %s\n' "$FAIL"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
