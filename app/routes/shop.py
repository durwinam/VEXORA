from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.database import connect


router = APIRouter()


@router.get(
    "/shop/",
    response_class=HTMLResponse,
)
def shop_page(request: Request):
    with connect() as db:
        products = db.execute(
            '''
            SELECT id, name, description, price
            FROM products
            WHERE active = 1
            ORDER BY id DESC
            '''
        ).fetchall()

    from app.main import templates

    return templates.TemplateResponse(
        "shop/index.html",
        {
            "request": request,
            "products": products,
        },
    )


@router.get("/shop/status/")
def status():
    with connect() as db:
        plans = db.execute(
            "SELECT COUNT(*) FROM products WHERE active = 1"
        ).fetchone()[0]
        servers = db.execute(
            "SELECT COUNT(*) FROM servers WHERE active = 1 AND status = 'online'"
        ).fetchone()[0]

    return {
        "status": "online",
        "active_plans": plans,
        "online_servers": servers,
    }


@router.post("/shop/order/")
def create_order(
    product_id: int = Form(...),
    customer_name: str = Form(""),
):
    with connect() as db:
        product = db.execute(
            "SELECT id, price FROM products WHERE id = ? AND active = 1",
            (product_id,),
        ).fetchone()

        if not product:
            return RedirectResponse(
                "/shop/plans/?error=plan",
                status_code=303,
            )

        code = "VX-" + secrets.token_hex(5).upper()
        db.execute(
            """
            INSERT INTO orders
            (order_code, product_id, customer_name, amount)
            VALUES (?, ?, ?, ?)
            """,
            (
                code,
                product["id"],
                customer_name.strip(),
                product["price"],
            ),
        )

    return RedirectResponse(
        "/shop/?order=" + code,
        status_code=303,
    )
