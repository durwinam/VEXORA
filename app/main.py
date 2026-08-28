from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import secrets, re, os, qrcode
from .config import settings
from .db import init_db, one, q, exec, audit
from .security import hash_password, verify_password, make_session, read_session
from .crypto import encrypt, decrypt
from .providers import provider, ProviderError
from .telegram import notify, send_owner_document
from .backup import make_backup

app=FastAPI(title='VEXORA',version=settings.version)
app.mount(settings.base_path+'static/', StaticFiles(directory=Path(__file__).parent/'static'), name='static')

def boot():
    init_db()
    if not one('SELECT id FROM tenants LIMIT 1'):
        tid=exec('INSERT INTO tenants(name,slug) VALUES(?,?)',('VEXORA','main'))
        if not one('SELECT id FROM admins LIMIT 1'):
            u='owner'; p=secrets.token_urlsafe(10); exec('INSERT INTO admins(username,password_hash,role,tenant_id) VALUES(?,?,?,?)',(u,hash_password(p),'owner',tid))
            print(f'VEXORA FIRST LOGIN: username={u} password={p}')
boot()

def current(request):
    t=request.cookies.get('vexora_session')
    if not t or not settings.secret_key: return None
    d=read_session(settings.secret_key,t)
    if not d: return None
    return one('SELECT * FROM admins WHERE id=? AND active=1',(d['admin_id'],))

def require(request, roles=None):
    a=current(request)
    if not a: raise HTTPException(401,'Authentication required')
    if roles and a['role'] not in roles: raise HTTPException(403,'Forbidden')
    return a

def page(title,body):
    return HTMLResponse(f'''<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · VEXORA</title><link rel="stylesheet" href="{settings.base_path}static/css/app.css"></head><body><header><b>VEXORA</b><nav><a href="{settings.shop_path}">فروشگاه</a><a href="{settings.admin_path}">مدیریت</a></nav></header><main>{body}</main><footer>© durwinam · VEXORA v{settings.version}</footer></body></html>''')

@app.get(settings.health_path)
def health():
    return {'status':'ok','version':settings.version,'bind':f'{settings.host}:{settings.port}',
            'public': f'{settings.public_scheme}://{settings.public_host}{settings.base_path}' if settings.public_host else None}
@app.get('/',response_class=HTMLResponse)
def root(): return RedirectResponse(settings.shop_path)

@app.get(settings.shop_path,response_class=HTMLResponse)
def shop(request:Request):
    host=request.headers.get('host','').split(':')[0]
    tenant=one('SELECT * FROM tenants WHERE domain=? OR slug=? ORDER BY domain IS NULL',(host,host)) or one('SELECT * FROM tenants WHERE slug="main"')
    plans=q('SELECT p.*,pa.name panel_name FROM plans p JOIN panels pa ON pa.id=p.panel_id WHERE p.tenant_id=? AND p.enabled=1',(tenant['id'],)) if tenant else []
    cards=''.join(f'<div class="card"><h3>{p["name"]}</h3><p>{p["volume_gb"]} GB · {p["days"]} روز</p><strong>{p["price"]:,} تومان</strong><button onclick="location.href=\'/shop/buy/{p["id"]}\'">خرید</button></div>' for p in plans)
    return page('Shop',f'<section class="hero"><h1>فروشگاه VEXORA</h1><p>خرید سریع و مدیریت کانفیگ بدون نیاز به حساب کاربری</p></section><div class="grid">{cards or "<div class=card>هنوز پلنی فعال نشده است.</div>"}</div>')

@app.get(settings.shop_path+'buy/{plan_id}',response_class=HTMLResponse)
def buy_page(plan_id:int):
    p=one('SELECT * FROM plans WHERE id=? AND enabled=1',(plan_id,));
    if not p: raise HTTPException(404)
    return page('Purchase',f'''<div class="card"><h2>{p["name"]}</h2><p>{p["volume_gb"]} GB · {p["days"]} روز · {p["price"]:,} تومان</p><form method="post" action="/shop/buy/{plan_id}"><input name="username" required placeholder="نام کاربری کانفیگ"><button>ایجاد سفارش</button></form></div>''')

