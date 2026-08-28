import base64, hashlib, hmac
from cryptography.fernet import Fernet, InvalidToken

def _key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(digest)

def encrypt(secret: str, value: str) -> str:
    return Fernet(_key(secret)).encrypt(value.encode()).decode()

def decrypt(secret: str, value: str) -> str:
    if not value: return ''
    try: return Fernet(_key(secret)).decrypt(value.encode()).decode()
    except InvalidToken: return ''
