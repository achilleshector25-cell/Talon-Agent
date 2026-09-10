
"""Live Telegram wiring — secure, owner-only, taint-aware."""
import asyncio
import json
import os
import uuid
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from typing import AsyncGenerator
from .base import BaseConnector, InboundMessage
from .telegram_commands import parse_tool_request

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"

class TelegramLiveConnector(BaseConnector):
    channel = "telegram"

    def __init__(self, token: str, owner_ids: set[int], gateway_url: str = "http://localhost:8443/v1/task"):
        self.token = token
        self.owner_ids = owner_ids
        self.gateway_url = gateway_url
        self.offset = 0

    async def _api(self, method: str, params: dict | None = None) -> dict:
        """Call the Telegram Bot API without exposing the token to callers."""
        params = params or {}

        def request() -> dict:
            url = TELEGRAM_API.format(token=self.token, method=method)
            body = None
            headers = {}
            if method == "getUpdates":
                query = dict(params)
                if isinstance(query.get("allowed_updates"), list):
                    query["allowed_updates"] = json.dumps(query["allowed_updates"])
                url = f"{url}?{urlencode(query)}"
            else:
                body = json.dumps(params).encode()
                headers["Content-Type"] = "application/json"
            try:
                with urlopen(Request(url, data=body, headers=headers), timeout=30) as response:
                    return json.loads(response.read())
            except HTTPError as error:
                try:
                    return json.loads(error.read())
                except Exception:
                    return {"ok": False, "description": f"Telegram HTTP {error.code}"}

        return await asyncio.to_thread(request)

    async def listen(self) -> AsyncGenerator[InboundMessage, None]:
        print(f"[talon/telegram] Polling started, owner_ids={self.owner_ids}")
        while True:
            try:
                data = await self._api(
                    "getUpdates",
                    {"offset": self.offset, "timeout": 25, "allowed_updates": ["message"]},
                )
                if not data.get("ok"):
                    await asyncio.sleep(2)
                    continue
                for upd in data.get("result", []):
                    self.offset = upd["update_id"] + 1
                    msg = upd.get("message")
                    if not msg or "text" not in msg:
                        continue
                    user_id = msg["from"]["id"]
                    chat_id = msg["chat"]["id"]
                    text = msg["text"]
                    # Sanitize + taint
                    sanitized = self.sanitize(text)
                    inbound = InboundMessage(
                        id=str(uuid.uuid4()),
                        channel="telegram",
                        user_id=str(user_id),
                        text=sanitized,
                        raw={"chat_id": chat_id, "from_id": user_id, "text": text, "update_id": upd["update_id"]},
                        taint_source=f"telegram:user:{user_id}" if user_id not in self.owner_ids else f"telegram:owner:{user_id}",
                    )
                    # Attach ownership for gateway
                    inbound.raw["is_owner"] = user_id in self.owner_ids
                    inbound.raw["chat_id"] = chat_id
                    yield inbound
            except Exception as e:
                print(f"[telegram] poll error: {e}")
                await asyncio.sleep(3)

    async def send(self, user_id: str, text: str):
        # user_id here is chat_id
        try:
            await self._api(
                "sendMessage",
                {"chat_id": int(user_id), "text": text[:4000], "parse_mode": "Markdown"},
            )
        except Exception as e:
            print(f"[telegram] send error: {e}")

    async def forward_to_gateway(self, inbound: InboundMessage):
        """Forward to TALON gateway with server-derived owner flag (never client)"""
        is_owner = inbound.raw.get("is_owner", False)
        requested_tool, requested_args = parse_tool_request(inbound.text)
        # In prod: this goes via mTLS QUIC, identity derived from cert. For Telegram, we derive server-side from owner_ids allowlist
        payload = {
            "message": inbound.text,
            "channel": "telegram",
            "tool": requested_tool,
            "args": requested_args,
            "_internal_identity": {
                "spiffe_id": f"spiffe://talon/{'owner' if is_owner else 'guest'}/telegram:{inbound.user_id}",
                "is_owner": is_owner,  # SERVER-DERIVED from allowlist, not client payload
                "fingerprint": f"telegram:{inbound.user_id}",
            },
        }
        # Simulate gateway call (in prod: mTLS)
        try:
            # Direct orchestrator call for MVP (no HTTP hop)
            from ..gateway.mtls import Identity
            from ..gateway.policy_engine import PolicyEngine
            from ..runtime.orchestrator import Orchestrator
            from ..memory.vault import MemoryVault

            ident = Identity(
                spiffe_id=payload["_internal_identity"]["spiffe_id"],
                role="owner" if is_owner else "guest",
                channel="telegram",
                fingerprint=payload["_internal_identity"]["fingerprint"],
            )
            # Lazy singletons
            if not hasattr(self, "_orch"):
                self._orch = Orchestrator(memory=MemoryVault(), policy_engine=PolicyEngine())

            result = await self._orch.run(
                message=inbound.text,
                identity=ident,
                channel="telegram",
                client_ip=f"telegram:{inbound.user_id}",
                requested_tool=payload["tool"],
                requested_args=payload["args"],
            )
            # Format response
            if "error" in result:
                resp_text = f"⚠️ {result['error']}\n{result.get('hits','')}"
            else:
                # Summarize results
                out_lines = []
                for r in result.get("results", []):
                    if "content" in r:
                        out_lines.append(r["content"][:800])
                    elif "results" in r:
                        out_lines.append(str(r["results"])[:800])
                    else:
                        out_lines.append(str(r)[:800])
                resp_text = "\n".join(out_lines) or "✅ Done"
                resp_text = f"*TALON*\n{resp_text}"

            await self.send(inbound.raw["chat_id"], resp_text)
            return result
        except Exception as e:
            await self.send(inbound.raw["chat_id"], f"❌ Gateway error: {e}")
            raise

async def run_telegram_bot():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    owner_raw = os.getenv("TELEGRAM_OWNER_IDS", "")
    if not token:
        print("ERROR: Set TELEGRAM_BOT_TOKEN env var. Get from @BotFather.")
        return
    owner_values = [x.strip() for x in owner_raw.split(",") if x.strip()]
    owner_ids = {int(x) for x in owner_values if x.isdigit()}
    invalid_owner_values = [x for x in owner_values if not x.isdigit()]
    if invalid_owner_values:
        print("WARNING: Ignoring non-numeric TELEGRAM_OWNER_IDS entries; use Telegram numeric user IDs.")
    if not owner_ids:
        print("WARNING: No TELEGRAM_OWNER_IDS set — all users will be guest (can only web_search). Set your Telegram user ID.")
    connector = TelegramLiveConnector(token=token, owner_ids=owner_ids)
    async for inbound in connector.listen():
        # Process each message concurrently
        asyncio.create_task(connector.forward_to_gateway(inbound))

if __name__ == "__main__":
    asyncio.run(run_telegram_bot())
