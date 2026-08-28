import httpx, asyncio
from .config import settings

def _send(text, document=None, topic=None):
    if not settings.tg_token or not settings.tg_chat: return False
    url=f"https://api.telegram.org/bot{settings.tg_token}/sendMessage"
    data={"chat_id":settings.tg_chat,"text":text,"disable_web_page_preview":True}
    tid=topic or settings.tg_topic
    if tid: data["message_thread_id"]=tid
    try:
        r=httpx.post(url,data=data,timeout=15); r.raise_for_status(); return True
    except Exception: return False

def notify(text): return _send(text)

def send_owner_document(path, caption=""):
    if not settings.tg_token or not settings.tg_chat: return False
    try:
        with open(path,"rb") as f:
            r=httpx.post(f"https://api.telegram.org/bot{settings.tg_token}/sendDocument",data={"chat_id":settings.owner_tg_id or settings.tg_chat,"caption":caption},files={"document":f},timeout=60)
            r.raise_for_status(); return True
    except Exception: return False
