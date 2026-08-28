import os, tempfile
os.environ['VEXORA_SECRET_KEY']='test-secret-key-123456789'
from app.security import hash_password, verify_password, make_session, read_session

def test_password():
 h=hash_password('StrongPassword!123'); assert verify_password('StrongPassword!123',h); assert not verify_password('bad',h)
def test_session():
 t=make_session('test-secret-key-123456789',7); assert read_session('test-secret-key-123456789',t)['admin_id']==7
