class GVisorExecutor:
    async def run(self, path: str, mode: str = "read"):
        return {"gvisor":True, "path":path, "mode":mode}
