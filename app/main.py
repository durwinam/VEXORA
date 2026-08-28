from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .config import settings
from .db import init_db
from .security import generate_credentials, generate_secret, hash_password
from .db import one, execute
from .routes import auth, shop, admin

BASE=Path(__file__).resolve().parent
app=FastAPI(title='VEXORA Configuration Shop', version=settings.version, docs_url=None, redoc_url=None)
app.state.templates=Jinja2Templates(directory=str(BASE/'templates'))
app.mount('/static', StaticFiles(directory=str(BASE/'static')), name='static')

@app.on_event('startup')
def startup():
    init_db()
    if not settings.secret_key:
        # Installer normally supplies this. Development mode gets a local secret.
        settings.secret_key=generate_secret()
    if one('SELECT id FROM admins LIMIT 1') is None:
        credential_file = Path('/opt/vexora/first-login')
        username = password = None
        if credential_file.exists():
            values = {}
            for line in credential_file.read_text(encoding='utf-8').splitlines():
                if '=' in line:
                    key, value = line.split('=', 1)
                    values[key.strip()] = value.strip()
            username = values.get('USERNAME')
            password = values.get('PASSWORD')
            credential_file.unlink(missing_ok=True)
        if not username or not password:
            username, password = generate_credentials()
        execute(
            'INSERT INTO admins(username,password_hash,role) VALUES(?,?,?)',
            (username, hash_password(password), 'owner'),
        )

@app.get(settings.health_path)
def health():
    return {'status':'ok','version':settings.version,'bind':f'{settings.host}:{settings.port}','public':settings.public_url or None,'base_path':settings.base_path}

@app.get('/')
def root():
    return RedirectResponse(settings.shop_path)

app.include_router(shop.router)
app.include_router(auth.router)
app.include_router(admin.router)
