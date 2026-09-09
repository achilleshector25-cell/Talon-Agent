"""TALON Secure Gateway — fail-closed request authentication."""
import ipaddress
import os
from typing import Any, Literal

from fastapi import FastAPI, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from .mtls import derive_identity_from_cert
from .policy_engine import PolicyEngine
from .token_vault import TokenVault
from ..runtime.orchestrator import Orchestrator
from ..memory.vault import MemoryVault

app = FastAPI(title="TALON Gateway", version="1.0.0")
policy = PolicyEngine()
vault = TokenVault()
memory = MemoryVault()
orch = Orchestrator(memory=memory, policy_engine=policy)

class TaskRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10_000)
    channel: Literal["telegram", "discord", "slack", "whatsapp", "api"] = "telegram"
    tool: Literal["file_read", "shell", "web_search"] | None = None
    args: dict[str, Any] = Field(default_factory=dict)


def _is_trusted_proxy(request: Request) -> bool:
    host = request.client.host if request.client else ""
    configured = os.getenv("TALON_TRUSTED_PROXY_CIDRS", "")
    try:
        address = ipaddress.ip_address(host)
        return any(address in ipaddress.ip_network(item.strip()) for item in configured.split(",") if item.strip())
    except ValueError:
        return False


def get_identity(
    request: Request,
    x_client_cert: str | None = Header(default=None),
    x_talon_channel: str | None = Header(default=None),
):
    # Never synthesize an owner identity.  A development identity is explicit,
    # non-owner, and cannot be enabled in production.
    if not x_client_cert:
        if os.getenv("TALON_DEV_MODE") == "1" and os.getenv("TALON_ENV", "production").lower() not in {"prod", "production"}:
            from .mtls import Identity
            return Identity(
                spiffe_id="spiffe://talon/guest/dev",
                role="guest",
                channel="api",
                fingerprint="dev",
            )
        raise HTTPException(status_code=401, detail="client certificate required")
    if not _is_trusted_proxy(request):
        raise HTTPException(status_code=401, detail="untrusted certificate forwarding source")
    try:
        channel = x_talon_channel or "api"
        if channel not in {"telegram", "discord", "slack", "whatsapp", "api"}:
            raise HTTPException(status_code=400, detail="unsupported channel")
        ca_pem = os.getenv("TALON_CLIENT_CA_PEM")
        if os.getenv("TALON_ENV", "production").lower() in {"prod", "production"} and not ca_pem:
            raise HTTPException(status_code=503, detail="client CA is not configured")
        return derive_identity_from_cert(
            x_client_cert.encode(),
            channel,
            trusted_ca_pem=ca_pem.encode() if ca_pem else None,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail="invalid client certificate") from exc

@app.post("/v1/task")
async def handle_task(req: TaskRequest, request: Request, ident=Depends(get_identity)):
    if req.channel != ident.channel and ident.channel != "api":
        raise HTTPException(status_code=403, detail="channel is not bound to client identity")
    # Orchestrate via taint-aware runtime
    result = await orch.run(
        message=req.message,
        identity=ident,
        channel=req.channel,
        client_ip=request.client.host if request.client else "127.0.0.1",
        requested_tool=req.tool,
        requested_args=req.args,
    )
    return result

@app.post("/v1/lockdown")
async def lockdown(ident=Depends(get_identity)):
    if not ident.is_owner:
        raise HTTPException(403, "Owner only")
    vault.rotate_all()
    memory.rotate()
    return {"status": "locked", "vault_cleared": True}

@app.get("/health")
async def health():
    return {"status":"ok","version":"1.0.0","security":"mtls+policy+taint+microvm"}
