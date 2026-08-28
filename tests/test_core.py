import os
os.environ['VEXORA_DATA_DIR']='/tmp/vexora-test-data'
os.environ['VEXORA_CONFIG_DIR']='/tmp/vexora-test-config'
os.environ['VEXORA_LOG_DIR']='/tmp/vexora-test-log'
from app.security import generate_secret, make_token, read_token

def test_token_roundtrip():
    secret=generate_secret()
    token=make_token(secret, 42, 1)
    data=read_token(secret, token)
    assert data and data['admin_id']==42
