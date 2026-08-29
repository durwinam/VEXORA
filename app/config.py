from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

VERSION = "1.0.0"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("/etc/vexora/.env", ".env"), env_file_encoding="utf-8", extra="ignore")
    version: str = Field(VERSION, validation_alias="VEXORA_VERSION")
    host: str = Field("127.0.0.1", validation_alias="VEXORA_HOST")
    port: int = Field(6000, validation_alias="VEXORA_PORT")
    public_host: str = Field("", validation_alias="VEXORA_PUBLIC_HOST")
    public_port: int = Field(8080, validation_alias="VEXORA_PUBLIC_PORT")
    public_scheme: str = Field("http", validation_alias="VEXORA_PUBLIC_SCHEME")
    shop_path: str = "/shop/"
    admin_path: str = "/admin/"
    health_path: str = Field("/health", validation_alias="VEXORA_HEALTH_PATH")
    config_dir: Path = Field(Path("/etc/vexora"), validation_alias="VEXORA_CONFIG_DIR")
    data_dir: Path = Field(Path("/var/lib/vexora"), validation_alias="VEXORA_DATA_DIR")
    log_dir: Path = Field(Path("/var/log/vexora"), validation_alias="VEXORA_LOG_DIR")
    secret_key: str = Field("", validation_alias="VEXORA_SECRET_KEY")
    session_hours: int = Field(24, validation_alias="VEXORA_SESSION_HOURS")
    max_upload_mb: int = Field(10, validation_alias="VEXORA_MAX_UPLOAD_MB")
    cookie_secure: bool = Field(False, validation_alias="VEXORA_COOKIE_SECURE")
    ssl_enabled: bool = Field(False, validation_alias="VEXORA_SSL_ENABLED")
    ssl_certfile: str = Field("", validation_alias="VEXORA_SSL_CERTFILE")
    ssl_keyfile: str = Field("", validation_alias="VEXORA_SSL_KEYFILE")
    log_level: str = Field("INFO", validation_alias="VEXORA_LOG_LEVEL")
    debug: bool = Field(False, validation_alias="VEXORA_DEBUG")
    telegram_bot_token: str = Field("", validation_alias="VEXORA_TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field("", validation_alias="VEXORA_TELEGRAM_CHAT_ID")
    backup_enabled: bool = Field(True, validation_alias="VEXORA_BACKUP_ENABLED")
    backup_keep: int = Field(7, validation_alias="VEXORA_BACKUP_KEEP")
    rate_limit_per_minute: int = Field(8, validation_alias="VEXORA_LOGIN_RATE_LIMIT")

    @property
    def db_path(self): return self.data_dir / "vexora.db"
    @property
    def public_url(self):
        if not self.public_host: return ""
        default = (self.public_scheme == "https" and self.public_port == 443) or (self.public_scheme == "http" and self.public_port == 80)
        return f"{self.public_scheme}://{self.public_host}{'' if default else ':' + str(self.public_port)}"
    @property
    def static_path(self): return "/static/"
    def path(self, child): return "/" + child.strip("/") + "/"

@lru_cache
def get_settings():
    s=Settings(); s.config_dir.mkdir(parents=True,exist_ok=True); s.data_dir.mkdir(parents=True,exist_ok=True); s.log_dir.mkdir(parents=True,exist_ok=True); return s
settings=get_settings()
