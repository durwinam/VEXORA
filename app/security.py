from argon2 import PasswordHasher
from cryptography.fernet import Fernet
from app.core import settings
import base64,hashlib
ph=PasswordHasher()
def hash_password(p): return ph.hash(p)
def verify_password(h,p):
    try:return ph.verify(h,p)
    except Exception:return False
def fernet():
    key=base64.urlsafe_b64encode(hashlib.sha256(settings.credential_key.encode()).digest()); return Fernet(key)
def encrypt(v): return fernet().encrypt(v.encode()).decode()
def decrypt(v): return fernet().decrypt(v.encode()).decode()
