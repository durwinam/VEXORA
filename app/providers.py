import httpx, json, urllib.parse

class ProviderError(Exception): pass
class BaseProvider:
    def __init__(self, base_url, username=None, secret=None, verify_tls=True):
        self.base=base_url.rstrip('/'); self.username=username; self.secret=secret; self.verify=bool(verify_tls); self.client=httpx.Client(timeout=20,verify=self.verify,follow_redirects=True)
    def close(self): self.client.close()
    def health(self):
        r=self.client.get(self.base); return r.status_code < 500

class MarzbanProvider(BaseProvider):
    def token(self):
        r=self.client.post(self.base+'/api/admin/token',data={'username':self.username,'password':self.secret});
        if r.status_code>=400: raise ProviderError(f"Marzban token HTTP {r.status_code}")
        return r.json()['access_token']
    def _h(self): return {'Authorization':'Bearer '+self.token()}
    def create_user(self, username, days, gb):
        r=self.client.post(self.base+'/api/user',headers=self._h(),json={'username':username,'expire':days,'data_limit':int(gb*1024**3)}); 
        if r.status_code>=400: raise ProviderError(f"Marzban create user HTTP {r.status_code}: {r.text[:300]}")
        d=r.json(); return {'id':d.get('username',username),'subscription_url':d.get('subscription_url'),'config':d.get('links') or d.get('links',[])}

class PasarGuardProvider(BaseProvider):
    def token(self):
        r=self.client.post(self.base+'/api/admin/token',data={'username':self.username,'password':self.secret});
        if r.status_code>=400: raise ProviderError(f"PasarGuard token HTTP {r.status_code}")
        return r.json()['access_token']
    def _h(self): return {'Authorization':'Bearer '+self.token()}
    def create_user(self, username, days, gb):
        # PasarGuard versions can differ in payload details; expose a conservative API adapter.
        payload={'username':username,'data_limit':int(gb*1024**3),'expire':days}
        r=self.client.post(self.base+'/api/user',headers=self._h(),json=payload)
        if r.status_code>=400: raise ProviderError(f"PasarGuard create user HTTP {r.status_code}: {r.text[:300]}")
        d=r.json(); return {'id':str(d.get('username',username)),'subscription_url':d.get('subscription_url'),'config':d.get('links',[])}

class XUIProvider(BaseProvider):
    def login(self):
        r=self.client.post(self.base+'/login',data={'username':self.username,'password':self.secret})
        if r.status_code>=400: raise ProviderError(f"3X-UI login HTTP {r.status_code}")
        return r
    def health(self):
        try: self.login(); return True
        except: return False
    def create_user(self, username, days, gb):
        raise ProviderError('3X-UI requires an inbound selection and client UUID/flow settings; configure the inbound mapping before creating users.')

def provider(kind, *args, **kw):
    k=kind.lower()
    if k in ('marzban','marzban_api'): return MarzbanProvider(*args,**kw)
    if k in ('pasarguard','pg'): return PasarGuardProvider(*args,**kw)
    if k in ('3x-ui','3xui','sanaei','xui'): return XUIProvider(*args,**kw)
    raise ProviderError('Unsupported provider')
