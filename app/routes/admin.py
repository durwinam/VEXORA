from fastapi import APIRouter, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from pathlib import Path
import secrets
from ..config import settings
from ..db import all_rows, one, execute, audit
from ..crypto import encrypt
from ..security import read_token
from ..services.backup import make_backup
router = APIRouter()

def p(child=''): return settings.path(f'admin/{child}') if child else settings.admin_path

def render(request, template, **ctx):
    return request.app.state.templates.TemplateResponse(request=request, name=template, context={'settings':settings, 'request':request, **ctx})

def current(request):
    token=request.cookies.get('vexora_session')
    data=read_token(settings.secret_key, token) if token else None
    return one('SELECT * FROM admins WHERE id=? AND active=1', (data['admin_id'],)) if data else None

def require(request):
    admin=current(request)
    if not admin: return None
    return admin

@router.get(settings.admin_path, response_class=HTMLResponse)
def dashboard(request: Request):
    admin=require(request)
    if not admin: return render(request, 'login.html')
    stats={
        'plans': one('SELECT COUNT(*) n FROM plans')['n'],
        'orders': one('SELECT COUNT(*) n FROM orders')['n'],
        'pending_receipts': one("SELECT COUNT(*) n FROM receipts WHERE status='pending'")['n'],
        'panels': one('SELECT COUNT(*) n FROM panels')['n'],
    }
    return render(request, 'admin.html', admin_user=admin, stats=stats)

@router.get(p('panels'), response_class=HTMLResponse)
def panels(request: Request):
    a=require(request)
    if not a: return RedirectResponse(settings.admin_path, 303)
    return render(request, 'panels.html', admin_user=a, panels=all_rows('SELECT * FROM panels ORDER BY id DESC'))

@router.post(p('panels'))
def add_panel(request: Request, name: str=Form(...), kind: str=Form('generic'), base_url: str=Form(...), username: str=Form(''), password: str=Form(''), verify_tls: bool=Form(True)):
    a=require(request)
    if not a: return RedirectResponse(settings.admin_path, 303)
    if not base_url.startswith(('http://','https://')): raise HTTPException(422, 'Invalid panel URL')
    execute('INSERT INTO panels(name,kind,base_url,username,secret_enc,verify_tls) VALUES(?,?,?,?,?,?)', (name.strip(),kind.strip(),base_url.rstrip('/'),username.strip(),encrypt(settings.secret_key,password),int(verify_tls)))
    return RedirectResponse(p('panels'), 303)

@router.get(p('plans'), response_class=HTMLResponse)
def plans(request: Request):
    a=require(request)
    if not a: return RedirectResponse(settings.admin_path, 303)
    return render(request, 'plans.html', admin_user=a, plans=all_rows('SELECT p.*,pan.name panel_name FROM plans p JOIN panels pan ON pan.id=p.panel_id ORDER BY p.id DESC'), panels=all_rows('SELECT id,name FROM panels WHERE enabled=1'))

@router.post(p('plans'))
def add_plan(request: Request, name: str=Form(...), panel_id: int=Form(...), price: int=Form(...), volume_gb: float=Form(...), days: int=Form(...)):
    a=require(request)
    if not a: return RedirectResponse(settings.admin_path, 303)
    if not one('SELECT id FROM panels WHERE id=?', (panel_id,)): raise HTTPException(422,'Invalid panel')
    execute('INSERT INTO plans(name,panel_id,price,volume_gb,days) VALUES(?,?,?,?,?)', (name.strip(),panel_id,max(0,price),max(0,volume_gb),max(1,days)))
    return RedirectResponse(p('plans'), 303)

@router.get(p('receipts'), response_class=HTMLResponse)
def receipts(request: Request):
    a=require(request)
    if not a: return RedirectResponse(settings.admin_path, 303)
    rows=all_rows('SELECT r.*,o.customer_name,p.name plan_name FROM receipts r JOIN orders o ON o.id=r.order_id JOIN plans p ON p.id=o.plan_id ORDER BY r.id DESC')
    return render(request, 'receipts.html', admin_user=a, receipts=rows)

@router.post(p('receipts/{receipt_id}/approve'))
def approve(receipt_id:int, request:Request):
    a=require(request)
    if not a: return RedirectResponse(settings.admin_path,303)
    execute("UPDATE receipts SET status='approved',reviewed_by=?,reviewed_at=CURRENT_TIMESTAMP WHERE id=?", (a['id'],receipt_id))
    audit('receipt.approved',a['id'],f'receipt={receipt_id}')
    return RedirectResponse(p('receipts'),303)

@router.get(p('backup'))
def backup(request:Request):
    a=require(request)
    if not a: return RedirectResponse(settings.admin_path,303)
    return FileResponse(make_backup(), filename='vexora-backup.zip', media_type='application/zip')

@router.get(p('certificates'), response_class=HTMLResponse)
def certificates(request:Request):
    a=require(request)
    if not a: return RedirectResponse(settings.admin_path,303)
    return render(request,'certificates.html',admin_user=a)
