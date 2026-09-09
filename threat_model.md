# Threat Model

## Project Overview

TALON is a Python secure-agent gateway with channel connectors, certificate-based
identity, policy-controlled tools, encrypted episodic memory, and a planned
microVM/WASM execution plane. It accepts requests from messaging channels and
must treat all inbound content as untrusted data.

## Assets

- **Client identities and capabilities** — certificate-bound SPIFFE identities,
  roles, channels, and short-lived tokens control access to tools.
- **Agent messages and memory** — prompts, tool results, and episodic history may
  contain private user data or attacker-controlled instructions.
- **Execution boundary** — shell/WASM tooling can access the host or external
  services if isolation and capabilities fail.
- **Secrets and audit evidence** — connector tokens, encryption keys, policy
  decisions, and audit records must not leak or be silently altered.

## Trust Boundaries

- **Connector or client to gateway** — inbound messages, headers, and request
  fields are untrusted until authenticated and validated.
- **Trusted proxy to gateway** — forwarded client certificates are accepted only
  from explicitly configured proxy networks and must validate to a configured CA.
- **Gateway to tools** — every tool name, argument, and capability must be
  re-authorized immediately before execution.
- **Agent runtime to memory** — stored events require confidentiality and
  integrity protection and must not be shared across identities.
- **Gateway to execution services** — host execution is never an acceptable
  fallback for a claimed microVM sandbox.

## Scan Anchors

- Production entry point: `talon/talon/gateway/core.py`
- Highest-risk areas: `talon/talon/gateway`, `talon/talon/execution`,
  `talon/talon/tools`, and `talon/talon/runtime`
- Public surface: `/health`; authenticated surfaces: `/v1/task` and
  `/v1/lockdown`; admin action: owner-only lockdown
- Dev-only surface: host execution is disabled unless explicitly enabled with
  `TALON_ALLOW_HOST_EXECUTION=1`

## Threat Categories

### Spoofing

The gateway must reject requests without a client certificate or an explicit,
non-owner development mode. Forwarded certificates must come only from trusted
proxies, use the client-auth EKU, contain an exact `spiffe://talon/{role}/{id}`
URI, and validate to the configured CA.

### Tampering

Clients must not choose their role, owner status, channel, or approved
capabilities. Unknown tools and malformed arguments must be denied. File paths
must be canonicalized before authorization, and shell execution must not accept
shell metacharacters.

### Repudiation

Sensitive policy decisions and lockdown operations need identity, certificate
fingerprint, timestamp, action, and a tamper-evident audit sink. Hashes used for
audit data must be cryptographic and stable across processes.

### Information Disclosure

Cache keys and memory records must be scoped to the authenticated identity.
Errors must not expose certificate parsing details, filesystem paths outside the
approved roots, or secrets. File reads must reject symlinks, non-regular files,
oversized files, and paths outside canonical roots.

### Denial of Service

Request bodies, messages, tool arguments, file sizes, command lengths, and
execution time must be bounded. Token accounting must be concurrency-safe, and
timed-out child process groups must be terminated.

### Elevation of Privilege

System identities must not bypass policy by default. Owner-only operations must
be enforced server-side. The executor must call a real isolated service in
production; the local host-execution fallback is disabled by default and is
never a security boundary.