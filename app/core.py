from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import secrets
class Settings(BaseSettings):
    version:str='1.0.0'; host:str='0.0.0.0'; port:int=6000
    shop_path:str='/shop/'; admin_path:str='/admin/'
    database_url:str='sqlite:///./data/vexora.db'
    secret_key:str=''; credential_key:str=''; cookie_secure:bool=False
    model_config=SettingsConfigDict(env_file='.env',env_prefix='VEXORA_',extra='ignore')
settings=Settings()

def ensure_secrets():
    if not settings.secret_key or settings.secret_key=='CHANGE_ME':
        settings.secret_key=secrets.token_urlsafe(48)
    if not settings.credential_key:
        settings.credential_key=secrets.token_urlsafe(48)
