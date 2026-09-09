from .base import BaseConnector
class WhatsAppConnector(BaseConnector):
    channel="whatsapp"
    async def listen(self): 
        while True: await __import__("asyncio").sleep(3600)
    async def send(self, user_id, text): print(f"[wa->{user_id}] {text}")
