"""Short-lived in-memory token storage bound to certificate and client IP."""
import secrets
import time
from threading import RLock
from typing import Dict

class TokenVault:
    def __init__(self):
        self._store: Dict[str, dict] = {}
        self._lock = RLock()

    def mint(self, identity, ip: str, ttl: int = 900) -> str:
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._store[token] = {
                "spiffe": identity.spiffe_id,
                "fingerprint": identity.fingerprint,
                "ip": ip,
                "exp": time.time() + max(1, min(ttl, 900)),
                "role": identity.role,
            }
        return token

    def validate(self, token: str, fingerprint: str, ip: str):
        with self._lock:
            rec = self._store.get(token)
            if not rec:
                return None
            if time.time() > rec["exp"]:
                del self._store[token]
                return None
            if not secrets.compare_digest(rec["fingerprint"], fingerprint):
                return None
            if not secrets.compare_digest(rec["ip"], ip):
                return None
            return dict(rec)

    def rotate_all(self):
        with self._lock:
            self._store.clear()
