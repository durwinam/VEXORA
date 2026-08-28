from functools import lru_cache
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    version: str = Field('4.1.0', validation_alias='VEXORA_VERSION')
    host: str = Field('127.0.0.1', validation_alias='VEXORA_HOST')
    port: int = Field(6000, validation_alias='VEXORA_PORT', ge=1, le=65535)
    public_host: str = Field('', validation_alias='VEXORA_PUBLIC_HOST')
    public_port: int = Field(443, validation_alias='VEXORA_PUBLIC_PORT')
    public_scheme: str = Field('https', validation_alias='VEXORA_PUBLIC_SCHEME')
    base_path: str = Field('/', validation_alias='VEXORA_BASE_PATH')
    shop_path: str = Field('/shop/', validation_alias='VEXORA_SHOP_PATH')
    admin_path: str = Field('/admin/', validation_alias='VEXORA_ADMIN_PATH')
    health_path: str = Field('/health', validation_alias='VEXORA_HEALTH_PATH')
    config_dir: Path = Field(Path('/etc/vexora'), validation_alias='VEXORA_CONFIG_DIR')
    data_dir: Path = Field(Path('/var/lib/vexora'), validation_alias='VEXORA_DATA_DIR')
    log_dir: Path = Field(Path('/var/log/vexora'), validation_alias='VEXORA_LOG_DIR')
    secret_key: str = Field('', validation_alias='VEXORA_SECRET_KEY')
    session_hours: int = Field(24, validation_alias='VEXORA_SESSION_HOURS')
    max_upload_mb: int = Field(10, validation_alias='VEXORA_MAX_UPLOAD_MB')
    cookie_secure: bool = Field(True, validation_alias='VEXORA_COOKIE_SECURE')
    telegram_bot_token: str = Field('', validation_alias='VEXORA_TELEGRAM_BOT_TOKEN')
    telegram_chat_id: str = Field('', validation_alias='VEXORA_TELEGRAM_CHAT_ID')
    default_panel_kind: str = Field('generic', validation_alias='VEXORA_DEFAULT_PANEL_KIND')

    @field_validator('base_path', 'shop_path', 'admin_path', mode='before')
    @classmethod
    def normalize_path(cls, value: str) -> str:
        value = str(value or '/').strip()
        if not value.startswith('/'):
            value = '/' + value
        return value if value == '/' else value.rstrip('/') + '/'

    @property
    def db_path(self) -> Path:
        return self.data_dir / 'vexora.db'

    @property
    def public_url(self) -> str:
        if not self.public_host:
            return ''
        port = '' if (self.public_scheme == 'https' and self.public_port == 443) or (self.public_scheme == 'http' and self.public_port == 80) else f':{self.public_port}'
        return f'{self.public_scheme}://{self.public_host}{port}{"" if self.base_path == "/" else self.base_path.rstrip("/")}'

    def path(self, child: str) -> str:
        base = self.base_path.rstrip('/')
        child = '/' + child.strip('/')
        return (base + child + '/') if base else (child + '/')

@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.config_dir.mkdir(parents=True, exist_ok=True)
    s.data_dir.mkdir(parents=True, exist_ok=True)
    s.log_dir.mkdir(parents=True, exist_ok=True)
    return s

settings = get_settings()
