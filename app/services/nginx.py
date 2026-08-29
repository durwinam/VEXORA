from pathlib import Path
from ..config import settings
def nginx_config(host,public_port,upstream_port):
    return f'''server {{
    listen {public_port};
    server_name {host};
    client_max_body_size {settings.max_upload_mb}M;
    gzip on; gzip_comp_level 5; gzip_min_length 1024; gzip_types text/plain text/css application/json application/javascript application/xml image/svg+xml;
    location /.well-known/acme-challenge/ {{ root /var/www/vexora-acme; }}
    location /static/ {{ proxy_pass http://127.0.0.1:{upstream_port}; expires 7d; add_header Cache-Control "public, max-age=604800, immutable"; }}
    location / {{
        proxy_pass http://127.0.0.1:{upstream_port};
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        add_header X-Content-Type-Options nosniff always;
        add_header X-Frame-Options SAMEORIGIN always;
        add_header Referrer-Policy strict-origin-when-cross-origin always;
    }}
}}
'''
def write_config(host,port):
    target=Path('/etc/nginx/sites-available/vexora.conf');target.parent.mkdir(parents=True,exist_ok=True);target.write_text(nginx_config(host,port,settings.port));return target
