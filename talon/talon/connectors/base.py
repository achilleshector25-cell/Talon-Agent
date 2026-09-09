from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator

@dataclass
class InboundMessage:
    id: str
    channel: str
    user_id: str
    text: str
    raw: dict
    taint_source: str  # for taint graph

class BaseConnector(ABC):
    channel: str

    @abstractmethod
    async def listen(self) -> AsyncGenerator[InboundMessage, None]: ...

    @abstractmethod
    async def send(self, user_id: str, text: str): ...

    def sanitize(self, text: str) -> str:
        # Strip prompt injection attempts, limit length
        if len(text) > 10000:
            text = text[:10000]
        # Remove zero-width, control chars
        return "".join(c for c in text if c.isprintable() or c in "\n\t")
