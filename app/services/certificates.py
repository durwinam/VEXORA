from pathlib import Path
import subprocess
from .system import command_exists, run
from ..config import settings

CERT_ROOT = settings.config_dir / 'certificates'

def cert_paths(host: str):
    root = CERT_ROOT / host.replace('/', '_')
    return root / 'fullchain.pem', root / 'privkey.pem'

def request_domain_certificate(domain: str, webroot: str = '/var/www/vexora-acme') -> dict:
    if not command_exists('certbot'):
        return {'ok': False, 'error': 'certbot is not installed'}
    CERT_ROOT.mkdir(parents=True, exist_ok=True)
    result = run(['certbot', 'certonly', '--webroot', '-w', webroot, '-d', domain, '--non-interactive', '--agree-tos', '-m', f'admin@{domain}', '--keep-until-expiring'])
    return {'ok': result.returncode == 0, 'output': result.stdout + result.stderr}

def request_ip_certificate(ip: str, webroot: str = '/var/www/vexora-acme') -> dict:
    if not command_exists('certbot'):
        return {'ok': False, 'error': 'certbot is not installed'}
    result = run(['certbot', 'certonly', '--webroot', '-w', webroot, '--non-interactive', '--agree-tos', '-m', f'admin@{ip.replace(".", "-")}.invalid', '--preferred-challenges', 'http', '--ip-address', ip])
    return {'ok': result.returncode == 0, 'output': result.stdout + result.stderr}
