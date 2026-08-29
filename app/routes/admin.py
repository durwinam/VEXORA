import secrets

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.auth import COOKIE_NAME, create_session, get_session
from app.config import settings
from app.database import connect
from app.security import verify_password


router = APIRouter(prefix="/admin")


def current_user(request: Request):
    return get_session(request)


def render(request, template, **context):
    from app.main import templates

    return templates.TemplateResponse(
        template,
        {
            "request": request,
            "username": current_user(request),
            "version": settings.version,
            **context,
        },
    )


def redirect_login(request):
    if not current_user(request):
        return RedirectResponse(
            "/admin/login",
            status_code=303,
        )
    return None


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if current_user(request):
        return RedirectResponse("/admin/", status_code=303)

    return render(
        request,
        "admin/login.html",
        error=None,
    )


@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    valid = False

    if username == settings.admin_username:
        valid = verify_password(
            password,
            settings.admin_password_hash,
        )

    if not valid:
        return render(
            request,
            "admin/login.html",
            error="نام کاربری یا رمز عبور اشتباه است.",
        )

    response = RedirectResponse(
        "/admin/",
        status_code=303,
    )

    response.set_cookie(
        COOKIE_NAME,
        create_session(username),
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 48,
    )

    with connect() as db:
        db.execute(
            "UPDATE admins SET last_login = CURRENT_TIMESTAMP WHERE username = ?",
            (username,),
        )
        db.execute(
            """
            INSERT INTO audit_logs(actor, action, target, ip)
            VALUES (?, 'login', 'admin', ?)
            """,
            (
                username,
                request.client.host if request.client else "",
            ),
        )

    return response


@router.post("/logout")
def logout():
    response = RedirectResponse(
        "/admin/login",
        status_code=303,
    )
    response.delete_cookie(COOKIE_NAME)
    return response


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    if redirect_login(request):
        return redirect_login(request)

    with connect() as db:
        products = db.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]
        users = db.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]
        orders = db.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]
        revenue = db.execute(
            "SELECT COALESCE(SUM(amount),0) FROM orders WHERE status='paid'"
        ).fetchone()[0]
        servers = db.execute(
            "SELECT COUNT(*) FROM servers WHERE status='online' AND active=1"
        ).fetchone()[0]
        tickets = db.execute(
            "SELECT COUNT(*) FROM tickets WHERE status != 'closed'"
        ).fetchone()[0]
        recent = db.execute(
            """
            SELECT orders.*, products.name AS product_name
            FROM orders
            LEFT JOIN products ON products.id = orders.product_id
            ORDER BY orders.id DESC
            LIMIT 8
            """
        ).fetchall()

    return render(
        request,
        "admin/dashboard.html",
        products=products,
        users=users,
        orders=orders,
        revenue=revenue,
        servers=servers,
        tickets=tickets,
        recent=recent,
    )


@router.get("/orders/", response_class=HTMLResponse)
def orders(request: Request):
    if redirect_login(request):
        return redirect_login(request)

    with connect() as db:
        rows = db.execute(
            """
            SELECT orders.*, products.name AS product_name
            FROM orders
            LEFT JOIN products ON products.id = orders.product_id
            ORDER BY orders.id DESC
            """
        ).fetchall()

    return render(request, "admin/orders.html", rows=rows)


@router.post("/orders/{order_id}/status")
def update_order_status(
    request: Request,
    order_id: int,
    status: str = Form(...),
):
    if redirect_login(request):
        return redirect_login(request)

    if status not in {
        "pending",
        "paid",
        "cancelled",
        "refunded",
    }:
        status = "pending"

    with connect() as db:
        db.execute(
            "UPDATE orders SET status=? WHERE id=?",
            (status, order_id),
        )

    return RedirectResponse(
        "/admin/orders/",
        status_code=303,
    )


@router.get("/users/", response_class=HTMLResponse)
def users(request: Request):
    if redirect_login(request):
        return redirect_login(request)

    with connect() as db:
        rows = db.execute(
            "SELECT * FROM users ORDER BY id DESC"
        ).fetchall()

    return render(request, "admin/users.html", rows=rows)


@router.get("/plans/", response_class=HTMLResponse)
def plans(request: Request):
    if redirect_login(request):
        return redirect_login(request)

    with connect() as db:
        rows = db.execute(
            "SELECT * FROM products ORDER BY sort_order, id"
        ).fetchall()

    return render(request, "admin/plans.html", rows=rows)


