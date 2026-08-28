import httpx
from ..config import settings

def notify(text: str) -> bool:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return False
    url = f'https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage'
    try:
        r = httpx.post(url, json={'chat_id': settings.telegram_chat_id, 'text': text}, timeout=10)
        return r.is_success
    except httpx.HTTPError:
        return False
