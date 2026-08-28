from datetime import datetime
from pathlib import Path
import zipfile
from ..config import settings

def make_backup() -> Path:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    out = settings.data_dir / f'vexora-backup-{datetime.now():%Y%m%d-%H%M%S}.zip'
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        if settings.db_path.exists(): z.write(settings.db_path, 'data/vexora.db')
        env = Path('.env')
        if env.exists(): z.write(env, 'config/.env')
    return out
