import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    version: str = os.getenv("VEXORA_VERSION", "1.0.0")
    host: str = os.getenv("VEXORA_HOST", "0.0.0.0")
    port: int = int(os.getenv("VEXORA_PORT", "6000"))
    shop_path: str = os.getenv("VEXORA_SHOP_PATH", "/shop/").rstrip("/") + "/"
    admin_path: str = os.getenv("VEXORA_ADMIN_PATH", "/admin/").rstrip("/") + "/"
    secret_key: str = os.getenv("VEXORA_SECRET_KEY", "")
    db_path: str = os.getenv("VEXORA_DB", "/opt/vexora/data/vexora.db")
    max_upload_mb: int = int(os.getenv("VEXORA_MAX_UPLOAD_MB", "10"))
    owner_tg_id: str = os.getenv("VEXORA_OWNER_TELEGRAM_ID", "")
    tg_token: str = os.getenv("VEXORA_TELEGRAM_BOT_TOKEN", "")
    tg_chat: str = os.getenv("VEXORA_TELEGRAM_CHAT_ID", "")
    tg_topic: str = os.getenv("VEXORA_TELEGRAM_TOPIC_ID", "")
    backup_interval: float = float(os.getenv("VEXORA_BACKUP_INTERVAL_HOURS", "24"))

settings = Settings()
