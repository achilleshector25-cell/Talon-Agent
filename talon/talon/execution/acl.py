from dataclasses import dataclass

@dataclass
class Capability:
    resource: str  # fs:/workspace, net:api.github.com, etc
    actions: list  # ["read"] etc

class ACL:
    def __init__(self):
        self.grants = {
            "file_read": [Capability("fs:/workspace",["read"])],
            "shell": [Capability("exec:microvm",["run"])],
            "web_search": [Capability("net:search.api",["fetch"])],
        }

    def check(self, tool: str, requested: Capability) -> bool:
        for cap in self.grants.get(tool, []):
            if requested.resource.startswith(cap.resource.split(":")[0]) and set(requested.actions).issubset(set(cap.actions)):
                return True
        return False
