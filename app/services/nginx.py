from pathlib import Path
from ..config import settings

def nginx_config(host: str, public_port: int, upstream_port: int, base_path: str = '/') -> str:
    location = base_path.rstrip('/') if base_path != '/' else ''
    prefix = location + '/' if location else '/'
    return f'''server {{\n    listen {public_port};\n    server_name {host};\n\n    location /.well-known/acme-challenge/ {{\n        root /var/www/vexora-acme;\n    }}\n\n    location {prefix} {{\n        proxy_pass http://127.0.0.1:{upstream_port};\n        proxy_http_version 1.1;\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto $scheme;\n        proxy_set_header X-Forwarded-Prefix {prefix};\n    }}\n}}\n'''

def write_config(host: str, port: int, path: str = '/') -> Path:
    target = Path('/etc/nginx/sites-available/vexora.conf')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(nginx_config(host, port, settings.port, path), encoding='utf-8')
    return target
