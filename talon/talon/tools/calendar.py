class Tool:
    name="calendar"
    async def run(self, args, identity, executor=None):
        return {"tool":"calendar","events":[]}
