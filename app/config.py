import os
from dataclasses import dataclass
from pathlib import Path


APP_VERSION = "1.0.0"


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("VEXORA_HOST", "0.0.0.0")
    port: int = int(os.getenv("VEXORA_PORT", "6000"))
    secret_key: str = os.getenv("VEXORA_SECRET_KEY", "")
    admin_username: str = os.getenv("VEXORA_ADMIN_USERNAME", "owner")
    admin_password_hash: str = os.getenv("VEXORA_ADMIN_PASSWORD_HASH", "")
    database_path: str = os.getenv(
        "VEXORA_DATABASE",
        "/var/lib/vexora/vexora.db",
    )


settings = Settings()
