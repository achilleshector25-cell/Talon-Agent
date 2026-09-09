# Threat Model — TALON

| Threat | Mitigation | OpenClaw Status |
|---|---|---|
| Auth bypass via senderIsOwner | mTLS + server-minted claims | Vulnerable |
| Skill supply chain | Sigstore + sandbox + scanner | 36% flawed |
| Prompt injection | Taint graph + classifier | XML wrapper |
| EDR/DLP bypass | microVM + no ambient net | Bypasses |
| Token exfil | Vault + 15m TTL + binding | Long-lived env |
| 30k exposed instances | QUIC + no public dashboard by default, Tailscale Funnel opt-in | Public WS |

STRIDE analysis implemented.
