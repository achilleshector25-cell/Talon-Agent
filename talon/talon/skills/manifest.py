"""Skill manifest — mandatory for marketplace"""
from pydantic import BaseModel
from typing import List

class SkillManifest(BaseModel):
    id: str
    version: str
    name: str
    permissions: dict  # e.g. {"fs": ["read:/workspace"], "network": false}
    wasm_hash: str
    sigstore_signature: str
    author: str
    description: str

    def is_safe(self) -> bool:
        # Enforce no ambient network unless declared
        if self.permissions.get("network") is True:
            return False
        return True
