from datetime import datetime
from pathlib import Path
import zipfile,os
from ..config import settings
def make_backup(include_env=True):
    settings.data_dir.mkdir(parents=True,exist_ok=True); out=settings.data_dir/f'vexora-backup-{datetime.now():%Y%m%d-%H%M%S}.zip'
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        if settings.db_path.exists():z.write(settings.db_path,'data/vexora.db')
        meta=settings.config_dir/'INSTALLATION.txt'
        if meta.exists():z.write(meta,'config/INSTALLATION.txt')
        env=settings.config_dir/'.env'
        if include_env and env.exists():z.write(env,'config/.env')
    os.chmod(out,0o600)
    files=sorted(settings.data_dir.glob('vexora-backup-*.zip'),key=lambda x:x.stat().st_mtime,reverse=True)
    for old in files[settings.backup_keep:]:
        try:old.unlink()
        except OSError:pass
    return out
