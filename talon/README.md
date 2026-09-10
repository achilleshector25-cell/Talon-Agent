# TALON — Secure Autonomous Agent System
> State-of-the-art replacement for OpenClaw. Zero-trust, capability-based, WASM-sandboxed.

**Authored as Meta AI Senior AI Systems Engineer**

## Why TALON > OpenClaw
- OpenClaw: free open-source agent using messaging as UI, gateway daemon managing lifecycles [search]. Gateway = Connectors + Controller (sessions/cron/memory) + Agent Runtime. 26 tools / 53 skills.
- Flaws fixed: client-controlled `senderIsOwner` auth bypass, default-insecure deployments flagged by China MIIT, 36% flawed skills, XML-wrapper prompt-injection defense, 10-100x token burn.

## Quick Start
```bash
docker compose up --build
# or
make dev
```

## Telegram commands

The live bridge accepts explicit tool commands:

```text
/shell <command>
```

`/shell` is still restricted to IDs listed in `TELEGRAM_OWNER_IDS`, requires
`TALON_ENABLE_SHELL=1`, and requires an available isolated execution runtime.
Host execution remains disabled by default; setting `TALON_ALLOW_HOST_EXECUTION=1`
is only a development fallback and is not a production sandbox.

## Architecture
```
Channel Isolation -> Secure Gateway (Rust core, mTLS+QUIC, OPA) -> Agent Runtime (Orchestrator + WASM Tools + Taint Graph + Memory Vault) -> Execution Plane (Firecracker microVMs, gVisor, ACLs)
```

## Security Guarantees
- mTLS required, SPIFFE IDs, 15m token TTL, server-minted roles (never client flag)
- WASM tools: no ambient authority
- Provenance Taint Graph: DATA vs INSTRUCTION separation
- AES-256-GCM Memory Vault + hash-chained audit log
- Firecracker microVM for shell/code

## License: Apache-2.0