@router.post("/plans/create")
def create_plan(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    price: int = Form(0),
    volume_gb: str = Form(""),
    duration_days: int = Form(30),
    devices: int = Form(1),
    badge: str = Form(""),
):
    if redirect_login(request):
        return redirect_login(request)

    volume = int(volume_gb) if volume_gb.strip() else None

    with connect() as db:
        db.execute(
            """
            INSERT INTO products
            (name, description, price, volume_gb, duration_days, devices, badge)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name.strip(),
                description.strip(),
                max(0, price),
                volume,
                max(1, duration_days),
                max(1, devices),
                badge.strip(),
            ),
        )

    return RedirectResponse(
        "/admin/plans/",
        status_code=303,
    )


@router.post("/plans/{plan_id}/toggle")
def toggle_plan(
    request: Request,
    plan_id: int,
):
    if redirect_login(request):
        return redirect_login(request)

    with connect() as db:
        db.execute(
            """
            UPDATE products
            SET active = CASE active WHEN 1 THEN 0 ELSE 1 END
            WHERE id=?
            """,
            (plan_id,),
        )

    return RedirectResponse(
        "/admin/plans/",
        status_code=303,
    )


@router.get("/servers/", response_class=HTMLResponse)
def servers(request: Request):
    if redirect_login(request):
        return redirect_login(request)

    with connect() as db:
        rows = db.execute(
            "SELECT * FROM servers ORDER BY id DESC"
        ).fetchall()

    return render(request, "admin/servers.html", rows=rows)


@router.post("/servers/create")
def create_server(
    request: Request,
    name: str = Form(...),
    country: str = Form(""),
    host: str = Form(""),
    port: int = Form(443),
):
    if redirect_login(request):
        return redirect_login(request)

    with connect() as db:
        db.execute(
            """
            INSERT INTO servers(name,country,host,port)
            VALUES (?,?,?,?)
            """,
            (
                name.strip(),
                country.strip(),
                host.strip(),
                min(65535, max(1, port)),
            ),
        )

    return RedirectResponse(
        "/admin/servers/",
        status_code=303,
    )


@router.get("/support/", response_class=HTMLResponse)
def support(request: Request):
    if redirect_login(request):
        return redirect_login(request)

    with connect() as db:
        rows = db.execute(
            "SELECT * FROM tickets ORDER BY id DESC"
        ).fetchall()

    return render(request, "admin/support.html", rows=rows)


@router.post("/support/{ticket_id}/status")
def update_ticket(
    request: Request,
    ticket_id: int,
    status: str = Form(...),
):
    if redirect_login(request):
        return redirect_login(request)

    if status not in {"open", "pending", "closed"}:
        status = "open"

    with connect() as db:
        db.execute(
            "UPDATE tickets SET status=? WHERE id=?",
            (status, ticket_id),
        )

    return RedirectResponse(
        "/admin/support/",
        status_code=303,
    )


@router.get("/reports/", response_class=HTMLResponse)
def reports(request: Request):
    if redirect_login(request):
        return redirect_login(request)

    with connect() as db:
        rows = db.execute(
            """
            SELECT substr(created_at,1,10) AS day,
                   COALESCE(SUM(amount),0) AS amount
            FROM orders
            WHERE status='paid'
            GROUP BY substr(created_at,1,10)
            ORDER BY day DESC
            LIMIT 30
            """
        ).fetchall()

    return render(request, "admin/reports.html", rows=rows)


@router.get("/settings/", response_class=HTMLResponse)
def settings_page(request: Request):
    if redirect_login(request):
        return redirect_login(request)

    with connect() as db:
        values = {
            row["key"]: row["value"]
            for row in db.execute(
                "SELECT key,value FROM settings"
            ).fetchall()
        }

    return render(
        request,
        "admin/settings.html",
        values=values,
    )


@router.post("/settings/")
def save_settings(
    request: Request,
    site_name: str = Form("VEXORA"),
    site_description: str = Form(""),
    support_enabled: str = Form("0"),
    maintenance: str = Form("0"),
):
    if redirect_login(request):
        return redirect_login(request)

    values = {
        "site_name": site_name.strip(),
        "site_description": site_description.strip(),
        "support_enabled": "1" if support_enabled == "1" else "0",
        "maintenance": "1" if maintenance == "1" else "0",
    }

    with connect() as db:
        for key, value in values.items():
            db.execute(
                """
                INSERT INTO settings(key,value)
                VALUES (?,?)
                ON CONFLICT(key)
                DO UPDATE SET value=excluded.value
                """,
                (key, value),
            )

    return RedirectResponse(
        "/admin/settings/?saved=1",
        status_code=303,
    )


@router.get("/admins/", response_class=HTMLResponse)
def admins(request: Request):
    if redirect_login(request):
        return redirect_login(request)

    with connect() as db:
        rows = db.execute(
            "SELECT id,username,role,active,last_login,created_at FROM admins ORDER BY id"
        ).fetchall()

    return render(request, "admin/admins.html", rows=rows)


@router.get("/audit/", response_class=HTMLResponse)
def audit(request: Request):
    if redirect_login(request):
        return redirect_login(request)

    with connect() as db:
        rows = db.execute(
            "SELECT * FROM audit_logs ORDER BY id DESC LIMIT 250"
        ).fetchall()

    return render(request, "admin/audit.html", rows=rows)
