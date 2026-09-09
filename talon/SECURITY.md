# Security Model

## Fixes for CVE-2026-44118, CVE-2026-25253, CVE-2026-24763 class
- Auth: server-derived owner flag from mTLS cert, not client field.
- Token theft: short-lived, bound to channel + IP, vault-stored.
- Command injection: WASM + microVM, no direct shell.

## Skill Marketplace
- Manifest required: permissions, network, fs.
- Pipeline: Semgrep + CodeQL + dataflow + LLM semantic + VirusTotal + Sigstore sign.
- Runtime enforcement: WASM imports whitelist.

## Audit
- All actions: OpenTelemetry + hash-chained log (WORM)
- Compliance: GDPR, SOC2, Dutch AP guidance (no sensitive data on experimental agents)

## Incident Response
- Kill switch: `talonctl lockdown --reason`
- Rotation: `talonctl rotate --all`
