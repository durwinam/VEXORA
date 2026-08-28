import base64, hashlib, hmac, secrets, time
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

PBKDF2_ITERS = 310_000

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERS)
    return f"pbkdf2_sha256${PBKDF2_ITERS}${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(dk).decode()}"

def verify_password(password: str, encoded: str) -> bool:
    try:
        alg, iters, salt, digest = encoded.split("$", 3)
        if alg != "pbkdf2_sha256": return False
        salt_b = base64.urlsafe_b64decode(salt.encode())
        expected = base64.urlsafe_b64decode(digest.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt_b, int(iters))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

def token_signer(secret: str):
    return URLSafeTimedSerializer(secret, salt="vexora-session")

def make_session(secret: str, admin_id: int) -> str:
    return token_signer(secret).dumps({"admin_id": admin_id, "iat": int(time.time())})

def read_session(secret: str, token: str, max_age=86400):
    try:
        return token_signer(secret).loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
