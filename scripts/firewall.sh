#!/usr/bin/env bash
set -euo pipefail
# VEXORA: public web ports only; backend port 6000 is not publicly reachable.
if command -v ufw >/dev/null 2>&1; then
  ufw allow 22/tcp >/dev/null || true
  ufw allow 80/tcp >/dev/null || true
  ufw allow 443/tcp >/dev/null || true
  ufw allow 8080/tcp >/dev/null || true
  ufw deny 6000/tcp >/dev/null || true
fi
