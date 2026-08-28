#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Run as root'; exit 1; }
APP=/opt/vexora
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv python3-pip curl ca-certificates
mkdir -p "$APP"; cp -a . "$APP/"; cd "$APP"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
[[ -f .env ]] || cp .env.example .env
mkdir -p data backups certificates
cat >/etc/systemd/system/vexora.service <<EOF
[Unit]
Description=VEXORA
After=network-online.target
Wants=network-online.target
[Service]
WorkingDirectory=$APP
EnvironmentFile=$APP/.env
ExecStart=$APP/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 6000
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=full
ReadWritePaths=$APP/data $APP/backups $APP/certificates
[Install]
WantedBy=multi-user.target
EOF
cat > /usr/local/bin/vexora <<'PY'
#!/usr/bin/env python3
import subprocess,sys
print('VEXORA CLI\n1) Health\n2) Website\n3) Service status\n4) Logs\n5) Restart\n6) Version\n0) Exit')
choice=input('> ').strip()
if choice=='1': subprocess.call(['curl','-fsS','http://127.0.0.1:6000/health'])
elif choice=='2': subprocess.call(['curl','-fsSI','http://127.0.0.1:6000/shop/'])
elif choice=='3': subprocess.call(['systemctl','status','vexora','--no-pager'])
elif choice=='4': subprocess.call(['journalctl','-u','vexora','-n','80','--no-pager'])
elif choice=='5': subprocess.call(['systemctl','restart','vexora'])
elif choice=='6': print('VEXORA v1.0.0')
PY
chmod +x /usr/local/bin/vexora
systemctl daemon-reload; systemctl enable --now vexora
sleep 2
curl -fsS http://127.0.0.1:6000/health
echo
