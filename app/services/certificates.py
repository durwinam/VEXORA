from pathlib import Path
from .system import command_exists, run

LE_LIVE = Path('/etc/letsencrypt/live')


def cert_paths(host: str):
    root = LE_LIVE / host
    return root / 'fullchain.pem', root / 'privkey.pem'


def request_domain_certificate(domain: str, webroot: str = '/var/www/vexora-acme') -> dict:
    if not command_exists('certbot'):
        return {'ok': False, 'error': 'certbot is not installed'}
    result = run(['certbot', 'certonly', '--webroot', '-w', webroot, '--non-interactive', '--agree-tos', '--register-unsafely-without-email', '--keep-until-expiring', '-d', domain])
    return {'ok': result.returncode == 0, 'output': result.stdout + result.stderr}


def request_ip_certificate(ip: str, webroot: str = '/var/www/vexora-acme') -> dict:
    if not command_exists('certbot'):
        return {'ok': False, 'error': 'certbot is not installed'}
    result = run(['certbot', 'certonly', '--webroot', '-w', webroot, '--non-interactive', '--agree-tos', '--register-unsafely-without-email', '--keep-until-expiring', '--preferred-profile', 'shortlived', '--ip-address', ip])
    return {'ok': result.returncode == 0, 'output': result.stdout + result.stderr}
