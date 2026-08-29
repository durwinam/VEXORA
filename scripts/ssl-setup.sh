#!/usr/bin/env bash
set -Eeuo pipefail

VEXORA_SSL_MODE="${VEXORA_SSL_MODE:-}"
VEXORA_DOMAIN="${VEXORA_DOMAIN:-}"
VEXORA_PUBLIC_IP="${VEXORA_PUBLIC_IP:-}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "        VEXORA 1.0.0 — SSL SETUP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "Select SSL certificate target:"
echo
echo "1) Domain"
echo "2) Public IP"
echo
read -r -p "Select [1/2]: " choice

case "$choice" in
  1)
    read -r -p "Enter your domain: " VEXORA_DOMAIN
    [[ -n "$VEXORA_DOMAIN" ]] || { echo "[ FAIL ] Domain is required."; exit 1; }
    VEXORA_SSL_MODE="domain"
    ;;
  2)
    read -r -p "Enter public IP: " VEXORA_PUBLIC_IP
    [[ -n "$VEXORA_PUBLIC_IP" ]] || { echo "[ FAIL ] Public IP is required."; exit 1; }
    VEXORA_SSL_MODE="ip"
    ;;
  *)
    echo "[ FAIL ] Invalid selection."
    exit 1
    ;;
esac

export VEXORA_SSL_MODE VEXORA_DOMAIN VEXORA_PUBLIC_IP
echo "[ OK ] SSL target selected: $VEXORA_SSL_MODE"
