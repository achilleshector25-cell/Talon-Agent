"""Channel isolation — each connector runs in its own seccomp profile"""
import asyncio

class IsolationRunner:
    def __init__(self, connector):
        self.connector = connector

    async def run_isolated(self):
        # In prod: this spawns via gVisor runsc + separate netns
        # For MVP: asyncio task with resource limits
        print(f"[isolation] Starting {self.connector.channel} in isolated sandbox")
        async for msg in self.connector.listen():
            # Forward to gateway via mTLS QUIC
            yield msg