@app.post(settings.shop_path+'buy/{plan_id}')
def buy(plan_id:int,request:Request,username:str=Form(...)):
    p=one('SELECT * FROM plans WHERE id=? AND enabled=1',(plan_id,));
    if not p: raise HTTPException(404)
    c=exec('INSERT INTO customers(tenant_id,username,plan_id) VALUES(?,?,?)',(p['tenant_id'],username,p['id']))
    notify(f'🛒 خرید/سفارش VEXORA\nUser: {username}\nPlan: {p["name"]}\nAmount: {p["price"]:,}')
    return RedirectResponse(settings.shop_path+'receipt/'+str(c),303)

@app.get('/shop/receipt/{customer_id}',response_class=HTMLResponse)
def receipt_page(customer_id:int):
    c=one('SELECT c.*,p.name plan_name,p.price FROM customers c JOIN plans p ON p.id=c.plan_id WHERE c.id=?',(customer_id,));
    if not c: raise HTTPException(404)
    return page('Receipt',f'''<div class="card"><h2>ارسال رسید</h2><p>پلن: {c["plan_name"]} — مبلغ: {c["price"]:,}</p><form method="post" action="/shop/receipt/{customer_id}" enctype="multipart/form-data"><input name="amount" type="number" value="{c["price"]}" required><input name="file" type="file" accept="image/*,.pdf" required><button>ارسال رسید</button></form></div>''')

@app.post('/shop/receipt/{customer_id}')
async def receipt(customer_id:int,request:Request,amount:int=Form(...),file:UploadFile=File(...)):
    c=one('SELECT * FROM customers WHERE id=?',(customer_id,));
    if not c: raise HTTPException(404)
    data=await file.read();
    if len(data)>settings.max_upload_mb*1024*1024: raise HTTPException(413,'File too large')
    ext=Path(file.filename or '').suffix.lower();
    if ext not in {'.jpg','.jpeg','.png','.webp','.pdf'}: raise HTTPException(415,'Unsupported file')
    d=Path('/opt/vexora/data/receipts'); d.mkdir(parents=True,exist_ok=True); path=d/f'{secrets.token_hex(16)}{ext}'; path.write_bytes(data)
    rid=exec('INSERT INTO receipts(tenant_id,customer_id,amount,file_path) VALUES(?,?,?,?)',(c['tenant_id'],customer_id,amount,str(path)))
    notify(f'🧾 رسید جدید #{rid}\nUser: {c["username"]}\nAmount: {amount:,}\nبرای تایید: بخش رسیدهای مدیریت')
    return page('Receipt', '<div class="card"><h2>رسید ارسال شد</h2><p>پس از تایید، اعتبار/کانفیگ به‌صورت خودکار پردازش می‌شود.</p></div>')

@app.get(settings.admin_path,response_class=HTMLResponse)
def admin(request:Request):
    a=current(request)
    if not a: return page('Login',f'<div class="card"><h2>ورود مدیریت</h2><form method="post" action="{settings.admin_path}login"><input name="username" placeholder="نام کاربری"><input name="password" type="password" placeholder="رمز"><button>ورود</button></form></div>')
    stats=[('پلن‌ها',one('SELECT COUNT(*) n FROM plans WHERE tenant_id=?',(a['tenant_id'],))['n']),('رسیدهای منتظر',one('SELECT COUNT(*) n FROM receipts WHERE tenant_id=? AND status="pending"',(a['tenant_id'],))['n']),('کانفیگ‌ها',one('SELECT COUNT(*) n FROM customers WHERE tenant_id=?',(a['tenant_id'],))['n'])]
    cards=''.join(f'<div class="stat"><b>{v}</b><span>{k}</span></div>' for k,v in stats)
    links='<a href="/admin/panels">پنل‌ها</a> <a href="/admin/plans">پلن‌ها</a> <a href="/admin/receipts">رسیدها</a> <a href="/admin/admins">ادمین‌ها</a> <a href="/admin/backup">بکاپ</a>'
    return page('Dashboard',f'<h1>داشبورد</h1><div class="stats">{cards}</div><div class="card menu">{links}</div>')

