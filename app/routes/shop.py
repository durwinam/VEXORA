from pathlib import Path
import secrets
from fastapi import APIRouter, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from ..config import settings
from ..db import all_rows, one, execute, audit
from ..services.telegram import notify
router = APIRouter()

def p(child=''): return settings.path(f'shop/{child}') if child else settings.shop_path

def render(request, template, **ctx):
    return request.app.state.templates.TemplateResponse(request=request, name=template, context={'settings':settings, 'request':request, **ctx})

@router.get(settings.shop_path, response_class=HTMLResponse)
def shop(request: Request):
    plans = all_rows('SELECT p.*, pan.name panel_name FROM plans p JOIN panels pan ON pan.id=p.panel_id WHERE p.enabled=1 AND pan.enabled=1 ORDER BY p.price')
    return render(request, 'shop.html', plans=plans)

@router.get(p('buy/{plan_id}'), response_class=HTMLResponse)
def buy_page(plan_id: int, request: Request):
    plan = one('SELECT p.*, pan.name panel_name FROM plans p JOIN panels pan ON pan.id=p.panel_id WHERE p.id=? AND p.enabled=1', (plan_id,))
    if not plan: raise HTTPException(404, 'Plan not found')
    return render(request, 'purchase.html', plan=plan)

@router.post(p('buy/{plan_id}'))
def buy(plan_id: int, request: Request, customer_name: str = Form(...), customer_contact: str = Form('')):
    plan = one('SELECT * FROM plans WHERE id=? AND enabled=1', (plan_id,))
    if not plan: raise HTTPException(404, 'Plan not found')
    order_id = execute('INSERT INTO orders(plan_id,customer_name,customer_contact) VALUES(?,?,?)', (plan_id, customer_name.strip(), customer_contact.strip()))
    audit('order.created', detail=f'order={order_id}', ip=request.client.host if request.client else '')
    notify(f'🛒 سفارش جدید #{order_id}\n{customer_name.strip()}\n{plan["name"]}')
    return RedirectResponse(p(f'receipt/{order_id}'), 303)


@router.post(p('receipt/{order_id}'))
async def receipt_upload(order_id: int, request: Request, amount: int = Form(...), receipt: UploadFile = File(...)):
    order = one('SELECT * FROM orders WHERE id=?', (order_id,))
    if not order:
        raise HTTPException(404, 'Order not found')
    data = await receipt.read()
    limit = settings.max_upload_mb * 1024 * 1024
    if len(data) > limit:
        raise HTTPException(413, 'Receipt file is too large')
    ext = Path(receipt.filename or '').suffix.lower()
    if ext not in {'.jpg', '.jpeg', '.png', '.webp', '.pdf'}:
        raise HTTPException(415, 'Unsupported receipt type')
    folder = settings.data_dir / 'receipts'
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f'{secrets.token_hex(16)}{ext}'
    target.write_bytes(data)
    execute('INSERT INTO receipts(order_id,amount,file_path) VALUES(?,?,?)', (order_id, max(0, amount), str(target)))
    audit('receipt.created', detail=f'order={order_id}', ip=request.client.host if request.client else '')
    notify(f'🧾 رسید جدید سفارش #{order_id}\nمبلغ: {amount:,}')
    return render(request, 'success.html', title='رسید ثبت شد', message='رسید شما با موفقیت ثبت شد.')

@router.get(p('receipt/{order_id}'), response_class=HTMLResponse)
def receipt_page(order_id: int, request: Request):
    order = one('SELECT o.*, p.name plan_name, p.price FROM orders o JOIN plans p ON p.id=o.plan_id WHERE o.id=?', (order_id,))
    if not order: raise HTTPException(404, 'Order not found')
    return render(request, 'receipt.html', order=order)
