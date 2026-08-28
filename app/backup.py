from pathlib import Path
from datetime import datetime, timezone
import zipfile, json, tempfile, os
from .config import settings
from .crypto import encrypt
from .db import db

def make_backup(outdir='/opt/vexora/backups'):
    Path(outdir).mkdir(parents=True,exist_ok=True)
    name=f"vexora-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.zip"; path=Path(outdir)/name
    with tempfile.TemporaryDirectory() as td:
        dbcopy=Path(td)/'vexora.db'
        with db() as c:
            dest=__import__('sqlite3').connect(dbcopy); c.backup(dest); dest.close()
        meta={'version':settings.version,'created_at':datetime.now(timezone.utc).isoformat(),'db':'vexora.db','note':'Secrets are encrypted with the VEXORA_SECRET_KEY-derived key.'}
        secrets={}
        with db() as c:
            for r in c.execute('SELECT id,name,kind,base_url,username,secret_enc,verify_tls FROM panels'):
                d=dict(r); d['secret']=encrypt(d.pop('secret_enc')) if d.get('secret_enc') else None; secrets[str(d['id'])]=d; d.pop('secret_enc',None)
        (Path(td)/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
        (Path(td)/'panel-secrets.enc.json').write_text(json.dumps(secrets,ensure_ascii=False))
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            z.write(dbcopy,'vexora.db'); z.write(Path(td)/'manifest.json','manifest.json'); z.write(Path(td)/'panel-secrets.enc.json','panel-secrets.enc.json')
    return str(path)
