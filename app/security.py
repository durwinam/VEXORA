import hashlib,hmac,secrets,time
from collections import defaultdict,deque
from passlib.context import CryptContext
pwd=CryptContext(schemes=["bcrypt"],deprecated="auto")
_attempts=defaultdict(deque)
def hash_password(p): return pwd.hash(p)
def verify_password(p,h):
    try:return pwd.verify(p,h)
    except Exception:return False
def make_token(secret,admin_id,hours):
    expiry=int(time.time())+hours*3600; body=f"{admin_id}:{expiry}:{secrets.token_urlsafe(24)}"; sig=hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest(); return f"{body}:{sig}"
def read_token(secret,token):
    try:
        admin_id,expiry,nonce,sig=token.split(":",3); body=f"{admin_id}:{expiry}:{nonce}"; expected=hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig,expected) or int(expiry)<int(time.time()): return None
        return {"admin_id":int(admin_id),"expires":int(expiry)}
    except Exception:return None
def generate_credentials(): return "owner",secrets.token_urlsafe(18)
def generate_secret(): return secrets.token_urlsafe(48)
def login_allowed(ip,limit):
    now=time.time(); q=_attempts[ip]
    while q and now-q[0]>60:q.popleft()
    if len(q)>=limit:return False
    q.append(now);return True
def clear_login_attempts(ip):_attempts.pop(ip,None)
