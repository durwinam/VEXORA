from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from ..config import settings
from ..db import one
from ..security import verify_password, make_token, login_allowed, clear_login_attempts
router = APIRouter()

def path(child: str) -> str: return settings.path(f'admin/{child}')

@router.post(path('login'))
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    ip=request.client.host if request.client else 'unknown'
    if not login_allowed(ip, settings.rate_limit_per_minute):
        return RedirectResponse(settings.admin_path + '?error=rate', 303)
    admin = one('SELECT * FROM admins WHERE username=? AND active=1', (username.strip(),))
    if not admin or not verify_password(password, admin['password_hash']):
        return RedirectResponse(settings.admin_path + '?error=login', 303)
    clear_login_attempts(ip)
    response = RedirectResponse(settings.admin_path, 303)
    response.set_cookie('vexora_session', make_token(settings.secret_key, admin['id'], settings.session_hours), httponly=True, secure=settings.cookie_secure, samesite='lax', max_age=settings.session_hours*3600, path='/')
    return response

@router.post(path('logout'))
def logout():
    response = RedirectResponse(settings.admin_path, 303)
    response.delete_cookie('vexora_session', path='/')
    return response
