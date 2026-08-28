from cryptography.fernet import Fernet
from .config import settings
import base64, hashlib

def key():
    return base64.urlsafe_b64encode(hashlib.sha256(settings.secret_key.encode()).digest())
def encrypt(s): return Fernet(key()).encrypt(s.encode()).decode()
def decrypt(s): return Fernet(key()).decrypt(s.encode()).decode()
