from .base import BaseConnector
class DiscordConnector(BaseConnector):
    channel="discord"
    async def listen(self):
        while True: await __import__("asyncio").sleep(3600)
    async def send(self, user_id, text): print(f"[discord->{user_id}] {text}")