@app.post(settings.admin_path+'login')
def login(request:Request,username:str=Form(...),password:str=Form(...)):
    a=one('SELECT * FROM admins WHERE username=? AND active=1',(username,)); ip=request.client.host if request.client else ''
    if not a or not verify_password(password,a['password_hash']):
        audit(a['id'] if a else None,'login_failed',ip,{'username':username}); notify(f'🔐 تلاش ناموفق ورود مدیریت\nUser: {username}\nIP: {ip}'); raise HTTPException(401,'Invalid credentials')
    audit(a['id'],'login_success',ip); notify(f'🔐 ورود مدیریت موفق\nUser: {username}\nIP: {ip}')
    r=RedirectResponse(settings.admin_path,303); r.set_cookie('vexora_session',make_session(settings.secret_key,a['id']),httponly=True,secure=False,samesite='strict',max_age=86400); return r

@app.post(settings.admin_path+'logout')
def logout():
    r=RedirectResponse(settings.admin_path,303); r.delete_cookie('vexora_session'); return r

@app.get(settings.admin_path+'panels',response_class=HTMLResponse)
def panels(request:Request):
    a=require(request,['owner','manager','operator']); rows=q('SELECT * FROM panels WHERE tenant_id=?',(a['tenant_id'],));
    form='''<form method="post"><input name="name" placeholder="نام"><select name="kind"><option>pasarguard</option><option>3x-ui</option><option>marzban</option></select><input name="base_url" placeholder="https://panel.example"><input name="username" placeholder="username"><input name="secret" type="password" placeholder="password"><button>افزودن</button></form>'''
    listing=''.join(f'<p>#{r["id"]} {r["name"]} — {r["kind"]} — {r["base_url"]}</p>' for r in rows)
    return page('Panels',f'<div class="card"><h2>اتصال پنل</h2>{form}{listing}</div>')

@app.post(settings.admin_path+'panels')
def add_panel(request:Request,name:str=Form(...),kind:str=Form(...),base_url:str=Form(...),username:str=Form(''),secret:str=Form('')):
    a=require(request,['owner','manager','operator']);
    if not re.match(r'^https?://[^\s]+$',base_url): raise HTTPException(400,'Invalid URL')
    pid=exec('INSERT INTO panels(tenant_id,name,kind,base_url,username,secret_enc) VALUES(?,?,?,?,?,?)',(a['tenant_id'],name,kind,base_url,username,encrypt(secret) if secret else None)); audit(a['id'],'panel_created',request.client.host if request.client else '',{'panel_id':pid}); return RedirectResponse(settings.admin_path+'panels',303)

@app.get(settings.admin_path+'plans',response_class=HTMLResponse)
def plans(request:Request):
    a=require(request,['owner','manager','operator']); ps=q('SELECT * FROM panels WHERE tenant_id=?',(a['tenant_id'],));
    opts=''.join(f'<option value="{p["id"]}">{p["name"]}</option>' for p in ps); rows=q('SELECT p.*,pa.name panel FROM plans p JOIN panels pa ON pa.id=p.panel_id WHERE p.tenant_id=?',(a['tenant_id'],)); listing=''.join(f'<p>{r["name"]} — {r["volume_gb"]}GB/{r["days"]}d — {r["price"]:,} — {r["panel"]}</p>' for r in rows)
    return page('Plans',f'<div class="card"><form method="post"><input name="name" placeholder="نام پلن"><select name="panel_id">{opts}</select><input name="price" type="number" placeholder="قیمت"><input name="volume_gb" type="number" step="0.1" placeholder="حجم GB"><input name="days" type="number" placeholder="روز"><button>ساخت پلن</button></form>{listing}</div>')

@app.post(settings.admin_path+'plans')
def add_plan(request:Request,name:str=Form(...),panel_id:int=Form(...),price:int=Form(...),volume_gb:float=Form(...),days:int=Form(...)):
    a=require(request,['owner','manager','operator']); p=one('SELECT * FROM panels WHERE id=? AND tenant_id=?',(panel_id,a['tenant_id']));
    if not p: raise HTTPException(403)
    exec('INSERT INTO plans(tenant_id,panel_id,name,price,volume_gb,days) VALUES(?,?,?,?,?,?)',(a['tenant_id'],panel_id,name,price,volume_gb,days)); return RedirectResponse(settings.admin_path+'plans',303)

