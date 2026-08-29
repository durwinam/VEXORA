#!/usr/bin/env bash

set -euo pipefail


BASE_URL="${1:-http://127.0.0.1:6000}"


curl     --fail     --silent     --show-error     --max-time 10     "${BASE_URL}/health"     >/dev/null


curl     --fail     --silent     --show-error     --max-time 10     "${BASE_URL}/shop/"     >/dev/null


echo "[ OK ] VEXORA health checks passed."
