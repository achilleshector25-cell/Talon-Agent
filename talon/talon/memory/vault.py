"""AES-256-GCM Memory Vault — encrypted at rest"""
import os, json, hashlib, time
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from typing import Any

class MemoryVault:
    def __init__(self, key: bytes | None = None):
        self.key = key or AESGCM.generate_key(bit_length=256)
        self.aes = AESGCM(self.key)
        self.episodic_log = []  # hash-chained
        self._last_hash = b"\x00"*32

    def _encrypt(self, data: dict) -> bytes:
        nonce = os.urandom(12)
        pt = json.dumps(data).encode()
        ct = self.aes.encrypt(nonce, pt, None)
        return nonce + ct

    def _decrypt(self, blob: bytes) -> dict:
        nonce, ct = blob[:12], blob[12:]
        pt = self.aes.decrypt(nonce, ct, None)
        return json.loads(pt)

    async def append_episodic(self, event: dict):
        # hash chain for tamper evidence
        payload = {"ts": time.time(), "event": event, "prev": self._last_hash.hex()}
        blob = self._encrypt(payload)
        h = hashlib.sha256(blob + self._last_hash).digest()
        self.episodic_log.append((blob, h))
        self._last_hash = h

    def verify_chain(self) -> bool:
        prev = b"\x00"*32
        for blob, h in self.episodic_log:
            if hashlib.sha256(blob+prev).digest() != h:
                return False
            prev = h
        return True

    def rotate(self) -> None:
        """Invalidate in-memory history and encryption material."""
        self.key = AESGCM.generate_key(bit_length=256)
        self.aes = AESGCM(self.key)
        self.episodic_log.clear()
        self._last_hash = b"\x00" * 32
