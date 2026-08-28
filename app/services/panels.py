from urllib.parse import urljoin
import httpx
from ..crypto import decrypt
from ..config import settings

class PanelClient:
    def __init__(self, panel: dict):
        self.panel = panel
        self.base = panel['base_url'].rstrip('/') + '/'
        self.verify = bool(panel['verify_tls'])

    def health(self) -> dict:
        try:
            r = httpx.get(urljoin(self.base, 'health'), timeout=8, verify=self.verify)
            return {'ok': r.is_success, 'status_code': r.status_code, 'text': r.text[:500]}
        except httpx.HTTPError as exc:
            return {'ok': False, 'error': str(exc)}
