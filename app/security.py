import hashlib
import hmac
import secrets
import time
from passlib.context import CryptContext

pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')

def hash_password(password: str) -> str:
    return pwd.hash(password)

def verify_password(password: str, encoded: str) -> bool:
    try:
        return pwd.verify(password, encoded)
    except Exception:
        return False

def make_token(secret: str, admin_id: int, hours: int) -> str:
    expiry = int(time.time()) + hours * 3600
    nonce = secrets.token_urlsafe(24)
    body = f'{admin_id}:{expiry}:{nonce}'
    sig = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f'{body}:{sig}'

def read_token(secret: str, token: str) -> dict | None:
    try:
        admin_id, expiry, nonce, sig = token.split(':', 3)
        body = f'{admin_id}:{expiry}:{nonce}'
        expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected) or int(expiry) < int(time.time()):
            return None
        return {'admin_id': int(admin_id), 'expires': int(expiry)}
    except (ValueError, TypeError):
        return None

def generate_credentials() -> tuple[str, str]:
    return 'owner', secrets.token_urlsafe(14)

def generate_secret() -> str:
    return secrets.token_urlsafe(48)
