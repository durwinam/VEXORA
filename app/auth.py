from itsdangerous import URLSafeTimedSerializer
from fastapi import Request

from app.config import settings


COOKIE_NAME = "vexora_admin_session"


def serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.secret_key)


def create_session(username: str) -> str:
    return serializer().dumps({"username": username})


def get_session(request: Request) -> str | None:
    value = request.cookies.get(COOKIE_NAME)

    if not value:
        return None

    try:
        data = serializer().loads(
            value,
            max_age=60 * 60 * 24,
        )
        return data.get("username")

    except Exception:
        return None
