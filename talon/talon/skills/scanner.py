"""Skill scanner — Semgrep + dataflow + LLM semantic + VirusTotal (mock for MVP)"""
import hashlib

class SkillScanner:
    def scan(self, wasm_bytes: bytes, manifest) -> dict:
        findings = []
        # 1. Static: check for suspicious imports
        if b"socket" in wasm_bytes or b"fetch" in wasm_bytes:
            if not manifest.permissions.get("network"):
                findings.append({"severity":"critical","issue":"network import without permission"})
        # 2. Hash
        h = hashlib.sha256(wasm_bytes).hexdigest()
        if h != manifest.wasm_hash:
            findings.append({"severity":"high","issue":"hash mismatch"})
        # 3. Sigstore verify (mock)
        if not manifest.sigstore_signature:
            findings.append({"severity":"high","issue":"missing signature"})
        return {"safe": len(findings)==0, "findings": findings, "score": 100 - len(findings)*25}
