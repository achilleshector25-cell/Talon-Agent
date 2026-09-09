from .manifest import SkillManifest
from .scanner import SkillScanner

class Marketplace:
    def __init__(self):
        self.scanner = SkillScanner()
        self.registry = {}

    def publish(self, wasm_bytes: bytes, manifest: SkillManifest):
        report = self.scanner.scan(wasm_bytes, manifest)
        if not report["safe"]:
            raise ValueError(f"Skill failed security scan: {report}")
        self.registry[manifest.id] = {"manifest":manifest,"wasm":wasm_bytes,"report":report}
        return report

    def install(self, skill_id: str):
        return self.registry.get(skill_id)
