import httpx, urllib.parse
from datetime import datetime, timezone
class ProviderError(RuntimeError): pass
class Provider:
    async def request(self,*a,**kw):
        async with httpx.AsyncClient(timeout=15,follow_redirects=True,verify=True) as c:
            r=await c.request(*a,**kw); r.raise_for_status(); return r
class XUI(Provider):
    def __init__(self,url,token): self.url=url.rstrip('/'); self.token=token
    def h(self): return {'Authorization':f'Bearer {self.token}','Accept':'application/json'}
    async def health(self): return (await self.request('GET',self.url+'/panel/api/server/status',headers=self.h())).json()
    async def inbounds(self): return (await self.request('GET',self.url+'/panel/api/inbounds/list',headers=self.h())).json()
    async def traffic(self,email): return (await self.request('GET',self.url+'/panel/api/clients/traffic/'+urllib.parse.quote(email,safe=''),headers=self.h())).json()
    async def create_user(self,email,total_gb,expiry_ms,inbound_ids,comment=''):
        body={'inboundIds':inbound_ids,'client':{'email':email,'totalGB':total_gb,'expiryTime':expiry_ms,'tgId':0,'comment':comment,'enable':True}}
        return (await self.request('POST',self.url+'/panel/api/clients/add',headers={**self.h(),'Content-Type':'application/json'},json=body)).json()
    async def delete_user(self,email): return (await self.request('POST',self.url+'/panel/api/clients/del/'+urllib.parse.quote(email,safe=''),headers=self.h())).json()
class Marzban(Provider):
    def __init__(self,url,user,password): self.url=url.rstrip('/'); self.user=user; self.password=password; self.token=None
    async def login(self):
        r=await self.request('POST',self.url+'/api/admin/token',data={'username':self.user,'password':self.password},headers={'Accept':'application/json'}); self.token=r.json()['access_token']; return True
    def h(self): return {'Authorization':'Bearer '+self.token,'Accept':'application/json'}
    async def health(self):
        if not self.token: await self.login()
        return (await self.request('GET',self.url+'/api/system',headers=self.h())).json()
    async def get_user(self,username):
        if not self.token: await self.login()
        return (await self.request('GET',self.url+'/api/user/'+urllib.parse.quote(username,safe=''),headers=self.h())).json()
    async def create_user(self,payload):
        if not self.token: await self.login()
        return (await self.request('POST',self.url+'/api/user',headers={**self.h(),'Content-Type':'application/json'},json=payload)).json()
class PasarGuard(Provider):
    """PasarGuard connector uses its documented API key/token supplied by the installation."""
    def __init__(self,url,token): self.url=url.rstrip('/'); self.token=token
    def h(self): return {'Authorization':'Bearer '+self.token,'Accept':'application/json'}
    async def health(self):
        # /api/system is the common health endpoint in current PasarGuard builds.
        return (await self.request('GET',self.url+'/api/system',headers=self.h())).json()
