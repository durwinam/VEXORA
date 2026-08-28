from fastapi import FastAPI,Request,Form,HTTPException
from fastapi.responses import HTMLResponse,RedirectResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.core import settings,ensure_secrets
from app.db import init_db,SessionLocal,Admin,Panel,Product,Audit
from app.security import hash_password,verify_password,encrypt,decrypt
from app.services.providers import XUI,Marzban,PasarGuard
from sqlalchemy import select
import secrets, re
ensure_secrets(); init_db()
app=FastAPI(title='VEXORA',version=settings.version)
app.mount('/static',StaticFiles(directory='app/static'),name='static')

def audit(req,actor,action,detail=''):
    db=SessionLocal(); db.add(Audit(actor=actor,action=action,ip=req.client.host if req.client else '',detail=detail)); db.commit(); db.close()

def ensure_owner():
    db=SessionLocal(); owner=db.scalar(select(Admin).where(Admin.role=='owner'))
    if not owner:
        u='owner'; p=secrets.token_urlsafe(10); owner=Admin(username=u,password_hash=hash_password(p),role='owner',path='/admin-'+secrets.token_hex(8)); db.add(owner); db.commit(); print(f'VEXORA OWNER USERNAME={u} PASSWORD={p} PATH={owner.path}')
    db.close()
ensure_owner()
@app.get('/health')
async def health(): return {'status':'ok','version':settings.version}
@app.get(settings.shop_path, response_class=HTMLResponse)
async def shop(): return HTMLResponse('<!doctype html><html lang="fa"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>VEXORA</title><link rel="stylesheet" href="/static/style.css"></head><body><main><h1>VEXORA</h1><p>فروشگاه کانفیگ</p><div class="card">محصولات شما اینجا نمایش داده می‌شوند.</div><footer>© 2026 durwinam • VEXORA v'+settings.version+'</footer></main></body></html>')
@app.post('/api/login')
async def login(request:Request,username:str=Form(...),password:str=Form(...)):
    db=SessionLocal(); a=db.scalar(select(Admin).where(Admin.username==username,Admin.active==True)); ok=bool(a and verify_password(a.password_hash,password)); db.close(); audit(request,username,'login_success' if ok else 'login_failed');
    if not ok: raise HTTPException(401,'Invalid credentials')
    return {'ok':True,'admin_path':a.path}
@app.get('/api/panels/{panel_id}/health')
async def panel_health(panel_id:int):
    db=SessionLocal(); p=db.get(Panel,panel_id)
    if not p: db.close(); raise HTTPException(404,'panel not found')
    creds=decrypt(p.credential_blob); db.close(); c=__import__('json').loads(creds); k=p.kind.lower()
    if k in ('3x-ui','3xui','sanaei'): obj=XUI(p.base_url,c['token'])
    elif k=='marzban': obj=Marzban(p.base_url,c['username'],c['password'])
    else: obj=PasarGuard(p.base_url,c['token'])
    try:return {'ok':True,'kind':k,'data':await obj.health()}
    except Exception as e:return JSONResponse({'ok':False,'error':str(e)},502)
