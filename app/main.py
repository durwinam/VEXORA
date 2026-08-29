from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import APP_VERSION
from app.database import initialize
from app.routes import admin, shop


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="VEXORA",
    version=APP_VERSION,
    docs_url=None,
    redoc_url=None,
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


@app.on_event("startup")
def startup() -> None:
    initialize()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": APP_VERSION,
    }


@app.get("/")
def root():
    return RedirectResponse(
        "/shop/",
        status_code=307,
    )


app.include_router(shop.router)
app.include_router(admin.router)
