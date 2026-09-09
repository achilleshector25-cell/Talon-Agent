"""Tool registry — WASM sandboxed, capability-checked"""
from . import file_read, shell, web_search
from ..execution.firecracker import FirecrackerExecutor

class ToolRegistry:
    def __init__(self):
        self.tools = {
            "file_read": file_read.Tool(),
            "shell": shell.Tool(),
            "web_search": web_search.Tool(),
        }
        self.fc = FirecrackerExecutor()

    async def execute(self, name: str, args: dict, identity):
        tool = self.tools.get(name)
        if not tool:
            return {"error":f"unknown tool {name}"}
        # Capability check (simplified)
        return await tool.run(args, identity, executor=self.fc)
