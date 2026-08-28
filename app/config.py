import os
from dataclasses import dataclass

def norm(v, default):
    v=(v or default).strip()
    if not v.startswith("/"): v="/"+v
    return v.rstrip("/")+"/"

@dataclass(frozen=True)
class Settings:
    version:str=os.getenv("VEXORA_VERSION","2.0.0")
    host:str=os.getenv("VEXORA_HOST","127.0.0.1")
    port:int=int(os.getenv("VEXORA_PORT","6000"))
    base_path:str=norm(os.getenv("VEXORA_BASE_PATH","/vexora/"),"/vexora/")
    shop_path:str=norm(os.getenv("VEXORA_SHOP_PATH","/vexora/shop/"),"/vexora/shop/")
    admin_path:str=norm(os.getenv("VEXORA_ADMIN_PATH","/vexora/admin/"),"/vexora/admin/")
    health_path:str=os.getenv("VEXORA_HEALTH_PATH","/health").rstrip("/") or "/health"
    public_scheme:str=os.getenv("VEXORA_PUBLIC_SCHEME","https")
    public_host:str=os.getenv("VEXORA_PUBLIC_HOST","")
    public_port:int=int(os.getenv("VEXORA_PUBLIC_PORT","443"))
    ssl_certfile:str=os.getenv("VEXORA_SSL_CERTFILE","")
    ssl_keyfile:str=os.getenv("VEXORA_SSL_KEYFILE","")
    secret_key:str=os.getenv("VEXORA_SECRET_KEY","")
    db_path:str=os.getenv("VEXORA_DB","/opt/vexora/data/vexora.db")
    max_upload_mb:int=int(os.getenv("VEXORA_MAX_UPLOAD_MB","10"))
    owner_tg_id:str=os.getenv("VEXORA_OWNER_TELEGRAM_ID","")
    tg_token:str=os.getenv("VEXORA_TELEGRAM_BOT_TOKEN","")
    tg_chat:str=os.getenv("VEXORA_TELEGRAM_CHAT_ID","")
    tg_topic:str=os.getenv("VEXORA_TELEGRAM_TOPIC_ID","")
    backup_interval:float=float(os.getenv("VEXORA_BACKUP_INTERVAL_HOURS","24"))
settings=Settings()
