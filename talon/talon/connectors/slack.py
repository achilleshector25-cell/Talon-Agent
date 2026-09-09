from .base import BaseConnector
class SlackConnector(BaseConnector):
    channel="slack"
    async def listen(self):
        while True: await __import__("asyncio").sleep(3600)
    async def send(self, user_id, text): print(f"[slack->{user_id}] {text}")
