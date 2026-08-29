from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import RedirectResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .config import settings
from .db import init_db,one,execute
from .security import generate_credentials,generate_secret,hash_password
from .routes import auth,shop,admin
VERSION="1.0.0"; BASE=Path(__file__).resolve().parent
app=FastAPI(title="VEXORA Configuration Shop",version=VERSION,docs_url=None,redoc_url=None)
app.state.templates=Jinja2Templates(directory=str(BASE/'templates'))
app.mount('/static',StaticFiles(directory=str(BASE/'static')),name='static')
@app.on_event('startup')
def startup():
    init_db()
    if not settings.secret_key: settings.secret_key=generate_secret()
    if one('SELECT id FROM admins LIMIT 1') is None:
        f=Path('/etc/vexora/first-login'); values={}
        if f.exists():
            for line in f.read_text(encoding='utf-8').splitlines():
                if '=' in line:
                    k,v=line.split('=',1); values[k.strip()]=v.strip()
            f.unlink(missing_ok=True)
        username=values.get('USERNAME'); password=values.get('PASSWORD')
        if not username or not password: username,password=generate_credentials()
        execute('INSERT INTO admins(username,password_hash,role) VALUES(?,?,?)',(username,hash_password(password),'owner'))
@app.get('/health')
def health(): return {'status':'ok','version':VERSION,'bind':f'{settings.host}:{settings.port}','public':settings.public_url or None,'shop':'/shop/','admin':'/admin/'}
@app.get('/')
def root(): return RedirectResponse('/shop/',302)
@app.exception_handler(404)
async def not_found(request,exc): return JSONResponse({'status':'not_found','path':request.url.path},status_code=404)
app.include_router(shop.router); app.include_router(auth.router); app.include_router(admin.router)