@app.get(settings.admin_path+'receipts',response_class=HTMLResponse)
def receipts(request:Request):
    a=require(request,['owner','manager','receipt','operator']); rows=q('SELECT r.*,c.username,p.name plan FROM receipts r JOIN customers c ON c.id=r.customer_id LEFT JOIN plans p ON p.id=c.plan_id WHERE r.tenant_id=? ORDER BY r.id DESC',(a['tenant_id'],));
    body=''.join(f'<div class="card"><b>#{r["id"]}</b> {r["username"]} — {r["amount"]:,} — {r["status"]} <a href="/admin/receipts/{r["id"]}/file">فایل</a> <form class="inline" method="post" action="/admin/receipts/{r["id"]}/review"><button name="decision" value="approved">تایید</button><button name="decision" value="rejected">رد</button></form></div>' for r in rows)
    return page('Receipts',body or '<div class="card">رسیدی نیست.</div>')

@app.get('/admin/receipts/{rid}/file')
def receipt_file(rid:int,request:Request):
    a=require(request,['owner','manager','receipt']); r=one('SELECT * FROM receipts WHERE id=? AND tenant_id=?',(rid,a['tenant_id']));
    if not r: raise HTTPException(404)
    return FileResponse(r['file_path'])

@app.post('/admin/receipts/{rid}/review')
def review(rid:int,request:Request,decision:str=Form(...)):
    a=require(request,['owner','manager','receipt']); r=one('SELECT * FROM receipts WHERE id=? AND tenant_id=?',(rid,a['tenant_id']));
    if not r: raise HTTPException(404)
    if decision not in ('approved','rejected'): raise HTTPException(400)
    exec('UPDATE receipts SET status=?,reviewed_by=?,reviewed_at=CURRENT_TIMESTAMP WHERE id=?',(decision,a['id'],rid)); notify(f'🧾 رسید #{rid} {"تایید شد" if decision=="approved" else "رد شد"} توسط {a["username"]}')
    return RedirectResponse(settings.admin_path+'receipts',303)

@app.get(settings.admin_path+'admins',response_class=HTMLResponse)
def admins(request:Request):
    a=require(request,['owner']); rows=q('SELECT id,username,role,active FROM admins WHERE tenant_id=?',(a['tenant_id'],)); listing=''.join(f'<p>#{r["id"]} {r["username"]} — {r["role"]}</p>' for r in rows)
    return page('Admins',f'''<div class="card"><form method="post"><input name="username" required><input name="password" type="password" required><select name="role"><option value="manager">مدیر</option><option value="operator">اپراتور</option><option value="receipt">تایید رسید</option></select><button>افزودن</button></form>{listing}</div>''')

@app.post(settings.admin_path+'admins')
def add_admin(request:Request,username:str=Form(...),password:str=Form(...),role:str=Form(...)):
    a=require(request,['owner']);
    if role not in ('manager','operator','receipt'): raise HTTPException(400)
    exec('INSERT INTO admins(username,password_hash,role,tenant_id) VALUES(?,?,?,?)',(username,hash_password(password),role,a['tenant_id'])); return RedirectResponse(settings.admin_path+'admins',303)

@app.get(settings.admin_path+'backup')
def backup(request:Request):
    a=require(request,['owner']); path=make_backup();
    if settings.owner_tg_id: send_owner_document(path,'VEXORA owner backup')
    audit(a['id'],'backup_created',request.client.host if request.client else '')
    return FileResponse(path,filename=Path(path).name)


@app.get(settings.admin_path+'certificates', response_class=HTMLResponse)
def certificates(request:Request):
    require(request,['owner','manager'])
    host=settings.public_host or 'SERVER-IP'
    return page('SSL / TLS', f'<div class="card"><h2>SSL / TLS</h2><p>Public URL: {settings.public_scheme}://{host}{settings.base_path}</p><p>HTTPS: 443</p><p>Fallback: 8080</p><p>Certificate files are managed by the ACME/Nginx installer.</p></div>')

@app.get('/admin/qr/{customer_id}')
def qr(customer_id:int,request:Request):
    require(request,['owner','manager','operator']); c=one('SELECT * FROM customers WHERE id=?',(customer_id,));
    if not c: raise HTTPException(404)
    data=c['subscription_url'] or c['config_text'] or ''
    if not data: raise HTTPException(404)
    img=qrcode.make(data); path=f'/opt/vexora/data/qr-{customer_id}.png'; img.save(path); return FileResponse(path,media_type='image/png')
