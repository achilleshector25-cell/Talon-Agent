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

### Replit development runbook

1. Store `TELEGRAM_BOT_TOKEN` as a Replit Secret.
2. Set `TELEGRAM_OWNER_IDS` in the development environment to your personal
   numeric Telegram user ID. Do not use the bot's ID or username.
3. Enable the development-only host fallback:

   ```text
   TALON_ENV=development
   TALON_DEV_MODE=1
   TALON_ENABLE_SHELL=1
   TALON_ALLOW_HOST_EXECUTION=1
   ```

4. Start the `TALON Telegram Bridge` workflow:

   ```bash
   cd talon && PYTHONPATH=. python talonctl_telegram.py
   ```

5. Send `/shell echo TALON works` to the bot. The response should include the
   command output and `host-exec-dev-only`. Pipelines and redirects are
   supported in this explicitly enabled development mode, for example:

   ```text
   /shell printf 'hello\n' | tr a-z A-Z
   ```

This mode gives the Telegram owner direct command execution on the Replit
host. Stop the bridge and remove `TALON_ALLOW_HOST_EXECUTION` before using
TALON with untrusted users or in production.

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
