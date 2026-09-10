import pytest


def test_owner_flag_not_client_controlled():
    from talon.gateway.mtls import Identity
    ident = Identity(spiffe_id="spiffe://talon/owner/test", role="owner", channel="telegram", fingerprint="abc")
    assert ident.is_owner is True
    guest = Identity(spiffe_id="spiffe://talon/guest/test", role="guest", channel="telegram", fingerprint="abc")
    assert guest.is_owner is False

def test_policy_default_deny():
    from talon.gateway.policy_engine import PolicyEngine
    from talon.gateway.mtls import Identity
    pe = PolicyEngine()
    guest = Identity(spiffe_id="spiffe://talon/guest/x", role="guest", channel="telegram", fingerprint="xyz")
    assert pe.evaluate(guest, "shell", {"cmd":"rm -rf /"}) is False
    assert pe.evaluate(guest, "web_search", {}) is True
    assert pe.evaluate(guest, "unknown", {}) is False

def test_system_identity_is_not_unconditionally_privileged():
    from talon.gateway.policy_engine import PolicyEngine
    from talon.gateway.mtls import Identity
    system = Identity(spiffe_id="spiffe://talon/system/test", role="system", channel="api", fingerprint="xyz")
    assert system.is_owner is False
    assert PolicyEngine().evaluate(system, "shell", {}) is False

def test_file_path_prefix_confusion_is_denied():
    from talon.gateway.policy_engine import PolicyEngine
    from talon.gateway.mtls import Identity
    owner = Identity(spiffe_id="spiffe://talon/owner/test", role="owner", channel="api", fingerprint="xyz")
    assert PolicyEngine().evaluate(owner, "file_read", {"path": "/workspace_evil/secret"}) is False

def test_gateway_rejects_missing_certificate(monkeypatch):
    from fastapi import HTTPException
    from talon.gateway.core import get_identity

    monkeypatch.delenv("TALON_DEV_MODE", raising=False)
    monkeypatch.setenv("TALON_ENV", "production")
    with pytest.raises(HTTPException) as error:
        get_identity(type("Request", (), {"client": None})())
    assert error.value.status_code == 401

def test_host_execution_is_disabled_by_default(monkeypatch):
    from talon.execution.firecracker import FirecrackerExecutor

    monkeypatch.delenv("TALON_ALLOW_HOST_EXECUTION", raising=False)
    executor = FirecrackerExecutor()
    result = __import__("asyncio").run(executor.run("echo unsafe"))
    assert result["error"] == "host_execution_disabled"

def test_telegram_shell_command_is_explicit():
    from talon.connectors.telegram_commands import parse_tool_request

    assert parse_tool_request("/shell echo safe") == (
        "shell",
        {"cmd": "echo safe"},
    )
    assert parse_tool_request("please run echo safe") == (None, {})
    assert parse_tool_request("/shell") == ("shell", {"cmd": ""})
