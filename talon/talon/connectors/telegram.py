from .base import BaseConnector, InboundMessage
import asyncio, uuid

class TelegramConnector(BaseConnector):
    channel = "telegram"

    async def listen(self):
        # In prod: long-poll/webhook via isolated network
        while True:
            await asyncio.sleep(3600)

    async def send(self, user_id: str, text: str):
        print(f"[telegram->{user_id}] {text[:200]}")

    def to_inbound(self, update: dict) -> InboundMessage:
        return InboundMessage(
            id=str(uuid.uuid4()),
            channel="telegram",
            user_id=str(update.get("from", {}).get("id")),
            text=self.sanitize(update.get("text","")),
            raw=update,
            taint_source="telegram:untrusted_user"
        )
