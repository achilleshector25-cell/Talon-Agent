class Tool:
    name="shell"
    async def run(self, args, identity, executor=None):
        if not identity.is_owner:
            return {"error":"owner only"}
        cmd = args.get("cmd", "")
        if not isinstance(cmd, str) or not cmd:
            return {"error":"command required"}
        # Execute in Firecracker microVM, no network
        if executor:
            res = await executor.run(cmd, network="none", timeout=10)
            return {"tool":"shell","cmd":cmd, **res}
        return {"error":"executor required"}
