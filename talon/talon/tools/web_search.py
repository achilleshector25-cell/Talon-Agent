class Tool:
    name="web_search"
    async def run(self, args, identity, executor=None):
        q = args.get("query","")
        # In prod: search via isolated egress proxy, taint result as web:untrusted
        return {"tool":"web_search","query":q,"results":[{"title":"Mock result for "+q[:30],"snippet":"This is tainted web content — marked DATA, not instruction.","taint":"web:untrusted"}]}
