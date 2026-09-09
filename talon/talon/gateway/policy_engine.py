"""Small fail-closed policy engine for the MVP gateway."""
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict
import time

class PolicyEngine:
    def __init__(self):
        self.shell_enabled = os.getenv("TALON_ENABLE_SHELL") == "1"
        self.allowed_roots = tuple(
            Path(item.strip()).expanduser().resolve()
            for item in os.getenv("TALON_FILE_ROOTS", "/workspace,/mnt/data/talon").split(",")
            if item.strip()
        )

    def evaluate(self, identity, tool: str, args: Dict[str, Any]) -> bool:
        if tool == "web_search":
            return identity.role in {"owner", "guest"} and isinstance(args.get("query", ""), str) and len(args.get("query", "")) <= 500
        if tool == "shell":
            return self.shell_enabled and identity.role == "owner"
        if tool == "file_read":
            if identity.role != "owner" or not isinstance(args.get("path"), str):
                return False
            try:
                path = Path(args["path"]).expanduser().resolve(strict=False)
                return any(path == root or root in path.parents for root in self.allowed_roots)
            except (OSError, RuntimeError):
                return False
        return False

    def audit(self, identity, tool, args, allowed: bool):
        return {
            "ts": time.time(),
            "spiffe": identity.spiffe_id,
            "tool": tool,
            "args_hash": hashlib.sha256(json.dumps(args, sort_keys=True, default=str).encode()).hexdigest(),
            "allowed": allowed,
            "fingerprint": identity.fingerprint,
        }
